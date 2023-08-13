import json
import config

import requests

headers = {
    "User-Agent": "Leaderboard application for Janken Campaign / Discord: @dawarfmaster / maukmul@gmail.com",
    "content-type": "application/json"
}


def retrieve_campaign_data(campaign_id):
    api_url = f"https://trackmania.io/api/campaign/{campaign_id}"

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        # Write the JSON data to a file
        with open(f"{data['name']}.json", "w") as file:
            json.dump(data, file, indent=4)

        print(f"JSON data written to {data['name']}.json")
    else:
        print(f"Error: {response.status_code}")


def retrieve_map_data(map_name, leaderboard_uid, map_uid):
    api_url = f"https://trackmania.io/api/leaderboard/{leaderboard_uid}/{map_uid}?offset=0&length=1000"

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        # Write the JSON data to a file
        with open(f"{map_name}.json", "w") as file:
            json.dump(data, file, indent=4)

        print(f"JSON data written to {map_name}.json")
    else:
        print(f"Error: {response.status_code}")

retrieve_campaign_data("383/47819")
# retrieve_map_data("Summer2023_01", "0c61a2fe-f90b-4c9e-8eca-e1472968c5db", "7hk8IflYsbMbpJv2gyYzx48Zvt7")
# "NLS-siqXMbFEn74VP9jBY2xPpO0PbnaTiFFW3WH", "nB_CVdlw2b3h4KP6NPsy4nFyFj9"
# 0c61a2fe-f90b-4c9e-8eca-e1472968c5db/7hk8IflYsbMbpJv2gyYzx48Zvt7
