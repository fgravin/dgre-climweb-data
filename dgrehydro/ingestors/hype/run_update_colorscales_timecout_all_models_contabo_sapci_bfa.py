"""
Script to update colorscales for timeCOUT across all HYPE models for SAPCI BFA.

This script:
1. Downloads forecast data for each model
2. Processes forecast and hindcast files
3. Calculates warning levels based on return periods
4. Creates colorscales, forecast, and hindcast CSV files

Converted from R script: run_update_colorscales_timecout_all_models_contabo_sapci_bfa.R
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from dgrehydro.ingestors.hype.hype_io import read_time_output


def wldef(discharge_values, return_levels, wl_rp_indices):
    """
    Determine the warning level for a given subbasin.

    Parameters
    ----------
    discharge_values : array-like
        Discharge values for all forecast days
    return_levels : array-like
        Return period threshold values for this subbasin
    wl_rp_indices : array-like
        Indices of return periods

    Returns
    -------
    int
        Warning level (0 if no warning, or index of highest exceeded return period)
    """
    mywl = 0

    # If any return level is NaN, never warn
    if np.any(pd.isna(return_levels)):
        return mywl

    # Check each return period threshold
    for k in wl_rp_indices:
        if np.any(discharge_values > return_levels[k]):
            mywl = k

    return mywl


def main():
    """Main function to process all models."""

    # 1. Configure directories
    models = [
        "World-Wide HYPE v1.3.5",
        "Niger HYPE v2.30",
        "Niger HYPE v2.30 + Updating with local stations",
        "West-Africa HYPE v1.2",
        "West-Africa HYPE v1.2 + Updating with local stations",
        "bf-hype1.0_chirps2.0_gefs_noEOWL_noINSITU"
    ]

    directories = [
        "wa-hype1.3_hgfd3.2_ecoper_noEOWL_noINSITU",
        "niger-hype2.30_hgfd3.2_ecoper_noEOWL_noINSITU",
        "niger-hype2.30_hgfd3.2_ecoper_noEOWL_INSITU-AR",
        "wa-hype1.2_hgfd3.2_ecoper_noEOWL_noINSITU",
        "wa-hype1.2_hgfd3.2_ecoper_noEOWL_INSITU-AR",
        "bf-hype1.0_chirps2.0_gefs_noEOWL_noINSITU"
    ]

    base_workspace = "/var/www/tethys/workspaces/sapci_bfa/app_workspace"

    # Loop through models (starting from index 1, which is index 2 in R's 1-based indexing)
    for i in range(1, len(models)):
        print(f"\n{'='*80}")
        print(f"Processing model {i+1}/{len(models)}: {models[i]}")
        print(f"{'='*80}")

        # Set up paths
        model_dir = directories[i]
        file_dir = Path(base_workspace) / model_dir
        static_dir = file_dir / "static"
        wl_dir = file_dir / "wl"

        # Ensure wl directory exists
        wl_dir.mkdir(parents=True, exist_ok=True)

        name_retlev = static_dir / "thresholds-rp-cout.txt"

        # 1. Download forecast data
        print(f"Downloading forecast data for model {i+1}...")
        download_script = f"/root/scripts/download_forecast/download_forecast{i+1}.py"
        try:
            subprocess.run(["python3", download_script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Download script failed with error: {e}")
        except FileNotFoundError:
            print(f"Warning: Download script not found: {download_script}")

        # 2. Format colorscales, hindcast and forecast for Tethys
        print("Finding latest forecast files...")
        all_files = os.listdir(file_dir)
        forecast_files = [f for f in all_files if "forecast_timeCOUT" in f]

        if not forecast_files:
            print(f"No forecast files found for model {i+1}. Skipping.")
            continue

        # Extract issue dates from filenames
        issue_dates = []
        for f in forecast_files:
            try:
                date_str = f[1:9]  # Extract rYYYYMMDD
                issue_date = datetime.strptime(date_str, "%Y%m%d").date()
                issue_dates.append(issue_date)
            except (ValueError, IndexError):
                continue

        if not issue_dates:
            print(f"Could not parse any issue dates for model {i+1}. Skipping.")
            continue

        # Get the latest issue date
        latest_idx = issue_dates.index(max(issue_dates))
        issue_date = issue_dates[latest_idx]

        # Check last warning level file date
        wl_files = list(wl_dir.glob("*.txt"))
        if wl_files:
            last_wl_dates = []
            for wl_file in wl_files:
                try:
                    # Extract date from filename like "004_mapWarningLevel_YYYY-MM-DD.txt"
                    date_part = wl_file.stem.split("_")[-1]
                    last_wl_dates.append(datetime.strptime(date_part, "%Y-%m-%d").date())
                except (ValueError, IndexError):
                    continue
            last_issue_date = max(last_wl_dates) if last_wl_dates else datetime(1900, 1, 1).date()
        else:
            last_issue_date = datetime(1900, 1, 1).date()

        print(f"Latest issue date: {issue_date}")
        print(f"Last processed date: {last_issue_date}")

        if issue_date < last_issue_date:
            print(f"No new data for model {i+1}. Skipping.")
            continue

        # Get forecast and hindcast files
        forecast_file = forecast_files[latest_idx]
        issue_date_str = issue_date.strftime("%Y%m%d")
        hindcast_pattern = f"{issue_date_str}_hindcast_timeCOUT"
        hindcast_files = [f for f in all_files if hindcast_pattern in f]

        if not hindcast_files:
            print(f"No hindcast file found for {issue_date}. Skipping.")
            continue

        hindcast_file = hindcast_files[0]

        print(f"Processing forecast file: {forecast_file}")
        print(f"Processing hindcast file: {hindcast_file}")

        # Read and process forecast data
        forecast_data = read_time_output(str(file_dir / forecast_file))

        # Transpose and format
        forecast_df = forecast_data.set_index("DATE").T
        forecast_df.index = forecast_df.index.str.replace("X", "")
        forecast_df = forecast_df.reset_index()
        forecast_df.insert(0, "index", range(1, len(forecast_df) + 1))
        forecast_df = forecast_df.rename(columns={"index": "SUBID"})
        forecast_df.columns = ["index", "SUBID"] + [str(c) for c in forecast_df.columns[2:]]

        # Save forecast
        forecast_csv = wl_dir / "forecast.csv"
        forecast_df.to_csv(forecast_csv, index=False)
        print(f"Saved forecast to: {forecast_csv}")

        # Read and process hindcast data
        hindcast_data = read_time_output(str(file_dir / hindcast_file))

        # Transpose and format
        hindcast_df = hindcast_data.set_index("DATE").T
        hindcast_df.index = hindcast_df.index.str.replace("X", "")
        hindcast_df = hindcast_df.reset_index()
        hindcast_df.insert(0, "index", range(1, len(hindcast_df) + 1))
        hindcast_df = hindcast_df.rename(columns={"index": "SUBID"})
        hindcast_df.columns = ["index", "SUBID"] + [str(c) for c in hindcast_df.columns[2:]]

        # Save hindcast
        hindcast_csv = wl_dir / "hindcast.csv"
        hindcast_df.to_csv(hindcast_csv, index=False)
        print(f"Saved hindcast to: {hindcast_csv}")

        # Prepare colorscales file
        print("Calculating warning levels...")

        # Read return level thresholds
        retlev = pd.read_table(name_retlev)
        retlev2 = retlev.drop(columns=["SUBID"]).T
        retlev2.columns = retlev["SUBID"].astype(str)

        # Extract return periods from row names (e.g., "RP2" -> 2)
        wl_rp = [int(rp.replace("RP", "")) for rp in retlev2.index]

        # Read forecast discharge data for warning level calculation
        thisq = read_time_output(str(file_dir / forecast_file))

        # Store dates
        all_dates = thisq["DATE"]

        # Remove DATE column and clean column names
        thisq = thisq.drop(columns=["DATE"])
        thisq.columns = thisq.columns.str.replace("X", "")

        # Special handling for Burkina (model index 5 in 0-based indexing)
        if i == 5:
            # Match columns between forecast and return levels
            common_cols = [col for col in thisq.columns if col in retlev2.columns]
            retlev2 = retlev2[common_cols]
            thisq = thisq[common_cols]

        # Check that columns match
        if list(thisq.columns) != list(retlev2.columns):
            print("Warning: Column mismatch between forecast and return levels!")
            print(f"Forecast columns: {len(thisq.columns)}")
            print(f"Return level columns: {len(retlev2.columns)}")
            # Try to align them
            common_cols = [col for col in thisq.columns if col in retlev2.columns]
            if common_cols:
                thisq = thisq[common_cols]
                retlev2 = retlev2[common_cols]
            else:
                print("No common columns found. Skipping.")
                continue

        # Calculate warning levels for each day
        thiswls = []
        for day_idx in range(len(thisq)):
            thisq1 = thisq.iloc[day_idx]
            thiswl = []
            for subid in thisq.columns:
                discharge_vals = thisq1[subid]
                return_vals = retlev2[subid].values
                wl_val = wldef([discharge_vals], return_vals, range(len(wl_rp)))
                thiswl.append(wl_val)
            thiswls.append(thiswl)

        # Convert to DataFrame
        thiswls_array = np.array(thiswls).T

        # Calculate max warning level across all days
        max_wl = np.max(thiswls_array, axis=1)

        # Create warning level DataFrame
        thiswl_df = pd.DataFrame(thiswls_array, columns=[str(d) for d in all_dates])
        thiswl_df.insert(0, "SUBID", [int(sid) for sid in thisq.columns])
        thiswl_df["WarningLevel_max"] = max_wl

        # Save warning level file with header
        wl_file = wl_dir / f"004_mapWarningLevel_{issue_date}.txt"
        with open(wl_file, "w") as f:
            f.write(f" Warning levels based on magnitudes with return-period: {', '.join(map(str, wl_rp))} years\n")
        thiswl_df.to_csv(wl_file, index=False, mode="a")
        print(f"Saved warning levels to: {wl_file}")

        # Create colorscales file (for Tethys)
        colorscales_df = thiswl_df.copy()
        colorscales_df.insert(0, "index", range(1, len(colorscales_df) + 1))
        colorscales_df.columns = ["index", "SUBID"] + [f"day{i+1}" for i in range(len(all_dates))] + ["max"]

        colorscales_csv = wl_dir / "colorscales.csv"
        colorscales_csv1 = wl_dir / "colorscales1.csv"
        colorscales_df.to_csv(colorscales_csv, index=False)
        colorscales_df.to_csv(colorscales_csv1, index=False)
        print(f"Saved colorscales to: {colorscales_csv}")

        # Create forecast dates file
        forecast_dates_df = pd.DataFrame({
            "Jour": [f"day{i+1}" for i in range(len(all_dates))] + ["max"],
            "Date": [str(d)[:10] for d in all_dates] + ["Max of 10 days forecast"]
        })

        forecast_dates_csv = wl_dir / "forecast_dates.csv"
        forecast_dates_df.to_csv(forecast_dates_csv, index=False)
        print(f"Saved forecast dates to: {forecast_dates_csv}")

        # Special handling for Burkina (model index 5): copy to riverine_flood directory
        if i == 5:
            print("Copying files to riverine_flood directory...")
            wl_dir1 = Path(base_workspace) / "riverine_flood" / "wl"
            wl_dir1.mkdir(parents=True, exist_ok=True)

            # Add a row of zeros to colorscales
            colorscales_df_copy = pd.concat([
                colorscales_df,
                pd.DataFrame([0] * len(colorscales_df.columns)).T
            ], ignore_index=True)
            colorscales_df_copy.columns = colorscales_df.columns

            colorscales_df_copy.to_csv(wl_dir1 / "colorscales.csv", index=False)
            colorscales_df_copy.to_csv(wl_dir1 / "colorscales1.csv", index=False)
            forecast_dates_df.to_csv(wl_dir1 / "forecast_dates.csv", index=False)
            print(f"Copied files to: {wl_dir1}")

        print(f"✓ Completed processing for model {i+1}: {models[i]}")


if __name__ == "__main__":
    main()