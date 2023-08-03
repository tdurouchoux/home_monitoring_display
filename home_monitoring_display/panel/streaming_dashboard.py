# %%
import os
from typing import Dict, List
from pathlib import Path
import argparse

import panel as pn

from home_monitoring_display.utils import extract_configs
from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.panel import indicator_factory

# TODO Clean all this shit


def construct_row(influxdb_connector: InfluxDBConnector, indicators_layout: List[Dict]) -> List:
    row_layout = []

    for indicator_config in indicators_layout:
        indicator_config_copy = indicator_config.copy()
        indicator_type = indicator_config_copy["type"]
        del indicator_config_copy["type"]

        if indicator_type == "trend":
            row_layout.append(
                indicator_factory.create_trend(
                    influxdb_connector, **indicator_config_copy
                )
            )
        elif indicator_type == "number":
            row_layout.append(
                indicator_factory.create_number(
                    influxdb_connector, **indicator_config_copy
                )
            )
        elif indicator_type == "gauge":
            row_layout.append(
                indicator_factory.create_gauge(
                    influxdb_connector, **indicator_config_copy
                )
            )
        elif indicator_type == "weather_icon":
            row_layout.append(
                indicator_factory.create_weather_icon(
                    influxdb_connector, **indicator_config_copy
                )
            )
        else:
            raise ValueError(
                f"Indicator type should either be 'trend' or 'number', got : {indicator_config['type']}"
            )

    return row_layout


def build_dashboard():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf-directory", help="configuration directory")
    args = parser.parse_args()

    layout_conf, connectors_conf = extract_configs(
        Path(args.conf_directory), "streaming_config.yaml", "connectors_config.yaml"
    ).values()

    influxdb_connectors = {
        name: InfluxDBConnector(**config) for name, config in connectors_conf.items()
    }

    layout_list = []

    for row_config in layout_conf["layouts"]:
        row_layout = construct_row(
            influxdb_connectors[row_config["influxdb_connector"]],
            row_config["indicators"],
        )

        layout_list.append(
            pn.Card(
                pn.Row(*row_layout),
                header=pn.widgets.StaticText(
                    value=f"<h1>{row_config['title']}</h1>", align="center"
                ),
                sizing_mode="stretch_width",
                collapsible=False,
                styles={"background": "#e6ebfc"},
            )
        )

    dashboard = pn.template.FastListTemplate(
        title=layout_conf["title"], main=layout_list, main_layout=None
    )
    return dashboard


if __name__.startswith("bokeh"):
    dashboard = build_dashboard()
    dashboard.servable()
    
if __name__ == "__main__":
    dashboard = build_dashboard()
    dashboard.show(port=5006)