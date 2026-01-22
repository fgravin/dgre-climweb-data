from ftplib import FTP
from typing import TypedDict, List
import logging
import os
from datetime import date, datetime

from dgrehydro import SETTINGS

HYPE_FOLDER = "hype"

class HypeModel(TypedDict):
    name: str
    path: str

HYPE_MODELS: List[HypeModel] = [
    # {
    #     "name": "Niger HYPE v2.30",
    #     "path": "niger-hype2.30_hgfd3.2_ecoper_noEOWL_noINSITU"
    # },
    # {
    #     "name": "Niger HYPE v2.30 + Updating with local stations",
    #     "path": "niger-hype2.30_hgfd3.2_ecoper_noEOWL_INSITU-AR"
    # },
    # {
    #     "name": "West-Africa HYPE v1.2",
    #     "path": "wa-hype1.2_hgfd3.2_ecoper_noEOWL_noINSITU"
    # },
    # {
    #     "name": "West-Africa HYPE v1.2 + Updating with local stations",
    #     "path": "wa-hype1.2_hgfd3.2_ecoper_noEOWL_INSITU-AR"
    # },
    {
        "name": "bf-hype1.0_chirps2.0_gefs_noEOWL_noINSITU",
        "path": "bf-hype1.0_chirps2.0_gefs_noEOWL_noINSITU"
    },
]

fanfar_ftp = SETTINGS.get('secrets').get('fanfar_ftp')

def fetch_daily_hype_data(utc_time: datetime = datetime.utcnow()):

    forecast_issue_date = utc_time.strftime("%Y%m%d")
    logging.info("[HYPE][FETCH]: Start for date %s", forecast_issue_date)
    root_dest_folder = os.path.join(SETTINGS.get('DATA_DIR'), HYPE_FOLDER)

    # Save the original working directory to restore it later
    original_cwd = os.getcwd()

    for model in HYPE_MODELS:
        model_name = model["name"]
        model_path = model["path"]

        model_folder = os.path.join(root_dest_folder, model_path)
        dest_folder = os.path.join(model_folder, forecast_issue_date)

        try:
            os.makedirs(dest_folder, exist_ok=True)
            os.chdir(dest_folder)
            logging.info("[HYPE][FETCH]: Changed directory to %s", dest_folder)
        except Exception as e:
            logging.error("[HYPE][FETCH]: Failed to create/change directory to %s: %s", dest_folder, str(e))
            continue

        ftp_source_path = fanfar_ftp["path"] + model_path + '/' + forecast_issue_date
        try:
            ftp = FTP()
            ftp.connect(host=fanfar_ftp["url"], port=21, timeout=60.0)
            ftp.login(user=fanfar_ftp["user"], passwd=fanfar_ftp["password"])
            logging.info("[HYPE][FETCH]: Connected to FTP %s", fanfar_ftp["url"])

            ftp.cwd(ftp_source_path)
            logging.info("[HYPE][FETCH]: Changed directory to %s on FTP", ftp_source_path)

            all_files = ftp.nlst()
            logging.info("[HYPE][FETCH]: Found files: %s", all_files)

            for filename in all_files:
                with open(filename, 'wb') as f:
                    ftp.retrbinary('RETR ' + filename, f.write)
                    logging.info("[HYPE][FETCH]: Downloaded file %s", filename)
                    print(f"Downloaded file {filename}")

            ftp.quit()
            logging.info("[HYPE][FETCH]: Completed downloads for model %s", model_name)

        except Exception as e:
            logging.error("[HYPE][FETCH]: Error processing model %s: %s", model_name, str(e))

    # Restore the original working directory
    os.chdir(original_cwd)
    logging.info("[HYPE][FETCH]: Restored original working directory: %s", original_cwd)

    return True
