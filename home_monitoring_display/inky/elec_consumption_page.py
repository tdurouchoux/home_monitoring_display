from typing import Dict, List
import datetime as dt

from PIL import Image, ImageDraw, ImageFont
from inky import InkyPHAT

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.inky.inky_page import InkyPage


class ElecConsumptionPage(InkyPage):
    WEEK_PRICE = 0.2352
    WEEKEND_PRICE = 0.1650
    LINE_GROUP_INTER = "5m"

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

        self.fields_configuration = fields_configuration
        self.title_font = ImageFont.truetype(self.font, 12)
        self.header_font = ImageFont.truetype(self.font, 11)
        self.value_font = ImageFont.truetype(self.font, 14)

    def get_data(self):
        data = {}
        connector = self.influxdb_connectors[
            self.fields_configuration["influxdb_connector"]
        ]
        measurement = self.fields_configuration["measurement"]
        app_power_field = self.fields_configuration["fields"]["app_power"]
        total_power_field = self.fields_configuration["fields"]["total_power"]

        # Instant power
        df_hour_consumption = connector.query_field(
            measurement, app_power_field, "1h", groupby_interval=self.LINE_GROUP_INTER
        )
        df_hour_consumption = df_hour_consumption.sort_values("_time", ascending=True)
        data[f"line_consumption"] = [
            row[app_power_field] for _, row in df_hour_consumption.iterrows()
        ]

        # Power consumption
        day_minutes = dt.datetime.now().hour * 60 + dt.datetime.now().minute
        min_day_power = connector.query_agg_field(
            measurement, total_power_field, f"{day_minutes}m", aggregation_func="min"
        )
        last_power = connector.query_last_field(measurement, total_power_field)

        data["day_consumption"] = (last_power - min_day_power) / 1000
        data["day_price"] = (
            data["day_consumption"] * self.WEEK_PRICE
            if dt.date.today().weekday() < 5
            else data["day_consumption"] * self.WEEKEND_PRICE
        )

        return data

    def draw_line_graph(
        self, line: List[int], width: int, height: int, x: int, y: int, draw: ImageDraw
    ) -> None:
        # Draw frame
        draw.line((x, y, x, y + height), fill=self.inky_display.WHITE)
        draw.line((x - 2, y + 2, x, y), fill=self.inky_display.WHITE)
        draw.line((x + 2, y + 2, x, y), fill=self.inky_display.WHITE)
        draw.line((x, y + height, x + width, y + height), fill=self.inky_display.WHITE)
        draw.line(
            (x + width - 2, y + height - 2, x + width, y + height),
            fill=self.inky_display.WHITE,
        )
        draw.line(
            (x + width - 2, y + height + 2, x + width, y + height),
            fill=self.inky_display.WHITE,
        )

        num_points = len(line)
        x_step = width / (num_points - 1)
        y_step = height / (max(line) * 1.3 - 0)
        x_coords = [i * x_step for i in range(num_points)]
        y_coords = [line[i] * y_step for i in range(num_points)]

        for i in range(num_points - 1):
            draw.line(
                (
                    x + x_coords[i],
                    y + height - y_coords[i],
                    x + x_coords[i + 1],
                    y + height - y_coords[i + 1],
                ),
                fill=self.inky_display.YELLOW,
            )

    def get_image(self, data: Dict) -> Image:
        img = super().get_image(data)
        draw = ImageDraw.Draw(img)

        # Title
        draw.text(
            (50, 2),
            "Electrical consumption",
            font=self.title_font,
            fill=self.inky_display.WHITE,
        )
        draw.line(
            (5, 20, self.inky_display.WIDTH - 5, 20),
            fill=self.inky_display.WHITE,
            width=2,
        )
        draw.text(
            (9, 25),
            " -1 hour:",
            font=self.header_font,
            fill=self.inky_display.WHITE,
        )

        # Last hour consumption
        self.draw_line_graph(data["line_consumption"], 70, 80, 10, 35, draw)

        # Last 10 minutes consumption
        draw.text(
            (88, 50),
            f"avg(-{self.LINE_GROUP_INTER}):",
            font=self.header_font,
            fill=self.inky_display.WHITE,
        )
        draw.text(
            (100, 75),
            f"{round(data['line_consumption'][-1])} W",
            font=self.value_font,
            fill=self.inky_display.YELLOW,
        )

        draw.line((158, 25, 158, 117), fill=self.inky_display.WHITE, width=2)

        # Day consumption
        draw.text(
            (186, 27), "Today:", font=self.header_font, fill=self.inky_display.WHITE
        )
        draw.text(
            (172, 50),
            f"{data['day_consumption']:.3f} kWh",
            font=self.value_font,
            fill=self.inky_display.YELLOW,
        )
        draw.text(
            (182, 85),
            f"{data['day_price']:.2f} €",
            font=self.value_font,
            fill=self.inky_display.YELLOW,
        )

        return img
