import datetime
import gzip
import logging
import os
import shutil

import requests
from requests.exceptions import RequestException

from dgrehydro import SETTINGS

waffgs_http = SETTINGS.get('secrets').get('waffgs_http')

def fetch_waffgs_data(utc_time: datetime = datetime.datetime.utcnow()):
    username = waffgs_http.get("user")
    password = waffgs_http.get("password")
    website = waffgs_http.get("url")

    forecast_issue_date = utc_time.strftime("%Y%m%d")
    logging.info("[WAFFGS][FETCH]: Start for date %s", forecast_issue_date)
    root_dest_folder = os.path.abspath(os.path.join(SETTINGS.get('DATA_DIR'), 'waffgs'))
    dest_folder = os.path.join(root_dest_folder, forecast_issue_date)

    try:
        os.makedirs(dest_folder, exist_ok=True)
        logging.info("[WAFFGS][FETCH]: Start fetch to %s", dest_folder)
    except Exception as e:
        logging.error("[WAFFGS][FETCH]: Failed to create directory to %s: %s", dest_folder, str(e))
        return False

    def download_file_with_auth(url, output_path, username, password):
        try:
            response = requests.get(url, auth=(username, password), stream=True, verify=False)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.info(f"[WAFFGS][FETCH] - Downloaded file: {os.path.basename(output_path)}")
        except RequestException as e:
            logging.error(f"[WAFFGS][FETCH] - Failed to download {url}: {e}")
            raise

    def unzip_gz_file(gz_path, out_path):
        try:
            with gzip.open(gz_path, "rb") as f_in, open(out_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            logging.info(f"[WAFFGS][FETCH] - Unzipped {os.path.basename(gz_path)} to {os.path.basename(out_path)}")
        except Exception as e:
            logging.error(f"[WAFFGS][FETCH] - Error unzipping {gz_path}: {e}")
            raise

    def get_filename(datetime):
        issue_hour = datetime.hour - 1  # Adjust for data availability delay
        intervals = [(0, 6), (6, 12), (12, 18), (18, 24)]
        product_hour, validity_hour = None, None

        for start, end in intervals:
            if start <= issue_hour < end:
                product_hour, validity_hour = start, end
                break

        if product_hour is None:
            raise ValueError("[WAFFGS][FETCH] - Unable to determine product hour interval.")

        logging.info(f"[WAFFGS][FETCH] - Forecast window: {product_hour:02d}:00 → {validity_hour:02d}:00 UTC")
        year, month, day = datetime.year, datetime.month, datetime.day
        filename_gz = f"{year}{month:02d}{day:02d}-{product_hour:02d}00_ffgs_prod_fcst_fft_forecast1_06hr_regional.txt.gz"
        return filename_gz

    # Fetch the data
    year, month, day = utc_time.year, utc_time.month, utc_time.day
    filename_gz = get_filename(utc_time)
    source_file_path = f"{website}{year}/{month:02d}/{day:02d}/FFFT1_TXT/{filename_gz}"
    dest_file_path = os.path.join(dest_folder, filename_gz)
    txt_file_path = dest_file_path.replace(".gz", "")

    download_file_with_auth(source_file_path, dest_file_path, username, password)
    unzip_gz_file(dest_file_path, txt_file_path)
    logging.info(f"[WAFFGS][FETCH] - Success")

    return txt_file_path
