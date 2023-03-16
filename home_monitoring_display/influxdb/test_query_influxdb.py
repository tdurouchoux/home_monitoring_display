from influxdb_client import InfluxDBClient

username = "admin"
password = "bodyguard"

database = "homemonitor"
retention_policy = "autogen"

bucket = f"{database}/{retention_policy}"

with InfluxDBClient(
    url="http://192.168.1.16:8086", token=f"{username}:{password}", org="-"
) as client:
    query_api = client.query_api()
    # query = f'from(bucket: "{bucket}") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "openweather_current_weather") |> filter(fn: (r) => r._field == "temp")'
    query = f'from(bucket: "{bucket}") |> range(start: -1h)'
    tables = query_api.query(query)
    for record in tables[0].records:
        print(
            f"#{record.get_time()} #{record.get_measurement()}: #{record.get_field()} #{record.get_value()}"
        )
