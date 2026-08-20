import duckdb

DB_FILE = "smarthome_iot.db"

def build_data_warehouse():
    conn = duckdb.connect(DB_FILE)
    
    # Target analytical schema
    conn.execute("CREATE SCHEMA IF NOT EXISTS analytics;")

    # Dim_locations (flattening properties and rooms together)
    conn.execute("DROP TABLE IF EXISTS analytics.dim_locations;")
    conn.execute("""
        CREATE TABLE analytics.dim_locations AS
        SELECT
            r.room_id,
            p.property_id,
            p.property_name,
            p.property_type,
            p.city,
            p.postal_code,
            r.room_name,
            r.floor_number,
            r.square_footage
        FROM core.rooms r
        JOIN core.properties p ON r.property_id = p.property_id;
    """)

    # Dim_devices (flattening devices and firmware together)
    conn.execute("DROP TABLE IF EXISTS analytics.dim_devices;")
    conn.execute("""
        CREATE TABLE analytics.dim_devices AS
        SELECT
            d.device_id,
            d.device_model,
            d.mac_address,
            d.serial_number,
            f.version_string AS firmware_version,
            f.is_critical_patch AS running_critical_patch
        FROM core.devices d
        LEFT JOIN core.firmware_releases f ON d.firmware_id = f.firmware_id;
    """)

    # Fact_telemetry_hourly (aggregates high-frequency data)
    conn.execute("DROP TABLE IF EXISTS analytics.fact_telemetry_hourly;")
    conn.execute("""
        CREATE TABLE analytics.fact_telemetry_hourly AS
        SELECT
            MD5(d.device_id || '_' || DATE_TRUNC('hour', t.timestamp)::TEXT) AS fact_key,
            d.device_id,
            r.room_id,
            DATE_TRUNC('hour', t.timestamp) AS event_hour,
            EXTRACT('hour' FROM t.timestamp) AS hour_of_day,
            EXTRACT('dow' FROM t.timestamp) AS day_of_week,

            COUNT(t.reading_id) AS total_readings_sent,
            ROUND(AVG(CASE WHEN t.metric_type = 'Temperature' THEN t.metric_value END), 2) AS avg_temperature_c,
            ROUND(SUM(CASE WHEN t.metric_type = 'Power_Usage' THEN t.metric_value END), 4) AS total_power_kwh,
            MAX(CASE WHEN t.metric_type = 'Motion_Detected' THEN t.metric_value END) AS motion_triggered_count


        FROM core.telemetry_readings t
        JOIN core.devices d ON t.device_id = d.device_id
        JOIN core.rooms r ON d.room_id = r.room_id
        GROUP BY d.device_id, r.room_id, DATE_TRUNC('hour', t.timestamp), EXTRACT('hour' FROM t.timestamp), EXTRACT('dow' FROM t.timestamp);
     """)

    warehouse_counts = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM analytics.dim_locations) AS locations,
            (SELECT COUNT(*) FROM analytics.dim_devices) AS devices,
            (SELECT COUNT(*) FROM analytics.fact_telemetry_hourly) AS facts;
    """).fetchone()

    print(f"\n Star schema ready. Staged {warehouse_counts[0]} locations, {warehouse_counts[1]} devices, and {warehouse_counts[2]} hourly aggregated facts.")
    print("=" * 60)
    conn.close()

if __name__ == "__main__":
    build_data_warehouse()