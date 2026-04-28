import requests
import json
import pandas as pd
import os
from datetime import datetime, timezone
import matplotlib.pyplot as plt

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


graph_df = combined_df.tail(50).copy()

graph_df["valuedatetime"] = pd.to_datetime(graph_df["valuedatetime"])
graph_df["datavalue"] = pd.to_numeric(graph_df["datavalue"], errors="coerce")

graph_df = graph_df.dropna(subset=["datavalue"])

if not graph_df.empty:
    plt.figure(figsize=(12, 6))
    plt.plot(graph_df["valuedatetime"], graph_df["datavalue"], marker="o")
    plt.title("Live Sensor Data - Most Recent 50 Readings")
    plt.xlabel("Date/Time")
    plt.ylabel("Sensor Value")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("sensor_graph.png")
    plt.close()

plt.figure(figsize=(12, 6))
plt.plot(graph_df["valuedatetime"], graph_df["datavalue"], marker="o")
plt.title("Live Sensor Data - Most Recent 50 Readings")
plt.xlabel("Date/Time")
plt.ylabel("Sensor Value")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig("sensor_graph.png")
plt.close()

  
