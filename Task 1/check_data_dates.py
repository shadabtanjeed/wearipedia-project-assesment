import json
import os
from datetime import datetime


def extract_date_from_record(record, filename):

    if "activity" in filename:
        return record.get("dateTime", "N/A")

    elif "spo2" in filename:
        return record.get("dateTime", "N/A")

    elif "hr" in filename and not "hrv" in filename:
        if "heart_rate_day" in record:
            heart_data = record["heart_rate_day"]
            if isinstance(heart_data, list) and heart_data:
                activities_heart = heart_data[0].get("activities-heart", [])
                if isinstance(activities_heart, list) and activities_heart:
                    return activities_heart[0].get("dateTime", "N/A")
        return "N/A"

    elif "hrv" in filename:
        print(f"    DEBUG HRV: Keys in record: {list(record.keys())}")
        if "hrv" in record:
            hrv_array = record["hrv"]
            print(
                f"    DEBUG HRV: hrv is type {type(hrv_array)} with length {len(hrv_array)}"
            )

            if isinstance(hrv_array, list) and len(hrv_array) > 0:
                hrv_obj = hrv_array[0]
                print(f"    DEBUG HRV: hrv[0] is type {type(hrv_obj)}")
                if isinstance(hrv_obj, dict):
                    print(f"    DEBUG HRV: hrv[0] keys: {list(hrv_obj.keys())}")

                    if "minutes" in hrv_obj:
                        minutes_array = hrv_obj["minutes"]
                        print(
                            f"    DEBUG HRV: minutes is type {type(minutes_array)} with length {len(minutes_array)}"
                        )

                        if isinstance(minutes_array, list) and len(minutes_array) > 0:
                            minute_obj = minutes_array[0]
                            print(
                                f"    DEBUG HRV: minutes[0] is type {type(minute_obj)}"
                            )
                            if isinstance(minute_obj, dict):
                                print(
                                    f"    DEBUG HRV: minutes[0] keys: {list(minute_obj.keys())}"
                                )

                                if "minute" in minute_obj:
                                    timestamp = minute_obj["minute"]
                                    print(
                                        f"    DEBUG HRV: Found timestamp: {timestamp}"
                                    )
                                    return timestamp.split("T")[0]

        print("    DEBUG HRV: Failed to extract date")
        return "N/A"

    elif "br" in filename:
        if "br" in record:
            br_data = record["br"]
            if isinstance(br_data, list) and br_data:
                return br_data[0].get("dateTime", "N/A")
        return "N/A"

    elif "azm" in filename:
        if "activities-active-zone-minutes-intraday" in record:
            azm_data = record["activities-active-zone-minutes-intraday"]
            if isinstance(azm_data, list) and azm_data:
                return azm_data[0].get("dateTime", "N/A")
        return "N/A"

    return record.get("dateTime", "N/A")


def check_data_dates():
    data_dir = "../Data/Modified Data"
    files_to_check = [
        "hr_user1_modified.json",
        "activity_user1_modified.json",
        "spo2_user1_modified.json",
        "hrv_user1_modified.json",
        "br_user1_modified.json",
        "azm_user1_modified.json",
    ]

    for filename in files_to_check:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)

                if data:
                    first_record = data[0]
                    last_record = data[-1]

                    print(f"\n{filename}:")
                    print(f"  Total records: {len(data)}")

                    if "hrv" in filename:
                        print(f"  DEBUG: First record type: {type(first_record)}")
                        print(
                            f"  DEBUG: First record keys: {list(first_record.keys())}"
                        )

                    first_date = extract_date_from_record(first_record, filename)
                    last_date = extract_date_from_record(last_record, filename)

                    print(f"  First record date: {first_date}")
                    print(f"  Last record date: {last_date}")

                    print("  Sample dates:")
                    for i, record in enumerate(data[:3]):
                        date = extract_date_from_record(record, filename)
                        print(f"    {i+1}: {date}")

                    user_id = first_record.get("user_id", "N/A")
                    print(f"  User ID: {user_id}")

            except Exception as e:
                print(f"Error reading {filename}: {e}")
                import traceback

                traceback.print_exc()
        else:
            print(f"File not found: {filename}")


if __name__ == "__main__":
    check_data_dates()
