import os
import pandas as pd
from historical_data_operation.historic_main import historical_main
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR,"BASE DIR")
env_file = BASE_DIR / ".env"


from pathlib import Path
import pandas as pd


def read_aa_config(excel_input_path, excel_file_name):
    """
    Read AA configuration data from Excel and return a list of dictionaries.
    """
    excel_file = Path(excel_input_path) / excel_file_name

    if not excel_file.exists():

        raise FileNotFoundError(f"File not found: {excel_file}")

    df = pd.read_excel(excel_file, engine="openpyxl")

    return df.fillna("").to_dict(orient="records")


def main():
    loaded = load_dotenv(env_file)
    excel_input_path = os.getenv("excel_input_path")
    excel_file_name = os.getenv("excel_input_file_name")

    # Full file path
    excel_file = Path(excel_input_path) / excel_file_name

    # excel_file = os.path.join(excel_input_path, excel_file_name)
    print(excel_file, "excel filee")
    # Read Excel
    if excel_file.exists():
        df = pd.read_excel(excel_file, engine="openpyxl")

        config_list = []

        for _, row in df.iterrows():
            config_dict = {
                "AA_Base_URL": row.get("AA_Base_URL",""),
                "Username": row.get("Username",""),
                "Password": row.get("Password",""),
                "Historic_Runner_List": row.get("Historic_Runner_List","")
            }

            config_list.append(config_dict)

        print(config_list)


        print(f"Rows: {len(df)}")
    else:
        print(f"File not found: {excel_file}")


    print(excel_input_path, "excel input type")

    AA_BASE_URL = os.getenv("base_url")
    AA_USERNAME = os.getenv("AA_USERNAME")
    AA_PASSWORD = os.getenv("AA_PASSWORD")

    cloud_loginData = {
        "base_url": AA_BASE_URL,
        "username": AA_USERNAME,
        "password": AA_PASSWORD,
        "multipleLogin": True
    }
    print("Historic main data started")

    # historical_main(cloud_loginData)
    print("Historic main data ended")

if __name__ == "__main__":
    main()
