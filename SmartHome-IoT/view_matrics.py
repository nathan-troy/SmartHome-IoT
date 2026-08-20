import duckdb

DB_FILE = "smarthome_iot.db"

def run_terminal_dashboard():
    conn = duckdb.connect(DB_FILE)

    print("=" * 60)
    print("Smart Home System Data Monitor")
    print("=" * 60)

    print("\n System wide asset inventory summary")
    print("-" * 45)
    asset_summary = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM core.customers) AS total_customers,
            (SELECT COUNT(*) FROM core.properties) AS total_properties,
            (SELECT COUNT(*) FROM core.devices) AS total_devices,
            (SELECT COUNT(*) FROM core.telemetry_readings) AS total_logs;
    """).fetchone()

    print(f"Total Registered Customers : {asset_summary[0]}")
    print(f" Monitored Properties       : {asset_summary[1]}")
    print(f" Deployed Smart Devices     : {asset_summary[2]}")
    print(f" Stored Telemetry Readings  : {asset_summary[3]}")

    print("\n Top Smart Home Distributions")
    print("-" * 45)
    print(f"{'Postal Area':<15}{'Property Count':<15}{'Total Devices':<15}")

    regional_data = conn.execute("""
        SELECT
            p.postal_code,
            COUNT(DISTINCT p.property_id) AS property_count,
            COUNT(d.device_id) AS device_count
        FROM core.properties p
        LEFT JOIN core.rooms r ON p.property_id = r.property_id
        LEFT JOIN core.devices d ON r.room_id = d.room_id
        GROUP BY p.postal_code
        ORDER BY device_count DESC
        LIMIT 5;
    """).fetchall()

    for row in regional_data:
        print(f"{row[0]:<15}{row[1]:<15}{row[2]:<15}")

    print("\n Operational Alert Log Summary")
    print("-" * 45)
    alerts = conn.execute("""
        SELECT
            security_level,
            COUNT(*) AS alert_count,
            COUNT(CASE WHEN resolved_at IS NULL THEN 1 END) AS active_unresolved
        FROM core.device_alert_logs
        GROUP BY security_level
        ORDER BY alert_count DESC;
    """).fetchall()

    if alerts:
        print(f"{'Severity':<15}{'Total Logged':<15}{'Still Unresolved':<15}")
        for row in alerts:
            print(f"{row[0]:<15}{row[1]:<15}{row[2]:<15}")
    else:
        print("Zero hardware alerts registered.")

        print("\n" + "=" * 60)
        conn.close()

if __name__ == "__main__":
    run_terminal_dashboard()