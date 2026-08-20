import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DB_FILE = "smarthome_iot.db"

def generate_analytics_dashboard():
    conn = duckdb.connect(DB_FILE)

    # Query for hourly environmental and energy profiles
    query_trends = """
        SELECT
            event_hour,
            AVG(avg_temperature_c) AS average_temp,
            SUM(total_power_kwh) AS aggregate_power
        FROM analytics.fact_telemetry_hourly
        GROUP BY event_hour
        ORDER BY event_hour;
    """
    df_trends = conn.execute(query_trends).df()

    df_trends['event_hour'] = pd.to_datetime(df_trends['event_hour'])
    df_trends = df_trends.sort_values('event_hour')

    # Query for alert breakdown
    query_alerts = """
        SELECT
            security_level,
            COUNT(*) AS total_count
        FROM core.device_alert_logs
        GROUP BY security_level;
    """
    df_alerts = conn.execute(query_alerts).df()
    conn.close()

    df_trends['event_hour'] = pd.to_datetime(df_trends['event_hour'])
    df_trends = df_trends.sort_values('event_hour')

    df_trends = df_trends.set_index('event_hour').resample('h').mean().reset_index()
    df_trends['aggregate_power'] = df_trends['aggregate_power'].interpolate(method='linear')
    df_trends['average_temp'] = df_trends['average_temp'].interpolate(method='linear')

    # Figure and subplots setup
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("SmartHome IoT Infrastructure Analytics", fontsize=16, fontweight='bold')

    import matplotlib.dates as mdates

    # Grid 1: dual axis system load trends
    ax1_twin = ax1.twinx()

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))

    line1 = ax1.plot(df_trends['event_hour'], df_trends['aggregate_power'],
                     color='#2ca02c', marker='o', linewidth=2, label='Power Load (kWh)')

    line2 = ax1_twin.plot(df_trends['event_hour'], df_trends['average_temp'],
                          color='#ff7f0e', marker='s', linestyle='--', linewidth=2, label='Avg Temp (°C)')

    ax1.set_xlabel('Timeline Interval', fontweight='bold')
    ax1.set_ylabel('Aggregated Grid Load (kWh)', color='#2ca02c', fontweight='bold')
    ax1_twin.set_ylabel('Mean Temperature (°C)', color='#ff7f0e', fontweight='bold')
    ax1.set_title('Grid Power Load vs Inside Temperatures', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)

    # Legend mapping
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    ax1.grid(True, alpha=0.3)

    #Grid 2: categorical infrastructure failure distribution
    colors = ['#ffbb78', '#ff4d4d', '#1f77b4']
    ax2.bar(df_alerts['security_level'], df_alerts['total_count'], color=colors, edgecolor='black', width=0.6)
    ax2.set_xlabel('Log Severity Level', fontweight='bold')
    ax2.set_ylabel('Registered Incidents Count', fontweight='bold')
    ax2.set_title('Operational System Vulnerability Logs', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.4, linestyle=':')

    # Overlay values on top of bars
    for index, val in enumerate(df_alerts['total_count']):
        ax2.text(index, val + 0.2, str(int(val)), ha='center', fontweight='bold')

    plt.tight_layout()

    output_filename = "executive_iot_report.png"
    plt.savefig(output_filename, dpi=300)
    print(f"Report visual successfully generated and saved to: {output_filename}")
    plt.show()

if __name__ == "__main__":
    generate_analytics_dashboard()
    