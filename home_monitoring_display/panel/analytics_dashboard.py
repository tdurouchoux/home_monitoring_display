import os
import datetime as dt
from functools import reduce
from pathlib import Path

import pytz
import pandas as pd
import hvplot.pandas
import panel as pn
from panel.interact import interact

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.utils import load_config
from home_monitoring_display.influxdb.multi_view_connector import MultiViewConnector

conf = load_config(
    Path(__file__)
    .parent.parent.parent.joinpath("conf")
    .joinpath("connectors_config.yaml")
)

# TODO Fix this shit

# pi_config = conf["pi"]
# pi_config["timeout"] = 100_000
# pi_config["default_group_measurement"] = {"teleinfo": "30s"}

hm_client = InfluxDBConnector(**conf["homemonitor"])
# pi_client = InfluxDBConnector(**pi_config)
# connector = MultiViewConnector(hm_client, pi_client)
connector = MultiViewConnector(hm_client)
# Setup widgets

measure_options = connector.get_measure_options(
    select_types=["integer", "float", "boolean"]
)

measures = pn.widgets.MultiChoice(
    name="Measures",
    options=measure_options,
)

group_plots = pn.widgets.Checkbox(name="Group plots", value=True)

start_date = min(
    *[meas_schema["first_date"] for meas_schema in connector.schema.values()]
)
start_date = start_date.replace(tzinfo=None)
end_date = max(*[meas_schema["last_date"] for meas_schema in connector.schema.values()])
end_date = end_date.replace(tzinfo=None)

datetime_range_picker = pn.widgets.DatetimeRangePicker(
    name="Période temporelle",
    # value=(end_date - dt.timedelta(days=2), end_date),
    value=(end_date - dt.timedelta(minutes=20), end_date),
    start=start_date,
    end=end_date,
)

# Analytic view


@pn.depends(
    measures=measures, group_plots=group_plots, date_range=datetime_range_picker
)
def plot_measures(measures, group_plots, date_range):
    start = pd.Timestamp(date_range[0]).replace(tzinfo=connector.timezone)
    stop = pd.Timestamp(date_range[1]).replace(tzinfo=connector.timezone)

    if len(measures) == 0:
        return pn.pane.Markdown("## No measures Selected")
    elif len(measures) == 1:
        return pn.pane.HoloViews(
            connector.query_measure(
                *measures[0].split(" | "), start=start, stop=stop
            ).hvplot(x="_time"),
            sizing_mode="stretch_both",
        )
    else:
        list_plots = [
            connector.query_measure(
                *measure.split(" | "), start=start, stop=stop
            ).hvplot(x="_time", responsive=True)
            for measure in measures
        ]
        if group_plots:
            return pn.pane.HoloViews(
                reduce(lambda x, y: x * y, list_plots), sizing_mode="stretch_both"
            )
        else:
            return pn.pane.HoloViews(
                reduce(lambda x, y: x + y, list_plots).cols(1),
                sizing_mode="stretch_both",
            )


pn.extension(sizing_mode="stretch_both")
template = pn.template.VanillaTemplate(
    title="Measures analytics",
    sidebar=[
        datetime_range_picker,
        group_plots,
        measures,
    ],
    main=plot_measures,
)
template.servable()
