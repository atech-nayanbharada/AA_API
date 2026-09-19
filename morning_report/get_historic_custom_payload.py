import os
import requests


def get_custom_task_list(token, base_cloud_login_data, operands):
    base_url = base_cloud_login_data.get('AA_Base_URL', '')

    url = f"{base_url}/v3/activity/list"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-Authorization": f"{token}"
    }

    payload = {
        "filter": {
            "operator": "or",
            "operands": operands
        },
        "sort": [
            {
                "field": "endDateTime",
                "direction": "desc"
            }
        ],
        "page": {
            "offset": 0,
            "length": 100
        }
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print("Task List API Status:", response.status_code)

        if response.status_code == 200:
            data = response.json()

            print("Task list received successfully")
            print(data, "data")
            return data

        else:
            print("Task List API Failed")
            print("Response:", response.text)

            return None

    except requests.exceptions.RequestException as e:
        print("Task List API Error:", e)
        return None
