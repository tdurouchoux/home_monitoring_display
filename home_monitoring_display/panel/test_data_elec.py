
from pathlib import Path
import argparse

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.utils import extract_configs



def test_data_processing():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf-directory", help="configuration directory")
    args = parser.parse_args()
    
    consumption_conf, connectors_conf = extract_configs(
        Path(args.conf_directory), "consumption_config.yaml", "connectors_config.yaml"
    ).values()


    influxdb_client = InfluxDBConnector(**connectors_conf[consumption_conf["influxdb_connector"]])
    schema = influxdb_client.get_schema()
    
    start_date = schema["teleinfo"]["first_date"]
    
    # groupby interval 1h
    # get_data()

    df_papp = influxdb_client.query_field("teleinfo", "PAPP", start_date, groupby_interval="1h", aggregation_func="mean")
    df_papp["day"] = df_papp._time.dt.day
    df_papp["day_of_week"] = df_papp._time.dt.day_of_week
    df_papp["date"] = df_papp._time.dt.date
    df_papp["hour"] = df_papp._time.dt.hour
    df_papp["month_name"] = df_papp._time.apply(lambda d: d.strftime("%B %Y"))
    df_papp["week"] = df_papp._time.dt.isocalendar().week
    df_papp["week"] -= df_papp.week.min()


    df_papp_day = (
        df_papp.groupby(["date", "month_name", "day_of_week"])
        .agg({"PAPP": "sum"})
        .reset_index()
    )
    df_papp_day["day"] = df_papp_day.date.apply(lambda d: int(d.strftime("%d")))
    df_papp_day["day_name"] = df_papp_day.date.apply(lambda d: d.strftime("%A"))
    df_papp_day["month"] = df_papp_day.date.apply(lambda d: d.month) 

    df_base = influxdb_client.query_field(
        "teleinfo", "BASE", start_date, groupby_interval="1h", aggregation_func="min"
    )

    current_price = {"week": 0.2352, "weekend": 0.1650}

    df_base["date"] = df_base._time.dt.date
    df_base_day = df_base.groupby("date").agg({"BASE": "min"}).reset_index()
    df_base_day["day"] = df_base_day.date.apply(lambda d: int(d.strftime("%d")))
    df_base_day["day_of_week"] = df_base_day.date.apply(lambda d: d.weekday())
    df_base_day["month_name"] = df_base_day.date.apply(lambda d: d.strftime("%B %Y"))

    query_max = f"SELECT last(BASE) AS BASE FROM teleinfo"
    max_base = influxdb_client.client.query(query_max)["teleinfo"]["BASE"].values[0]

    df_base_day_shift = df_base_day.BASE.shift(-1)
    df_base_day_shift.iloc[-1] = max_base


    df_base_day["energy_consumption"] = df_base_day_shift - df_base_day.BASE

    df_base_day["price"] = df_base_day[["day_of_week", "energy_consumption"]].apply(
        lambda row: (
            row["energy_consumption"] * current_price["week"] / 1000
            if row["day_of_week"] < 5
            else row["energy_consumption"] * current_price["weekend"] / 1000
        ),
        axis=1,
    )

if __name__ == "__main__":
    test_data_processing()