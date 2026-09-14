
"""
Download daily ERA5 meteorology for all 23 Klimerko-SEPA locations
using ONE multi-location Open-Meteo Historical API request.

Run this script from the repository root.
   Input:
    data/analysis/city_coordinates.csv

Output:
    data/analysis/era5_city_daily.csv
"""

import time
import requests
import pandas as pd

COORD_FILE = "data/analysis/city_coordinates.csv"
OUT_FILE = "data/analysis/era5_city_daily.csv"

START = "2019-10-07"
END = "2024-12-31"
TZ = "Europe/Belgrade"

coords = pd.read_csv(COORD_FILE)

latitudes = ",".join(coords["Latitude"].astype(str))
longitudes = ",".join(coords["Longitude"].astype(str))

params = {
    "latitude": latitudes,
    "longitude": longitudes,
    "start_date": START,
    "end_date": END,
    "daily": ",".join([
        "temperature_2m_mean",
        "relative_humidity_2m_mean",
        "wind_speed_10m_mean",
        "precipitation_sum",
    ]),
    "timezone": TZ,
    "models": "era5",
    "temperature_unit": "celsius",
    "wind_speed_unit": "ms",
    "precipitation_unit": "mm",
}

url = "https://archive-api.open-meteo.com/v1/archive"

print("Requesting ERA5 data for 23 locations in one API call...")
print("This may take a little while.")

for attempt in range(8):
    r = requests.get(url, params=params, timeout=180)

    if r.status_code == 200:
        break

    if r.status_code == 429:
        retry_after = r.headers.get("Retry-After")
        wait = int(retry_after) if retry_after and retry_after.isdigit() else 30 * (attempt + 1)
        print(f"Rate limit (429). Waiting {wait} s before retry {attempt+1}/8...")
        time.sleep(wait)
        continue

    print("HTTP status:", r.status_code)
    print(r.text[:1000])
    r.raise_for_status()
else:
    raise RuntimeError("Open-Meteo still returns 429 after all retries. Try again later.")

js = r.json()

# For multiple coordinates Open-Meteo returns a list of location objects.
if not isinstance(js, list):
    js = [js]

if len(js) != len(coords):
    raise RuntimeError(
        f"Expected {len(coords)} locations, but API returned {len(js)}."
    )

frames = []

for i, loc in enumerate(js):
    d = pd.DataFrame(loc["daily"])
    c = coords.iloc[i]

    d.insert(0, "City", c["City"])
    d["Requested_latitude"] = c["Latitude"]
    d["Requested_longitude"] = c["Longitude"]
    d["Grid_latitude"] = loc.get("latitude")
    d["Grid_longitude"] = loc.get("longitude")
    d["Grid_elevation_m"] = loc.get("elevation")
    d["Timezone"] = loc.get("timezone")
    d["Source_model"] = "ERA5"

    frames.append(d)

meteo = pd.concat(frames, ignore_index=True)

meteo = meteo.rename(columns={
    "time": "Date",
    "temperature_2m_mean": "T2m_mean_C",
    "relative_humidity_2m_mean": "RH2m_mean_pct",
    "wind_speed_10m_mean": "Wind10m_mean_ms",
    "precipitation_sum": "Precipitation_sum_mm",
})

meteo["Date"] = pd.to_datetime(meteo["Date"])
meteo = meteo.sort_values(["City", "Date"]).reset_index(drop=True)

# QA
print("\nQA summary:")
qa = meteo.groupby("City").agg(
    n_days=("Date", "size"),
    first_date=("Date", "min"),
    last_date=("Date", "max"),
    missing_T=("T2m_mean_C", lambda x: x.isna().sum()),
    missing_RH=("RH2m_mean_pct", lambda x: x.isna().sum()),
    missing_wind=("Wind10m_mean_ms", lambda x: x.isna().sum()),
    missing_precip=("Precipitation_sum_mm", lambda x: x.isna().sum()),
)
print(qa.to_string())

meteo.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")

print(f"\nSUCCESS: saved {OUT_FILE}")
print(f"Rows: {len(meteo):,}")
