from typing import Dict

from PIL import Image, ImageDraw, ImageFont
from inky import InkyPHAT

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.inky.inky_page import InkyPage

class HomeMonitorPage(InkyPage):
    SUBCASE_WIDTH = 82

    def __init__(
        self,
        inky_display: InkyPHAT,
        influxdb_connectors: Dict[str, InfluxDBConnector],
        font: str,
        refresh_period: int,
        fields_configuration: Dict,
    ) -> None:
        self.fields_configuration = fields_configuration
        super().__init__(inky_display, influxdb_connectors, font, refresh_period)

    def get_data(self) -> Dict:
        data = {}

        for name, config in self.fields_configuration:
            if field_cat == "elec":
                data["elec"]["app_power"] = self.influxdb_connectors[
                    config["influxdb_connector"]
                ].query_mean_field(
                    config["measurement"], config["fields"]["app_power"], "10m"
                )

            else:
                for field_name, field in self.field_configuration["fields"].items():
                    data[name][field_name] = self.influxdb_connectors[
                        config["influxdb_connector"]
                    ].query_last_field(config["measurement"], field)

        return data

    def get_image(self, data) -> Image:
        img = super().get_image(data)
        draw = ImageDraw.Draw(img)

        header_font = ImageFont.truetype(self.font, 11)
        values_font = ImageFont.truetype(self.font, 14)

        # Outside weather
        weather_icon, mask = self.get_icon(data["weather"]["weather_description"])
        img.paste(weather_icon, (20, 5), mask)

        draw.text(
            (70, 16),
            f"{data['weather']['temperature']:.1f}˚C",
            font=values_font,
            fill=self.inky_displayYELLOW,
        )
        draw.text(
            (135, 16),
            f"{int(data['weather']['humidity'])} %",
            font=values_font,
            fill=self.inky_displayWHITE,
        )
        draw.text(
            (180, 16),
            f"{int(data['weather']['wind_speed'])}km/h",
            font=values_font,
            fill=self.inky_displayWHITE,
        )

        draw.line(
            (5, 50, self.inky_display.WIDTH - 5, 50),
            fill=self.inky_display.WHITE,
            width=2,
        )

        # Living room monitoring
        draw.text(
            (self.SUBCASE_WIDTH / 3, 55),
            "Salon",
            font=header_font,
            fill=self.inky_display.WHITE,
        )
        draw.text(
            (self.SUBCASE_WIDTH / 4, 75),
            f"{data['salon']['temperature']:.1f}˚C",
            font=values_font,
            fill=self.inky_display.YELLOW,
        )
        draw.text(
            (self.SUBCASE_WIDTH / 3 + 5, 95),
            f"{int(data['salon']['humidity'])}%",
            font=values_font,
            fill=self.inky_display.WHITE,
        )

        draw.line(
            (self.SUBCASE_WIDTH, 55, self.SUBCASE_WIDTH, self.inky_display.HEIGHT - 5),
            fill=self.inky_display.WHITE,
            width=2,
        )
        # Kitchen monitoring
        draw.text(
            (self.SUBCASE_WIDTH * 5 / 4, 55),
            "Cuisine",
            font=header_font,
            fill=self.inky_display.WHITE,
        )
        draw.text(
            (self.SUBCASE_WIDTH * 5 / 4, 75),
            f"{data['cuisine']['temperature']:.1f}",
            font=values_font,
            fill=self.inky_display.YELLOW,
        )
        draw.text(
            (self.SUBCASE_WIDTH * 4 / 3 + 5, 95),
            f"{int(data['cuisine']['humidity'])}%",
            font=values_font,
            fill=self.inky_display.WHITE,
        )

        draw.line(
            (
                2 * self.SUBCASE_WIDTH + 2,
                55,
                2 * self.SUBCASE_WIDTH + 2,
                self.inky_display.HEIGHT - 5,
            ),
            fill=self.inky_display.WHITE,
            width=2,
        )

        # Electricity monitoring
        draw.text(
            (self.SUBCASE_WIDTH * 11 / 5, 55),
            "Elec (10m)",
            font=header_font,
            fill=self.inky_display.WHITE,
        )
        draw.text(
            (self.SUBCASE_WIDTH * 9 / 4 + 3, 85),
            f"{data['elec']['app_power']} W",
            font=values_font,
            fill=self.inky_display.WHITE,
        )

        return img
