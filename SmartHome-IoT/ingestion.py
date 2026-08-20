import os
import glob
import json
import duckdb
import pandas as pd
import numpy as np

RAW_DATA_DIR = "raw-data"
DB_FILE = "smarthome_iot.db"

def initialise_duckdb_staging():
    print(f"Connecting to analytical warehouse: {DB_FILE}")
    conn = duckdb.connect(DB_FILE)

    conn.execute("CREATE SCHEMA IF NOT EXISTS staging;")
    return conn

def ingest_csv_dimensions(conn):
    csv_mappings = {
        "stg_customers": "customers.csv",
        "stg_properties": "properties.csv",
        "stg_rooms": "rooms.csv",
        "stg_devices": "devices.csv",
        "stg_firmware_releases": "firmware_releases.csv",
        "stg_invoices": "invoices.csv",
        "stg_utility_tariffs": "utility_tariffs.csv"
    }

    for table_name, file_name in csv_mappings.items():
        file_path = os.path.join(RAW_DATA_DIR, file_name)
        if not os.path.exists(file_path):
            continue

        df = pd.read_csv(file_path, dtype=str)

        conn.execute(f"DROP TABLE IF EXISTS staging.{table_name};")
        conn.execute(f"CREATE TABLE staging.{table_name} AS SELECT * FROM df;")

def ingest_json_streams(conn):
    json_mappings = {
        "stg_telemetry_readings": "telemetry_readings.json",
        "stg_device_alert_logs": "device_alert_logs.json"
    }

    for table_name, file_name in json_mappings.items():
        file_path = os.path.join(RAW_DATA_DIR, file_name)
        if not os.path.exists(file_path):
            continue


        with open(file_path, "r", encoding="utf-8") as f:
            raw_json = json.load(f)

        df = pd.DataFrame(raw_json)

        # Convert NaN objects to NULL strings
        df = df.replace({np.nan: None})
        df = df.astype(str)

        conn.execute(f"DROP TABLE IF EXISTS staging.{table_name};")
        conn.execute(f"CREATE TABLE staging.{table_name} AS SELECT * FROM df;")

def main():
    if not os.path.exists(RAW_DATA_DIR):
        print(f"Target source folder '{RAW_DATA_DIR}' cannot be located.")
        return
    
    conn = None
    try:
        conn = initialise_duckdb_staging()

        # CSV extraction
        ingest_csv_dimensions(conn)

        # JSON stream ingestion
        ingest_json_streams(conn)

        print("\n Raw data ingestion successfully executed")

    except Exception as e:
        print (f"\n Pipeline exception encountered during ingestion phase: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()