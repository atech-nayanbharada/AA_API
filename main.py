import os
from historical_data_operation.historic_main import historical_main
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR,"BASE DIR")
env_file = BASE_DIR / ".env"



def read_excel_as_dict_list(excel_input_path, excel_file_name):
    excel_file = Path(excel_input_path) / excel_file_name

    if not excel_file.exists():
        raise FileNotFoundError(f"File not found: {excel_file}")

    df = pd.read_excel(excel_file, engine="openpyxl")

    return df.fillna("").to_dict(orient="records")



def main():
    loaded = load_dotenv(env_file)
    excel_input_path = os.getenv("excel_input_path")
    excel_file_name = os.getenv("excel_input_file_name")

    config_list = read_excel_as_dict_list(excel_input_path, excel_file_name)
    print(config_list, "config list")
    print("Historic main data started")
    historical_main(config_list)
    print("Historic main data ended")

if __name__ == "__main__":
    main()
