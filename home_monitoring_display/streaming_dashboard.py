# %%
import os
from pathlib import Path

import panel as pn

from home_monitoring_display.utils import load_config
from home_monitoring_display.query_influxdb import InfluxDBConnector
from home_monitoring_display.indicator_factory import IndicatorFactory

conf_directory = Path(__file__).parent.parent.joinpath("conf")

conf = load_config(conf_directory.joinpath("streaming_config.yaml"))
connectors_conf = load_config(conf_directory.joinpath("connectors_config.yaml"))

influxdb_connectors = {
    name: InfluxDBConnector(**config) for name, config in connectors_conf.items()
}

indicator_factory = IndicatorFactory(**conf["indicators_parameters"])

layout_list = []

for layout_config in conf["layouts"]:
    indicator_list = []
    influxdb_connector = influxdb_connectors[layout_config["influxdb_connector"]]

    for indicator_config in layout_config["indicators"]:
        indicator_config_copy = indicator_config.copy()
        del indicator_config_copy["type"]

        if indicator_config["type"] == "trend":
            indicator_list.append(
                indicator_factory.create_trend(
                    influxdb_connector, **indicator_config_copy
                )
            )
        elif indicator_config["type"] == "number":
            indicator_list.append(
                indicator_factory.create_number(
                    influxdb_connector, **indicator_config_copy
                )
            )
        elif indicator_config["type"] == "gauge":
            indicator_list.append(
                indicator_factory.create_gauge(
                    influxdb_connector, **indicator_config_copy
                )
            )
        else:
            raise ValueError(
                f"Indicator type should either be 'trend' or 'number', got : {indicator_config['type']}"
            )

    layout_list.append(
        pn.Card(
            pn.Row(*indicator_list),
            title=layout_config["title"],
            sizing_mode="stretch_both",
            collapsible=False,
        )
    )


template = pn.template.FastListTemplate(
    title=conf["title"], main=layout_list, main_layout=""
)
template.servable()
