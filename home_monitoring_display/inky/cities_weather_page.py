import os
from typing import Dict, List

from PIL import Image, ImageDraw, ImageFont
from inky import InkyPHAT
import requests

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display.inky.inky_page import InkyPage

# TODO handle failed requests


class CitiesWeatherPage(InkyPage):
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
        cities: List[str],
    ) -> None:
        super().__init__(
            inky_display, influxdb_connectors, resources_path, font, refresh_period
        )
        self.cities = cities

        if len(self.cities) > 4:
            raise ValueError(f"Maximum 4 cities allowed, got {len(self.cities)} cities")

        if "OPENWEATHER_API_KEY" not in os.environ:
            raise ValueError("OPENWEATHER_API_KEY not found in environment variables")
        self.api_key = os.environ["OPENWEATHER_API_KEY"]

        self.title_font = ImageFont.truetype(self.font, 12)
        self.sensor_font = ImageFont.truetype(self.font, 14)

    def get_data(self):
        data = {}

        for city in self.cities:
            data[city] = {}
            response = requests.get(
                "http://api.openweathermap.org/data/2.5/weather?"
                f"q={city}&appid={self.api_key}&units=metric"
            )

            if response.status_code != 200:
                print("Failed to retrieve weather data")
                return {}

            result = response.json()

            if len(result["name"]) < len(city):
                data[city]["name"] = result["name"]
            else:
                data[city]["name"] = city
            data[city]["weather_description"] = result["weather"][0]["description"]
            data[city]["temperature"] = result["main"]["temp"]
            data[city]["humidity"] = result["main"]["humidity"]

        return data

    def draw_city_meteo(
        self,
        city: str,
        temp: float,
        hum: int,
        description: str,
        x: int,
        y: int,
        img: Image,
    ) -> None:
        draw_city = ImageDraw.Draw(img)
        draw_city.text(
            (x + (self.inky_display.WIDTH / 4) - 3 * len(city), y + 2),
            city,
            font=self.title_font,
            fill=self.inky_display.WHITE,
        )

        weather_icon, mask_image = self.get_icon(description)
        img.paste(weather_icon, (x + 15, y + 15), mask_image)

        draw_city.text(
            (x + 65, y + 18),
            f"{temp:.1f}˚C",
            font=self.sensor_font,
            fill=self.inky_display.YELLOW,
        )
        draw_city.text(
            (x + 75, y + 36),
            f"{hum}%",
            font=self.sensor_font,
            fill=self.inky_display.WHITE,
        )

    def get_image(self, data) -> Image:
        img = super().get_image(data)
        draw = ImageDraw.Draw(img)

        draw.line(
            (
                5,
                self.inky_display.HEIGHT / 2,
                self.inky_display.WIDTH - 5,
                self.inky_display.HEIGHT / 2,
            ),
            fill=self.inky_display.WHITE,
            width=2,
        )
        draw.line(
            (
                self.inky_display.WIDTH / 2,
                5,
                self.inky_display.WIDTH / 2,
                self.inky_display.HEIGHT - 5,
            ),
            fill=self.inky_display.WHITE,
            width=2,
        )

        for i, city in enumerate(self.cities):
            self.draw_city_meteo(
                data[city]["name"],
                data[city]["temperature"],
                data[city]["humidity"],
                data[city]["weather_description"],
                (i % 2) * int((self.inky_display.WIDTH / 2) + 1),
                (i // 2) * int((self.inky_display.HEIGHT / 2) + 1),
                img,
            )

        return img
