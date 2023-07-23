from typing import Dict

from PIL import Image, ImageDraw, ImageFont
from inky import InkyPHAT

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.inky.inky_page import InkyPage


def iter_list(l):
    i = 0
    while True:
        yield l[i % len(l)]
        i += 1


class SysMonitorPage(InkyPage):
    CIRCLE_SPACING = 12
    CIRCLE_DIAMETER = 50
    RECT_WIDTH = 12

    def __init__(
        self,
        inky_display: InkyPHAT,
        influxdb_connectors: Dict[str, InfluxDBConnector],
        resources_path: str,
        font: str,
        refresh_period: int,
        fields_configuration: Dict,
    ) -> None:
        super().__init__(
            inky_display, influxdb_connectors, resources_path, font, refresh_period
        )
        self.iter_connectors = iter_list(list(influxdb_connectors.keys()))
        self.fields_configuration = fields_configuration
        self.title_font = ImageFont.truetype(self.font, 12)
        self.metric_font = ImageFont.truetype(self.font, 10)

    @property
    def connector_name(self):
        return next(self.iter_connectors)

    def get_data(self) -> Dict:
        data = {}

        data["connector_name"] = self.connector_name
        config = self.fields_configuration[data["connector_name"]]

        for field in ["cpu_usage", "ram_usage"]:
            data[f"{field}_10m_avg"] = self.influxdb_connectors[
                data["connector_name"]
            ].query_agg_field(
                config[field]["measurement"], config[field]["field"], "10m"
            )

        for field in ["mem_usage", "cpu_temp"]:
            data[field] = self.influxdb_connectors[
                data["connector_name"]
            ].query_last_field(config[field]["measurement"], config[field]["field"])
            data[f"max_{field}"] = config[field]["max_value"]

        return data

    def draw_metric_monitor(
        self,
        metric_name: str,
        metric_value: int,
        x: int,
        y: int,
        draw: ImageDraw,
        max_value: int = 100,
        legend_text: str = "%",
        draw_circle: bool = True,
    ) -> None:
        if draw_circle:
            width = self.CIRCLE_DIAMETER
            circle_coor = [x, y, x + self.CIRCLE_DIAMETER, y + self.CIRCLE_DIAMETER]
            draw.pieslice(
                circle_coor,
                -90,
                -90 + (metric_value * 360 / max_value),
                fill=self.inky_display.YELLOW,
                outline=self.inky_display.YELLOW,
            )
            draw.ellipse(circle_coor, fill=None, outline=self.inky_display.WHITE)

        else:
            width = self.RECT_WIDTH
            rect_coor = [x, y, x + self.RECT_WIDTH, y + self.CIRCLE_DIAMETER]
            rect_fill_coor = rect_coor.copy()
            rect_fill_coor[1] = max(
                rect_coor[1] + self.CIRCLE_DIAMETER * (1 - metric_value / max_value),
                rect_coor[1],
            )

            draw.rectangle(
                rect_fill_coor,
                fill=self.inky_display.YELLOW,
                outline=self.inky_display.YELLOW,
            )
            draw.rectangle(rect_coor, fill=None, outline=self.inky_display.WHITE)

        draw.text(
            (x + width / 2 - (3 * len(metric_name)), y - 15),
            metric_name,
            font=self.metric_font,
            fill=self.inky_display.WHITE,
        )
        legend = f"{metric_value}{legend_text}"
        draw.text(
            (x + width / 2 - (3 * len(legend)), y + self.CIRCLE_DIAMETER + 5),
            legend,
            font=self.metric_font,
            fill=self.inky_display.YELLOW,
        )

    def draw_image(self, data) -> Image:
        img = super().draw_image(data)
        draw = ImageDraw.Draw(img)

        draw.text(
            (62 - 3 * len(data["connector_name"]), 2),
            f"System monitoring {data['connector_name']}",
            font=self.font_title,
            fill=self.inky_display.WHITE,
        )
        draw.line(
            (5, 20, self.inky_display.WIDTH - 5, 20),
            fill=self.inky_display.WHITE,
            width=2,
        )

        self.draw_metric_monitor(
            "CPU (10m)", data["cpu_usage_10m_avg"], self.CIRCLE_SPACING, 43, draw
        )
        self.draw_metric_monitor(
            "RAM (10m)",
            data["ram_usage_10m_avg"],
            2 * self.CIRCLE_SPACING + self.CIRCLE_DIAMETER,
            43,
            draw,
        )
        self.draw_metric_monitor(
            "Memory",
            data["mem_usage"],
            2 * self.CIRCLE_DIAMETER + 3 * self.CIRCLE_SPACING,
            43,
            draw,
            max_value=data["max_mem_usage"],
            legend_text=f"GB/{data['max_mem_usage']}GB",
        )
        self.draw_metric_monitor(
            "Temp",
            data["cpu_temp"],
            3 * (self.CIRCLE_DIAMETER + 2 * self.CIRCLE_SPACING),
            43,
            draw,
            max_value=data["max_cpu_temp"],
            legend_text="˚C",
            draw_circle=False,
        )

        return img
