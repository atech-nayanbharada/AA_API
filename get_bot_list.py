import requests


def get_bot_list(token):
    url = "https://adanirpacloudproduction02.my.automationanywhere.digital/v3/activity/list"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-Authorization": f"{token}"
    }

    payload = {

        "filter": {
            "operator": "eq",
            "field": "status",
            "value": "QUEUED"

        },
        "sort": [
            {
                "field": "startDateTime",
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

        print("Bot List API Status:", response.status_code)

        if response.status_code != 200:
            print("Response:", response.text)
            return None

        return response.json()

    except requests.exceptions.RequestException as e:
        print("Bot List API Error:", e)
        return None
