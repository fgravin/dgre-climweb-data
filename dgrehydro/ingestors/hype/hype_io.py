import re

import pandas as pd


# ----------------------------------------------------------------------------
# ReadTimeOutput (R → Python)
# ----------------------------------------------------------------------------
def read_time_output(filename: str, dt_format="%Y-%m-%d", hype_var:str=None, select:list[int]=None, nrows:int=None) -> pd.DataFrame:
    """
    Reads a HYPE 'time' output file and returns a pandas DataFrame.

    Parameters
    ----------
    filename : str
        Path to the HYPE time output file.
    dt_format : str
        Date format (default: "%Y-%m-%d").
    hype_var : str, optional
        Variable name (inferred from filename if None).
    select : list[int], optional
        Column indices to read (must include 1 for the DATE column).
    nrows : int, optional
        Number of rows to read.

    Returns
    -------
    df : pandas.DataFrame
        Cleaned and formatted time series data with a 'DATE' column.
        Attributes include 'subid', 'variable', and 'timestep'.
    """

    # --- Read first two lines to get metadata
    with open(filename, "r") as f:
        header_lines = [next(f).strip() for _ in range(2)]
    subids = [int(x) for x in header_lines[1].split("\t")[1:]]

    if select is not None:
        if 1 not in select:
            raise ValueError("Argument 'select' must include column 1.")
        subids = [subids[i - 1] for i in select[1:]]

    # --- Determine columns to read
    usecols = None
    if select is not None:
        usecols = [i - 1 for i in select]  # adjust R’s 1-based to Python’s 0-based

    # --- Load the data skipping first two lines
    df = pd.read_csv(
        filename,
        sep="\t",
        skiprows=2,
        header=None,
        na_values=["-9999", "****************"],
        usecols=usecols,
        nrows=nrows,
    )

    df.columns = ["DATE"] + [f"X{subid}" for subid in subids]

    # --- Parse variable name
    if hype_var is None:
        match = re.search(r"time([A-Za-z0-9]{1,4})", filename)
        hype_var = match.group(1) if match else "VAR"

    # --- Convert DATE column
    if dt_format is not None:
        try:
            df["DATE"] = pd.to_datetime(df["DATE"], format=dt_format, errors="coerce")
        except Exception:
            print("⚠️ Date/time conversion failed; keeping strings.")

    # --- Infer timestep
    timestep = "none"
    if df["DATE"].dtype == "datetime64[ns]" and len(df) > 1:
        delta_hours = (df["DATE"].iloc[1] - df["DATE"].iloc[0]).total_seconds() / 3600
        if abs(delta_hours - 24) < 1e-3:
            timestep = "day"
        elif abs(delta_hours - 168) < 1e-3:
            timestep = "week"
        elif delta_hours in [672, 696, 720, 744]:
            timestep = "month"
        elif delta_hours in [8760, 8784]:
            timestep = "year"
        else:
            timestep = f"{delta_hours} hour"

    # --- Attach attributes
    df.attrs["subid"] = subids
    df.attrs["variable"] = hype_var.upper()
    df.attrs["timestep"] = timestep

    return df


# ----------------------------------------------------------------------------
# ReadMapOutput (R → Python)
# ----------------------------------------------------------------------------
def read_map_output(filename, dt_format=None, hype_var=None, nrows=None):
    """
    Reads a HYPE 'map' output file and returns a pandas DataFrame.

    Parameters
    ----------
    filename : str
        Path to the HYPE map output file.
    dt_format : str, optional
        Date format for columns (default: infer).
    hype_var : str, optional
        Variable name (inferred from filename if None).
    nrows : int, optional
        Number of rows to read.

    Returns
    -------
    df : pandas.DataFrame
        Data with SUBID and X<date> columns, plus date/timestep metadata.
    """

    # --- Read header lines
    with open(filename, "r") as f:
        header_lines = [next(f).strip() for _ in range(2)]
    comment = header_lines[0]
    xd = header_lines[1].split(",")[1:]

    # --- Read body
    df = pd.read_csv(
        filename,
        skiprows=2,
        header=None,
        sep=",",
        na_values=["-9999", "****************"],
        nrows=nrows,
    )

    df.columns = ["SUBID"] + [f"X{d.replace('-', '.')}" for d in xd]

    # --- Parse variable name
    if hype_var is None:
        match = re.search(r"map([A-Za-z0-9]{1,4})", filename)
        hype_var = match.group(1) if match else "VAR"

    # --- Convert dates
    if dt_format is not None:
        try:
            xd_dt = pd.to_datetime(xd, format=dt_format, errors="coerce")
        except Exception:
            xd_dt = xd
            print("⚠️ Date/time conversion failed; keeping strings.")
    else:
        xd_dt = xd

    # --- Infer timestep
    timestep = "none"
    if isinstance(xd_dt[0], pd.Timestamp) and len(xd_dt) > 1:
        try:
            delta_hours = (xd_dt[1] - xd_dt[0]).total_seconds() / 3600
            if abs(delta_hours - 24) < 1e-3:
                timestep = "day"
            elif abs(delta_hours - 168) < 1e-3:
                timestep = "week"
            elif delta_hours in [672, 696, 720, 744]:
                timestep = "month"
            elif delta_hours in [8760, 8784]:
                timestep = "year"
            else:
                timestep = f"{delta_hours} hour"
        except Exception:
            pass

    # --- Attach attributes
    df.attrs["date"] = xd_dt
    df.attrs["variable"] = hype_var.upper()
    df.attrs["comment"] = comment
    df.attrs["timestep"] = timestep

    return df
