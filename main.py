import os
from datetime import datetime, time
from historical_data_operation.historic_main import historical_main
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
from zoneinfo import ZoneInfo
from morning_report.morning_report import morning_report_main

BASE_DIR = Path(__file__).resolve().parent
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

    # ========================================================
    # CURRENT IST TIME
    # ========================================================

    ist = ZoneInfo("Asia/Kolkata")
    now = datetime.now(ist)
    current_time = now.time()

    # ========================================================
    # MORNING REPORT WINDOW
    # ========================================================

    morning_start_time = time(hour=7,minute=0)
    morning_end_time = time(hour=9,minute=0)
    evening_start_time = time(hour=17,minute=0)
    evening_end_time = time(hour=18,minute=45)
    print("=" * 60)
    print("Current Date :",now.strftime("%d-%m-%Y"))
    print("Current Time :",now.strftime("%I:%M:%S %p IST"))
    print("=" * 60)

    # ========================================================
    # PROCESS SELECTION
    # ========================================================

    if morning_start_time<= current_time<= morning_end_time:
        # ----------------------------------------------------
        # 07:00 AM TO 09:00 AM
        # ----------------------------------------------------
        print("Morning reporting window detected.")
        print("Starting morning report process...")
        morning_report_main(config_list)
        print("Morning report process completed.")

    elif evening_start_time <= current_time <= evening_end_time:
        # ----------------------------------------------------
        # 17:00 AM TO 19:00 AM
        # ----------------------------------------------------
        print("Evening reporting window detected.")
        print("Starting evening report process...")
        morning_report_main(config_list)
        print("Evening report process completed.")

    else:
        # ----------------------------------------------------
        # ALL OTHER TIMES
        # ----------------------------------------------------
        print("Outside morning reporting window.")
        print("Starting historical monitoring process...")
        historical_main(config_list)
        print("Historical monitoring process completed.")


if __name__ == "__main__":
    main()
