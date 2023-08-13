import json
import time

import requests
import base64

from config import email, password

NO_TIME_PENALTY = 500000


def setup_access_token(audience="NadeoLiveServices"):
    ubiservices_url = "https://public-ubiservices.ubi.com/v3/profiles/sessions"
    headers = {
        "Content-Type": "application/json",
        "Ubi-AppId": "86263886-327a-4328-ac69-527f0d20a237",
        "User-Agent": f"Leaderboard application for Janken Campaign / {email}",
        "Authorization": f"Basic {base64.b64encode(f'{email}:{password}'.encode()).decode()}"
    }
    auth_data = {
        "email": email,
        "password": password,
        "audience": audience
    }

    response = requests.post(ubiservices_url, headers=headers, json=auth_data)

    if response.status_code == 200:
        auth_ticket = response.json().get("ticket")
        if auth_ticket:
            # Step 2: Use Ubisoft Authentication Ticket for Nadeo Authentication

            nadeo_url = "https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices"
            nadeo_headers = {
                "Content-Type": "application/json",
                "Authorization": f"ubi_v1 t={auth_ticket}"
            }
            nadeo_body = {
                "audience": audience
            }

            nadeo_response = requests.post(nadeo_url, headers=nadeo_headers, json=nadeo_body)

            if nadeo_response.status_code == 200:
                full_access_token = nadeo_response.json().get("accessToken")
                print("Nadeo Access Token:", full_access_token)
                splitted_token = full_access_token.split(".")
                return full_access_token, splitted_token[0], splitted_token[1], splitted_token[2]
            else:
                print("Nadeo Authentication Error:", nadeo_response.status_code)
        else:
            print("Ubisoft Authentication Error:", "Ticket not found")
    else:
        print("Ubisoft Authentication Error:", response.status_code)

    return None


nls_full_access_token, _, _, _ = setup_access_token()
ns_full_access_token, _, _, _ = setup_access_token(audience="NadeoServices")

# while len(payload) % 4 != 0:
#     payload += "="
# print(base64.b64decode(payload))


def retrieve_map_records(mapUid, max_records=30000):
    finished = False
    result = {}
    # TODO: Extend this for leaderboards with over 100 entries
    current_offset = 0
    n_records_per_request = 100
    while not finished:
        leaderboard_get_url = f"https://live-services.trackmania.nadeo.live/api/token/leaderboard/group/Personal_Best/map/{mapUid}/top?length={n_records_per_request}&onlyWorld=true&offset={current_offset}"
        print(f"Getting {leaderboard_get_url}")
        current_offset += n_records_per_request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"nadeo_v1 t={nls_full_access_token}"
        }
        time.sleep(1)

        response = requests.get(leaderboard_get_url, headers=headers)

        # print(response)
        zones = response.json()['tops']
        for zone in zones:
            if zone['zoneName'] == 'World':
                for top in zone['top']:
                    result[top['accountId']] = top['score']

                if len(zone['top']) < n_records_per_request or current_offset >= max_records:
                    finished = True

    return result


# result = retrieve_map_records(mapUid="nB_CVdlw2b3h4KP6NPsy4nFyFj9")
# print(result)


def retrieve_campaign_times():
    playerRecords = {}

    with open("BS Campagne.json", 'r') as json_file:
        data = json.load(json_file)

        for i, campaign_map in enumerate(data['playlist']):
            if i > 1:
                # Early break for debugging
                break
            time.sleep(1)
            mapAT = campaign_map["authorScore"]
            mapName = campaign_map['name']
            mapUid = campaign_map['mapUid']
            print("Processing", mapUid, mapName)
            mapRecords = retrieve_map_records(mapUid)

            # Add a 5 minute penalty to everyone by default
            for accountId in playerRecords.keys():
                playerRecords[accountId][mapName] = {}
                playerRecords[accountId][mapName]["time"] = NO_TIME_PENALTY
                playerRecords[accountId][mapName]["AT"] = False

            for accountId in mapRecords.keys():
                if accountId not in playerRecords.keys():
                    # If this is the first time we encounter of a player, add the time and a 5 minute penalty for each missing finish
                    playerRecords[accountId] = {}
                    playerRecords[accountId][mapName] = {}
                    playerRecords[accountId][mapName]["time"] = NO_TIME_PENALTY
                    playerRecords[accountId][mapName]["AT"] = False
                else:
                    # If a player has a time, add the time and remove the 5 minute penalty
                    playerRecords[accountId][mapName] = {}
                    playerRecords[accountId][mapName]["time"] = mapRecords[accountId]
                    playerRecords[accountId][mapName]["AT"] = mapRecords[accountId] < mapAT

    return playerRecords


leaderboard = retrieve_campaign_times()
print(leaderboard)


def create_leaderboard(leaderboard):
    print("Generating pretty leaderboard")
    display_named_leaderboard = {}
    # First retrieve "cached" account Ids and only retrieve new ones.
    with open("accounts.json", 'r') as json_file:
        collected_accInfos = []
        cached_account_info = json.load(json_file)

        request_strings = []
        accIds = list(leaderboard.keys())
        _i = 0
        request_string = ""
        for accId in accIds:
            # If we already know this person, don't extend the request.
            if accId in cached_account_info:
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
            print("All accounts already in cache!")
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
                collected_accInfos.append(accInfos)

            collected_accInfos = [elem for arr in collected_accInfos for elem in arr]
            for accInfo in collected_accInfos:
                cached_account_info[accInfo["accountId"]] = accInfo["displayName"]

            # Dump the newest cached version of all the accounts
            with open("accounts.json", "w") as json_file:
                json.dump(cached_account_info, json_file)

        for accId in cached_account_info.keys():
            if accId in leaderboard:
                display_named_leaderboard[cached_account_info[accId]] = leaderboard[accId]

    def milliseconds_to_time(milliseconds):
        seconds, milliseconds = divmod(milliseconds, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{milliseconds:04d}"

    # Calculate the maximum length of keys for alignment
    max_key_length = max(len(key) for key in display_named_leaderboard.keys())

    # # Iterate through the dictionary and print key-value pairs
    # for key, value in sorted(display_named_leaderboard.items()):
    #     print(f"{key}: {value}, {milliseconds_to_time(value)}")

    # Sort the dictionary by values
    sorted_leaderboard = sorted(display_named_leaderboard.items(), key=lambda item: item[1])

    # for rank, (key, value) in enumerate(sorted(data.items(), key=lambda item: item[1]), start=1):
    #     print("%-5s %-*s: %d" % (rank, max_key_length, key, value))

    leaderboard_list = []

    # Iterate through the dictionary and print formatted key-value pairs
    for rank, (key, value) in enumerate(sorted_leaderboard, start=1):
        time_string = milliseconds_to_time(value)
        print("%-5s %-*s: %s" % (rank, max_key_length, key, time_string))
        leaderboard_list.append({"name": key,
                                 "rank": rank,
                                 "time_string": time_string})

    leaderboard_to_cache = {"data": leaderboard_list}

    with open("leaderboard.json", "w") as json_file:
        json.dump(leaderboard_to_cache, json_file)


create_leaderboard(leaderboard)
