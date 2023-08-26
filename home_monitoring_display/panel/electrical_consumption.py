import argparse
import os
import datetime as dt
from pathlib import Path

import pandas as pd
import panel as pn
import hvplot.pandas
import matplotlib.pyplot as plt

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.utils import extract_configs, load_config

# TODO Add a cache functionality to speed up queries
# TODO Refactor and clean this

# TODO Change calendar plot to matplotlib
# TODO Use for grid and other plots
# TODO Add tabs

CALENDAR_CARD_COLORS = {3000: "green", 7000: "yellow", 8000: "orange"}

# Get data




# Month selection



# Distribution tab


def plot_distrib_bar(df, group, sort_key, title):
    return (
        df.groupby(list(set((group, sort_key))))
        .agg({"PAPP": "mean"})
        .reset_index()
        .sort_values(sort_key, ascending=True)
        .hvplot.bar(
            x=group,
            y="PAPP",
            title=title,
            ylabel="VA",
            ylim=(0, 1.05 * df.PAPP.max()),
            responsive=True,
            shared_axes=False,
        )
    )


def plot_distrib_box(df, group, sort_key, title):
    return df.sort_values(sort_key, ascending=True).hvplot.box(
        y="PAPP",
        by=group,
        title=title,
        ylabel="Wh",
        ylim=(0, 1.05 * df.PAPP.max()),
        responsive=True,
        shared_axes=False,
    )

# Distributions
def get_distributions_layout(df_papp, df_papp_day):
    distributions = pn.Column(
        pn.Row(
            plot_distrib_bar(
                df_papp,
                "hour",
                "hour",
                title="Mean apparent power usage per hour",
            ),
            plot_distrib_box(
                df_papp,
                "hour",
                "hour",
                title="Distribution apparent power per hour",
            ),
            sizing_mode="stretch_both",
        ),
        pn.Row(
            plot_distrib_bar(
                df_papp_day,
                "day_name",
                "day_of_week",
                title="Mean daily power usage",
            ),
            plot_distrib_box(
                df_papp_day,
                "day_name",
                "day_of_week",
                title="Distribution daily apparent power ",
            ),
            sizing_mode="stretch_both",
        ),
        pn.Row(
            plot_distrib_bar(
                df_papp_day,
                "month_name",
                "month",
                title="Mean daily apparent power usage per month",
            ),
            plot_distrib_box(
                df_papp_day,
                "month_name",
                "month",
                title="Distribution daily apparent power per month",
            ),
            sizing_mode="stretch_both",
        ),
        sizing_mode="stretch_both",
    )
    
    return distributions


# Consumption
def get_consumption_layout(df_papp_day, df_base_day, select_month):

    @pn.depends(select_month=select_month)
    def get_consumption(select_month):
        df_papp_day_month = df_papp_day[df_papp_day["month_name"] == select_month]
        df_base_day_month = df_base_day[df_base_day["month_name"] == select_month]

        plot_energy_month = df_papp_day_month[:-1].hvplot.bar(
            x="day",
            y="PAPP",
            responsive=True,
            title="Energy consumption per day",
        ) * df_base_day_month.hvplot.bar(
            x="day",
            y="energy_consumption",
            legend=True,
        )
        total_consumption = pn.indicators.Number(
            name="Total consumption",
            value=df_base_day_month.energy_consumption.sum() / 1000,
            format="{value:.3f} kWh",
        )
        plot_price_month = df_base_day_month.hvplot.bar(
            x="day",
            y="price",
            responsive=True,
            title="Energy price per day",
        )
        total_price = pn.indicators.Number(
            name="Total consumption",
            value=df_base_day_month.price.sum(),
            format="{value:.2f} €",
        )

        grid_layout = pn.GridSpec(sizing_mode="stretch_both")

        grid_layout[0, 0:2] = plot_energy_month
        grid_layout[0, 3] = total_consumption
        grid_layout[1, 0:2] = plot_price_month
        grid_layout[1, 3] = total_price
        
        return grid_layout

    return get_consumption

# Calendar
def get_calendar_card(df_papp_day, date, max_papp):
    bar_fig = df_papp_day.plot.bar(
        x="hour", y="PAPP", ylim=(0, max_papp), ylabel="PAPP"
    ).get_figure()

    title = date.strftime("%A %d %B")

    total_day = df_papp_day.PAPP.sum()
    for thresh, color in CALENDAR_CARD_COLORS.items():
        background_color = color
        if total_day < thresh:
            break

    card = pn.Card(
        pn.pane.Matplotlib(
            bar_fig, sizing_mode="stretch_both", min_height=100, min_width=166
        ),
        title=title,
        collapsible=False,
        background=background_color,
        sizing_mode="stretch_both",
    )

    plt.close()

    return card


def get_calendar_layout(df_papp, select_month):

    @pn.depends(select_month=select_month)
    def get_calendar(select_month):
        df_papp_month = df_papp[df_papp["month_name"] == select_month]
        max_papp = df_papp_month.PAPP.max()

        min_date = df_papp.date.min()
        min_week = min_date.isocalendar().week

        grid_layout = pn.GridSpec(sizing_mode="stretch_both")

        for date in df_papp_month.date.unique():
            df_papp_day = df_papp_month[df_papp_month.date == date]

            grid_layout[
                date.isocalendar().week - min_week, date.isocalendar().weekday - 1
            ] = get_calendar_card(df_papp_day, date, max_papp)

        return grid_layout

    return get_calendar

def get_data():
    return df_papp, df_papp_day, df_base_day, df_base_day_shift

# Layout

def build_dashboard():
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

    df_papp = influxdb_client.query_field("teleinfo", "PAPP", start_date)
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
    
    month_list = list(
    df_papp_day.sort_values("date", ascending=True)["month_name"].unique()
    )

    select_month = pn.widgets.Select(name="Month", options=month_list)
    
    # df_papp 
    # df_papp_day
    # df_base_day
    
    consumption_layout = get_consumption_layout(df_papp_day, df_base_day, select_month)
    calendar_layout = get_calendar_layout(df_papp, select_month)
    distributions_layout = get_distributions_layout(df_papp, df_papp_day)
    
    
    layout = pn.template.MaterialTemplate(
        title="Electrical consumption",
        main=[
            pn.Card(
                consumption_layout, sizing_mode="stretch_both", title="Energy consumption"
            ),
            pn.Card(
                calendar_layout,
                sizing_mode="stretch_both",
                title="Calendar energy consumption",
            ),
            pn.Card(
                distributions_layout,
                sizing_mode="stretch_both",
                title="Energy consumption time distribution",
            ),
        ],
        sidebar=[select_month],
    )
    
    return layout



if __name__.startswith("bokeh"):
    dashboard = build_dashboard()
    dashboard.servable()
    
if __name__ == "__main__":
    dashboard = build_dashboard()
    dashboard.show(port=5006)
