import os

import requests
from datetime import datetime, timedelta, timezone

from get_api_through_token import get_token
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
env_file = BASE_DIR / ".env.aa"


def get_task_list(token):
    base_url = os.getenv("base_url")

    url = f"{base_url}/v3/activity/list"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-Authorization": f"{token}"
    }

    payload = {
        "filter": {
            "operator": "or",
            "operands": [

                {
                    "operator": "eq",
                    "field": "status",
                    "value": "RUN_ABORTED"
                },
                {
                    "operator": "eq",
                    "field": "status",
                    "value": "RUN_TIMED_OUT"
                },
                {
                    "operator": "eq",
                    "field": "status",
                    "value": "DEPLOY_FAILED"
                },
                {
                    "operator": "eq",
                    "field": "status",
                    "value": "RUN_FAILED"
                }
            ]
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
