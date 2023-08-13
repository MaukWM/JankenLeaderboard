import base64
import json
import time

import requests

from config import email, password

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


def retrieve_map_records(nls_full_access_token, mapUid, max_records=30000):
    finished = False
    result = {}
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


def retrieve_all_campaign_records(nls_full_access_token, campaign_json):
    map_records = {}

    with open(campaign_json, 'r') as json_file:
        data = json.load(json_file)

        for i, campaign_map in enumerate(data['playlist']):
            # if i > 3:
            #     # Early break for debugging
            #     break
            time.sleep(1)
            map_author_time = campaign_map["authorScore"]
            map_name = campaign_map['name']
            map_uid = campaign_map['mapUid']
            print("Processing", map_uid, map_name)
            all_map_records = retrieve_map_records(nls_full_access_token, map_uid)

            map_records[map_uid] = {
                'name': map_name,
                'author_time': map_author_time,
                'all_records': all_map_records
            }

    return map_records

