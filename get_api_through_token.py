import os
import time
import requests
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
env_file = BASE_DIR / ".env.aa"


def get_token():
    loaded = load_dotenv(env_file)
    print("ENV Loaded:", loaded)
    print("ENV File:", env_file)

    AA_BASE_URL = os.getenv("base_url")
    AA_USERNAME = os.getenv("AA_USERNAME")
    AA_PASSWORD = os.getenv("AA_PASSWORD")

    print(AA_BASE_URL)
    print(AA_USERNAME)
    print(AA_PASSWORD)
    Cloud_loginData = {
        "username": AA_USERNAME,
        "password": AA_PASSWORD,
        "multipleLogin": True
    }
    login_response = requests.post(AA_BASE_URL + "/v2/authentication", json=Cloud_loginData)
    time.sleep(3)
    print(login_response, "login response")
    if login_response.status_code == 200:
        print("\nAPI Response : ", login_response.status_code)
        print("**********Successfully Logged In**********")
        login_json = login_response.json()
        token = login_json.get('token', "")
        print("*********TOKEN CODE", token)

    else:
        print("API Response : ", login_response.status_code)
        print("Error. Connect to VPN or check the code.")
        token = None

    return token
