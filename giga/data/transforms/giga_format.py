import pandas as pd


def cleanup_numeric_string(s):
    return "".join(filter(lambda x: str.isdigit(x) or x == "." or x == "-", s))


def cell_towers_to_standard_format(frame: pd.DataFrame):
    # sanitizes and transforms giga cell tower data into standardized format used by the models
    t = frame.rename(
        columns={
            "Site ID": "tower_id",
            "Ownership of site": "operator",
            "Indoor /outdoor": "outdoor",
            "Latitude": "lat",
            "Longitude": "lon",
            "Tower Height": "height",
            "Technology": "technologies",
        }
    )
    t["lat"] = t["lat"].apply(lambda x: cleanup_numeric_string(x))
    t["lon"] = t["lon"].apply(lambda x: cleanup_numeric_string(x))
    t["outdoor"] = t["outdoor"].apply(
        lambda x: True if x.lower() == "outdoor" else False
    )
    t["technologies"] = t["technologies"].apply(
        lambda x: ["3G"] if x == "3G Only" else x.split("/")
    )
    t["height"] = t["height"].apply(lambda x: 0.0 if x == "IBS" else float(x))
    return t
