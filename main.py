import requests
import json
import pandas as pd
import os
from datetime import datetime, timezone

URL = "https://monitormywatershed.org/dataloader/ajax/"
RESULT_ID = "10543"
FILE_NAME = f"live_sensor_{RESULT_ID}_all.csv"

def fetch_data(start_date, end_date):
    payload = {
        "request_data": json.dumps({
            "method": "get_result_timeseries",
            "resultid": RESULT_ID,
            "start_date": start_date,
            "end_date": end_date,
        })
    }

    response = requests.post(URL, data=payload)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, str):
        data = json.loads(data)

    rows = []
    for k in data.get("datavalue", {}).keys():
        rows.append({
            "valueid": data.get("valueid", {}).get(k),
            "datavalue": data.get("datavalue", {}).get(k),
            "valuedatetime": data.get("valuedatetime", {}).get(k),
            "utc_offset": data.get("valuedatetimeutcoffset", {}).get(k),
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["valuedatetime"] = pd.to_datetime(df["valuedatetime"], unit="ms")
        df = df.sort_values("valuedatetime")

    return df


now = datetime.now(timezone.utc)
end_date = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"

if os.path.exists(FILE_NAME):
    old_df = pd.read_csv(FILE_NAME)
    old_df["valuedatetime"] = pd.to_datetime(old_df["valuedatetime"])

    last_time = old_df["valuedatetime"].max().to_pydatetime().replace(tzinfo=timezone.utc)
    start_date = last_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
else:
    old_df = pd.DataFrame()
    start_date = "2020-01-01T00:00:00.000Z"   

new_df = fetch_data(start_date, end_date)

combined_df = pd.concat([old_df, new_df], ignore_index=True)
combined_df = combined_df.drop_duplicates(subset=["valueid"])
combined_df = combined_df.sort_values("valuedatetime")

combined_df.to_csv(FILE_NAME, index=False)

print(f"[{datetime.now().strftime('%H:%M:%S')}] CSV updated — {len(combined_df)} total rows")

  