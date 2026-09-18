import time
import requests


def get_token(base_cloud_login_data):
    aa_base_url = base_cloud_login_data.get('AA_Base_URL','')
    cloud_login_data = {
        "username": base_cloud_login_data.get('Username',''),
        "password": base_cloud_login_data.get('Password',''),
        "multipleLogin": True
    }
    login_response = requests.post(aa_base_url + "/v2/authentication", json=cloud_login_data)
    time.sleep(3)
    print(login_response, "login response")
    if login_response.status_code == 200:
        print("\nAPI Response : ", login_response.status_code)
        print("**********Successfully Logged In**********")
        login_json = login_response.json()
        token = login_json.get('token', "")
        # print("*********TOKEN CODE", token)
    else:
        print("API Response : ", login_response.status_code)
        print("Error. Connect to VPN or check the code.")
        token = None
    return token
