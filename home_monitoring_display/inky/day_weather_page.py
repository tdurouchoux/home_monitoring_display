import os
from typing import Dict, List
import datetime as dt

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from inky import InkyPHAT
import requests

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.inky.inky_page import InkyPage


class DayWeatherPage(InkyPage):
    CASE_HEIGHT = 28
    CASE_WIDTH = 81
    RAIN_WIDTH = 20
    RAIN_HEAVY_THRESHOLD = 5

    def __init__(
        self,
        inky_display: InkyPHAT,
        influxdb_connectors: Dict[str, InfluxDBConnector],
        resources_path: str,
        font: str,
        refresh_period: int,
        gps_coordinates: List[float],
    ) -> None:
        super().__init__(
            inky_display, influxdb_connectors, resources_path, font, refresh_period
        )

        self.gps_coordinates = gps_coordinates

        if "OPENWEATHER_API_KEY" not in os.environ:
            raise ValueError("OPENWEATHER_API_KEY not found in environment variables")
        self.api_key = os.environ["OPENWEATHER_API_KEY"]

        self.higher_font = ImageFont.truetype(self.font, 14)
        self.lower_font = ImageFont.truetype(self.font, 10)

    def get_data(self) -> Dict:
        response = requests.get(
            f"https://api.openweathermap.org/data/3.0/onecall?"
            f"lat={self.gps_coordinates[0]}&lon={self.gps_coordinates[1]}&"
            f"units=metric&exclude=daily,alerts&appid={self.api_key}"
        )

        if response.status_code != 200:
            print("Failed to retrieve weather data")
            return {}

        result = response.json()

        data = {}

        # Current weathers
        data["current_time"] = dt.datetime.fromtimestamp(
            result["current"]["dt"]
        ).strftime("%H:%M")
        data["current_temp"] = result["current"]["temp"]
        data["current_description"] = result["current"]["weather"][0]["description"]

        for i in range(6):
            mean_rain = (
                sum(
                    [
                        x["precipitation"]
                        for x in result["minutely"][i * 10 : (i + 1) * 10]
                    ]
                )
                / 10
            )

            if mean_rain == 0:
                data[f"rain_{i}"] = self.inky_display.BLACK
            elif mean_rain < self.RAIN_HEAVY_THRESHOLD:
                data[f"rain_{i}"] = self.inky_display.WHITE
            else:
                data[f"rain_{i}"] = self.inky_display.YELLOW

        for i in range(6):
            data[f"hour_{i}_time"] = dt.datetime.fromtimestamp(
                result["hourly"][(i + 1) * 3]["dt"]
            ).strftime("%H:%M")
            data[f"hour_{i}_temp"] = result["hourly"][(i + 1) * 3]["temp"]
            data[f"hour_{i}_description"] = result["hourly"][(i + 1) * 3]["weather"][0][
                "description"
            ]

        return data

    def draw_3hour_case(
        self, time: str, temp: str, description: str, x: int, y: int, img: Image
    ) -> None:
        draw_case = ImageDraw.Draw(img)
        draw_case.rectangle(
            (x, y, x + self.CASE_WIDTH + 2, y + self.CASE_HEIGHT + 2),
            fill=None,
            outline=self.inky_display.WHITE,
            width=2,
        )

        weather_icon, mask_image = self.get_icon(description, (26, 26))
        img.paste(weather_icon, (x + 12, y + 2), mask_image)

        draw_case.text(
            (x + 43, y + 4), time, font=self.lower_font, fill=self.inky_display.WHITE
        )
        draw_case.text(
            (x + 43, y + 16), temp, font=self.lower_font, fill=self.inky_display.WHITE
        )

    def get_image(self, data) -> Image:
        img = super().get_image(data)
        draw = ImageDraw.Draw(img)

        # Draw current weather
        weather_icon, mask_image = self.get_icon(data["current_description"])
        img.paste(weather_icon, (10, 10), mask_image)

        draw.text(
            (55, 10),
            data["current_time"],
            font=self.higher_font,
            fill=self.inky_display.WHITE,
        )
        draw.text(
            (57, 30),
            data["current_temp"],
            font=self.higher_font,
            fill=self.inky_display.WHITE,
        )

        # Draw rain
        draw.text(
            (147, 2), "Pluie (1h)", font=self.lower_font, fill=self.inky_display.WHITE
        )
        for i in range(6):
            draw.rectangle(
                (
                    110 + i * (self.RAIN_WIDTH + 2),
                    18,
                    110 + (i + 1) * (self.RAIN_WIDTH + 2),
                    45,
                ),
                fill=data[f"rain{i}"],
                outline=self.inky_display.WHITE,
                width=2,
            )

        # Draw day weather
        for i in range(3):
            self.draw_3hour_case(
                data[f"hour_{i}_time"],
                data[f"hour_{i}_temp"],
                draw[f"hour_{i}_description"],
                (i % 3) * (2 + self.CASE_WIDTH),
                60 + (i // 3) * (2 + self.CASE_HEIGHT),
                img,
            )
