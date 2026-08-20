import duckdb
import pandas as pd
import numpy as np

DB_FILE = "smarthome_iot.db"

def get_db_connections():
    return duckdb.connect(DB_FILE)

def setup_core_schema(conn):
    conn.execute("CREATE SCHEMA IF NOT EXISTS core;")

def transform_and_load_dimensions(conn):
    # Transform Customers
    df_cust = conn.execute("SELECT * FROM staging.stg_customers;").df()

    # Text normalisation: handle varying name casings cleanly
    df_cust['first_name'] = df_cust['first_name'].str.strip().str.capitalize()
    df_cust['last_name'] = df_cust['last_name'].str.strip().str.capitalize()
    df_cust['email'] = df_cust['email'].str.strip().str.lower()
    df_cust['signup_date'] = pd.to_datetime(df_cust['signup_date'], format='mixed', dayfirst=True)

    conn.execute("DROP TABLE IF EXISTS core.customers;")
    conn.execute("CREATE TABLE core.customers AS SELECT * FROM df_cust;")

    # Transform properties
    df_prop = conn.execute("SELECT * FROM staging.stg_properties;").df()

    # Strip whitespace, converts to uppercase, handles spatial integrity
    df_prop['postal_code'] = df_prop['postal_code'].str.strip().str.upper()
    df_prop['property_name'] = df_prop['property_name'].str.strip()

    conn.execute("DROP TABLE IF EXISTS core.properties;")
    conn.execute("CREATE TABLE core.properties AS SELECT * FROM df_prop;")

    # Transform rooms
    df_rooms = conn.execute("SELECT * FROM staging.stg_rooms;").df()

    df_rooms['floor_number'] = df_rooms['floor_number'].astype(int)
    df_rooms['square_footage'] = df_rooms['square_footage'].astype(int)

    conn.execute("DROP TABLE IF EXISTS core.rooms;")
    conn.execute("CREATE TABLE core.rooms AS SELECT * FROM df_rooms;")

    # Transform devices
    df_dev = conn.execute("SELECT * FROM staging.stg_devices;").df()
    df_dev['mac_address'] = df_dev['mac_address'].str.strip().str.upper()
    df_dev['serial_number'] = df_dev['serial_number'].str.strip().str.upper()

    conn.execute("DROP TABLE IF EXISTS core.devices;")
    conn.execute("CREATE TABLE core.devices AS SELECT * FROM df_dev;")

    # Transform firmware releases
    df_firm = conn.execute("SELECT * FROM staging.stg_firmware_releases;").df()
    df_firm['release_date'] = pd.to_datetime(df_firm['release_date'], format='mixed', dayfirst=True).dt.date
    df_firm['is_critical_patch'] = df_firm['is_critical_patch'].str.lower().map({'true': True, 'false': False})

    conn.execute("DROP TABLE IF EXISTS core.firmware_releases;")
    conn.execute("CREATE TABLE core.firmware_releases AS SELECT * FROM df_firm;")

    # Transform invoices
    df_inv = conn.execute("SELECT * FROM staging.stg_invoices;").df()
    df_inv['billing_period_start'] = pd.to_datetime(df_inv['billing_period_start'], format='mixed', dayfirst=True).dt.date
    df_inv['billing_period_end'] = pd.to_datetime(df_inv['billing_period_end'], format='mixed', dayfirst=True).dt.date
    df_inv['amount_due'] = pd.to_numeric(df_inv['amount_due'], errors='coerce')

    conn.execute("DROP TABLE IF EXISTS core.invoices;")
    conn.execute("CREATE TABLE core.invoices AS SELECT * FROM df_inv;")

    # Transform utility tariffs
    df_tar = conn.execute("SELECT * FROM staging.stg_utility_tariffs;").df()
    df_tar['postal_code'] = df_tar['postal_code'].str.strip().str.upper()
    df_tar['rate_per_kwh'] = pd.to_numeric(df_tar['rate_per_kwh'], errors='coerce')
    df_tar['is_peak_pricing'] = df_tar['is_peak_pricing'].str.lower().map({'true': True, 'false': False})
    df_tar['effective_from'] = pd.to_datetime(df_tar['effective_from'])

    conn.execute("DROP TABLE IF EXISTS core.utility_tariffs;")
    conn.execute("CREATE TABLE core.utility_tariffs AS SELECT * FROM df_tar;")

def transform_and_load_streams(conn):
    df_tel = conn.execute("SELECT * FROM staging.stg_telemetry_readings;").df()

    df_tel['timestamp'] = pd.to_datetime(df_tel['timestamp'])
    df_tel['metric_value'] = pd.to_numeric(df_tel['metric_value'], errors='coerce')
    df_tel['metric_type'] = df_tel['metric_type'].str.strip()

    conn.execute("DROP TABLE IF EXISTS core.telemetry_readings;")
    conn.execute("CREATE TABLE core.telemetry_readings AS SELECT * FROM df_tel;")

    # Transform device alert logs
    df_alert = conn.execute("SELECT * FROM staging.stg_device_alert_logs;").df()

    df_alert['timestamp'] = pd.to_datetime(df_alert['timestamp'])

    # Replace literal 'none' or empty entries with system Nan boundaries
    df_alert['resolved_at'] = df_alert['resolved_at'].replace({'None': np.nan, '': np.nan})
    df_alert['resolved_at'] = pd.to_datetime(df_alert['resolved_at'])

    conn.execute("DROP TABLE IF EXISTS core.device_alert_logs;")
    conn.execute("CREATE TABLE core.device_alert_logs AS SELECT * FROM df_alert;")

def main():
    conn = None
    try:
        conn = get_db_connections()
        setup_core_schema(conn)

        transform_and_load_dimensions(conn)
        transform_and_load_streams(conn)

        print("\n Schema transformed successfully. Data types normalised.")

    except Exception as e:
        print(f"\n Pipeline transformation execution interrupted: {e}")
    finally:
        if conn:
            conn.close()
        
if __name__ == "__main__":
    main()

