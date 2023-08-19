import datetime as dt
from functools import reduce
from pathlib import Path
import argparse

import pandas as pd
import hvplot.pandas
import panel as pn
from panel.interact import interact

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.influxdb.multi_view_connector import MultiViewConnector
from home_monitoring_display.utils import extract_configs

# Adaptative range interval


def get_date_range(date_range, first_date):
    if date_range[0] < first_date:
        return {"value": (first_date, date_range[1])}
    return {"value": date_range}


# not used
# TODO must interact with cache
def get_groupby_interval(start, stop):
    time_delta = stop - start

    if time_delta > dt.timedelta(days=30):
        return "30m"
    if time_delta > dt.timedelta(days=7):
        return "10m"
    if time_delta > dt.timedelta(days=1):
        return "1m"
    return None


def plot_measures(multi_view_connector, measures, group_plots, date_range):
    start = pd.Timestamp(date_range[0]).replace(tzinfo=multi_view_connector.timezone)
    stop = pd.Timestamp(date_range[1]).replace(tzinfo=multi_view_connector.timezone)

    if len(measures) == 0:
        return pn.pane.Markdown("## No measures Selected")

    if len(measures) == 1:
        return pn.pane.HoloViews(
            multi_view_connector.query_measure(*measures[0][1:], start=start, stop=stop)
            .rename(
                columns={measures[0][3]: " ".join((measures[0][0], measures[0][3]))}
            )
            .hvplot(x="_time"),
            sizing_mode="stretch_both",
        )

    list_plots = [
        multi_view_connector.query_measure(*measure[1:], start=start, stop=stop)
        .rename(columns={measure[3]: " ".join((measure[0], measure[3]))})
        .hvplot(x="_time", responsive=True)
        for measure in measures
    ]
    if group_plots:
        return pn.pane.HoloViews(
            reduce(lambda x, y: x * y, list_plots).opts(show_legend=True),
            sizing_mode="stretch_both",
        )
    else:
        return pn.pane.HoloViews(
            reduce(lambda x, y: x + y, list_plots).cols(1),
            sizing_mode="stretch_both",
        )


def build_dashboard():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf-directory", help="configuration directory")
    args = parser.parse_args()

    analytics_conf, connectors_conf = extract_configs(
        Path(args.conf_directory), "analytics_config.yaml", "connectors_config.yaml"
    ).values()

    influxdb_connectors = {}

    for connector_name in connectors_conf:
        conf = dict(
            connectors_conf[connector_name],
            **analytics_conf[connector_name].get("extra_params", {})
        )

        influxdb_connectors[connector_name] = InfluxDBConnector(**conf)

    multi_view_connector = MultiViewConnector(**influxdb_connectors)

    first_date = multi_view_connector.get_first_date().replace(tzinfo=None)
    last_date = multi_view_connector.get_last_date().replace(tzinfo=None)

    date_range_select = pn.widgets.Select(
        options={
            "2 heures": (last_date - dt.timedelta(hours=2), last_date),
            "12 heures": (last_date - dt.timedelta(hours=12), last_date),
            "1 jour": (last_date - dt.timedelta(days=1), last_date),
            "2 jours": (last_date - dt.timedelta(days=2), last_date),
            "1 semaine": (last_date - dt.timedelta(days=7), last_date),
            "1 mois": (last_date - dt.timedelta(days=30), last_date),
            "Tout": (first_date, last_date),
        },
        value=(last_date - dt.timedelta(hours=2), last_date),
    )

    date_range = pn.bind(get_date_range, date_range_select, first_date)

    date_range_picker = pn.widgets.DatetimeRangePicker(
        name="Période temporelle",
        refs=date_range,
        start=first_date,
        end=last_date,
    )

    group_plots = pn.widgets.Checkbox(name="Group plots", value=True)

    measures_options = {
        " | ".join((analytics_conf[connector_name]["measures"][measurement], field)): (
            analytics_conf[connector_name]["measures"][measurement],
            connector_name,
            measurement,
            field,
        )
        for (
            connector_name,
            measurement,
        ), measurement_schema in multi_view_connector.schema.items()
        for field, field_type in measurement_schema["fields"].items()
        if field_type in ["integer", "float", "boolean"]
    }

    measures = pn.widgets.MultiChoice(
        name="Measures",
        options=measures_options,
    )

    # Check how bind works
    plot_widget = pn.bind(
        plot_measures, multi_view_connector, measures, group_plots, date_range_picker
    )

    pn.extension(sizing_mode="stretch_both")
    dashboard = pn.template.VanillaTemplate(
        title="Exploration temporelle",
        sidebar=[
            date_range_select,
            date_range_picker,
            group_plots,
            measures,
        ],
        main=plot_widget,
    )
    return dashboard


if __name__.startswith("bokeh"):
    dashboard = build_dashboard()
    dashboard.servable()

if __name__ == "__main__":
    dashboard = build_dashboard()
    dashboard.show(port=5006)
