import logging
import os
import re
from datetime import datetime
from ftplib import FTP

from dgrehydro import SETTINGS

CRITPOINT_FOLDER = "critical_points"

anam_ftp = SETTINGS.get('secrets').get('anam_ftp')


def fetch_critpoint_data(utc_time: datetime = datetime.utcnow()) -> str:
    """
    Fetch CSV file from FTP for the given date.
    Returns path to downloaded file or None if not found.

    Args:
        utc_time: The datetime to fetch data for (default: current UTC time)

    Returns:
        Path to the downloaded CSV file, or None if no file found
    """
    target_date = utc_time.strftime("%Y-%m-%d")
    target_date_folder = utc_time.strftime("%Y%m%d")
    logging.info("[CRITPOINT][FETCH]: Start for date %s", target_date)

    dest_folder = os.path.abspath(
        os.path.join(SETTINGS.get('DATA_DIR'), CRITPOINT_FOLDER, target_date_folder)
    )

    try:
        os.makedirs(dest_folder, exist_ok=True)
        logging.info("[CRITPOINT][FETCH]: Created directory %s", dest_folder)
    except Exception as e:
        logging.error("[CRITPOINT][FETCH]: Failed to create directory %s: %s", dest_folder, str(e))
        return None

    try:
        ftp = FTP()
        ftp.connect(host=anam_ftp["url"], port=21, timeout=60.0)
        ftp.login(user=anam_ftp["user"], passwd=anam_ftp["password"])
        logging.info("[CRITPOINT][FETCH]: Connected to FTP %s", anam_ftp["url"])

        ftp_path = anam_ftp["path"]
        ftp.cwd(ftp_path)
        logging.info("[CRITPOINT][FETCH]: Changed directory to %s on FTP", ftp_path)

        all_files = ftp.nlst()
        logging.info("[CRITPOINT][FETCH]: Found %d files on FTP", len(all_files))

        # Find CSV files matching our date pattern: SAPCI_LOCAL_POIS{YYYY-MM-DD-HH-MM}.csv
        matching_file = find_file_for_date(all_files, target_date)

        if matching_file is None:
            logging.warning("[CRITPOINT][FETCH]: No CSV file found for date %s", target_date)
            ftp.quit()
            return None

        logging.info("[CRITPOINT][FETCH]: Found matching file: %s", matching_file)

        local_file_path = os.path.join(dest_folder, matching_file)
        with open(local_file_path, 'wb') as f:
            ftp.retrbinary('RETR ' + matching_file, f.write)
            logging.info("[CRITPOINT][FETCH]: Downloaded file %s", matching_file)

        ftp.quit()
        logging.info("[CRITPOINT][FETCH]: Completed download for date %s", target_date)

        return local_file_path

    except Exception as e:
        logging.error("[CRITPOINT][FETCH]: Error fetching data: %s", str(e))
        return None


def find_file_for_date(files: list, target_date: str) -> str:
    """
    Find the most recent CSV file matching the target date.

    Args:
        files: List of filenames from FTP
        target_date: Date string in format YYYY-MM-DD

    Returns:
        Filename of the most recent matching file, or None if not found
    """
    # Pattern: SAPCI_LOCAL_POIS2026-01-21-12-03.csv
    pattern = re.compile(r"SAPCI_LOCAL_POIS(\d{4}-\d{2}-\d{2})-(\d{2})-(\d{2})\.csv")

    matching_files = []
    for f in files:
        match = pattern.match(f)
        if match:
            file_date = match.group(1)
            if file_date == target_date:
                try:
                    hour = int(match.group(2))
                    minute = int(match.group(3))
                    matching_files.append((f, hour * 60 + minute))
                except ValueError:
                    continue

    if not matching_files:
        return None

    # Return the file with the latest time
    matching_files.sort(key=lambda x: x[1], reverse=True)
    return matching_files[0][0]
