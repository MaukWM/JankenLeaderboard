import json
import time

import requests
import base64

from api_util import setup_access_token, retrieve_all_campaign_records

NO_TIME_PENALTY = 300000
CAMPAIGN_NAME = "BS Campagne"


def create_participant_data(campaign_records):
    participant_data = {}

    # Initialize a record of all participants
    for map_uid in campaign_records.keys():
        for account_id in campaign_records[map_uid]["all_records"].keys():
            if account_id not in participant_data:
                participant_data[account_id] = {}
                participant_data[account_id]['ATs'] = 0

    # Afterwards, initialize all map times (this is inefficient but I can't bother making it better)
    for account_id in participant_data.keys():
        participant_data[account_id]['maps'] = {}
        for map_uid in campaign_records.keys():
            participant_data[account_id]['maps'][map_uid] = {}
            participant_data[account_id]['maps'][map_uid]["time"] = NO_TIME_PENALTY
            participant_data[account_id]['maps'][map_uid]["AT"] = False

    return participant_data


def fill_participant_data(campaign_records, participant_data):
    for map_uid in campaign_records.keys():
        map_records = campaign_records[map_uid]['all_records']
        for participant_id in map_records.keys():
            participant_data[participant_id]['maps'][map_uid]['time'] = map_records[participant_id]
            participant_data[participant_id]['maps'][map_uid]['AT'] = map_records[participant_id] < campaign_records[map_uid]['author_time']
            participant_data[participant_id]['ATs'] += map_records[participant_id] < campaign_records[map_uid]['author_time']

    # Calculate total time
    for participant_id in participant_data.keys():
        total_time = 0
        for map_uid in participant_data[participant_id]['maps'].keys():
            total_time += participant_data[participant_id]['maps'][map_uid]['time']
        participant_data[participant_id]['total_time'] = total_time

    return participant_data


def retrieve_id_to_display_name_dict(ns_full_access_token, participant_id_list):
    id_to_display_name_dict = {}
    # First retrieve "cached" account Ids and only retrieve new ones.
    with open("participant_id_to_display_name_dict.json", 'r') as json_file:
        collected_acc_infos = []
        cached_conversion_dict = json.load(json_file)

        request_strings = []
        _i = 0
        request_string = ""
        for accId in participant_id_list:
            # If we already know this person, don't extend the request.
            if accId in cached_conversion_dict:
                continue

            request_string += f"{accId},"
            _i += 1

            if _i > 48:
                request_string = request_string[:-1]
                request_strings.append(request_string)
                request_string = ""
                _i = 0

        # Append the final result
        if request_string not in request_strings:
            request_string = request_string[:-1]
            request_strings.append(request_string)

        if request_strings[0] == "":
            print("All participant_ids are already in cached!")
        else:
            for request_string in request_strings:
                accountId_get_url = f"https://prod.trackmania.core.nadeo.online/accounts/displayNames/?accountIdList={request_string}"
                print(f"Getting {accountId_get_url}")
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"nadeo_v1 t={ns_full_access_token}"
                }

                response = requests.get(accountId_get_url, headers=headers)
                time.sleep(1)

                accInfos = response.json()
                collected_acc_infos.append(accInfos)

            collected_acc_infos = [elem for arr in collected_acc_infos for elem in arr]
            for accInfo in collected_acc_infos:
                cached_conversion_dict[accInfo["accountId"]] = accInfo["displayName"]

            # Dump the newest cached version of all the accounts
            with open("participant_id_to_display_name_dict.json", "w") as json_file:
                json.dump(cached_conversion_dict, json_file)

    return cached_conversion_dict


def refresh_leaderboard():
    """
    Fully refresh the leaderboard. We do this inefficiently.
    """
    # Get some fresh access tokens.
    nls_full_access_token, _, _, _ = setup_access_token()
    ns_full_access_token, _, _, _ = setup_access_token(audience="NadeoServices")

    # First, retrieve ALL records from ALL campaign maps (slowly)
    campaign_records = retrieve_all_campaign_records(nls_full_access_token, "BS Campagne.json")

    # Second, from the retrieved records, identify ALL participants.
    participant_data = create_participant_data(campaign_records)

    # After creating the setup for the table, we now fill in the results in order to obtain a ranking
    participant_data = fill_participant_data(campaign_records, participant_data)

    # We have our resulting leaderboard, sort, convert ids, and cache it.
    participant_id_list = list(participant_data.keys())
    id_to_display_name_dict = retrieve_id_to_display_name_dict(ns_full_access_token, participant_id_list)
    participant_data = {id_to_display_name_dict[key]: value for key, value in participant_data.items()}
    sorted_participant_data = dict(sorted(participant_data.items(), key=lambda item: item[1]["total_time"]))

    def milliseconds_to_time(milliseconds):
        seconds, milliseconds = divmod(milliseconds, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:01d}:{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

    # print(participant_data)

    leaderboard_list = []

    # Iterate through the dictionary and print formatted key-value pairs
    for rank, participant_name in enumerate(sorted_participant_data.keys(), start=1):
        time_string = milliseconds_to_time(sorted_participant_data[participant_name]['total_time'])
        ATs = sorted_participant_data[participant_name]['ATs']
        maps = sorted_participant_data[participant_name]['maps']
        for map_uid in maps.keys():
            maps[map_uid]['time'] = milliseconds_to_time(maps[map_uid]['time'])
        print("%-*s: %s" % (rank, participant_name, time_string))
        leaderboard_list.append({"name": participant_name,
                                 "rank": rank,
                                 "time_string": time_string,
                                 "ATs": ATs,
                                 "maps": maps})

    leaderboard_to_cache = {"data": leaderboard_list}

    with open("leaderboard.json", "w") as json_file:
        json.dump(leaderboard_to_cache, json_file)


refresh_leaderboard()
