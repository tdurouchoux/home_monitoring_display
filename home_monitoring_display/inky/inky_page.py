import os
from abc import ABC, abstractmethod
from typing import Dict, Tuple
from datetime import timedelta

from PIL import Image, ImageDraw
from inky import InkyPHAT
import numpy as np
import reactivex as rx
from reactivex import operators
from reactivex.scheduler import NewThreadScheduler

from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector

# ! this code is not made for larger screens than phat

RPI_MAX_TEMP = 85

MAPPING_ICON_ID = {
    "thunderstorm with light rain": "icon-storm.png",
    "thunderstorm with rain": "icon-storm.png",
    "thunderstorm with heavy rain": "icon-storm.png",
    "light thunderstorm": "icon-storm.png",
    "thunderstorm": "icon-storm.png",
    "heavy thunderstorm": "icon-storm.png",
    "ragged thunderstorm": "icon-storm.png",
    "thunderstorm with light drizzle": "icon-storm.png",
    "thunderstorm with drizzle": "icon-storm.png",
    "thunderstorm with heavy drizzle": "icon-storm.png",
    "light rain": "icon-rain.png",
    "moderate rain": "icon-rain.png",
    "heavy intensity rain": "icon-rain.png",
    "very heavy rain": "icon-rain.png",
    "extreme rain": "icon-rain.png",
    "freezing rain": "icon-rain.png",
    "light intensity shower rain": "icon-rain.png",
    "shower rain": "icon-rain.png",
    "heavy intensity shower rain": "icon-rain.png",
    "ragged shower rain": "icon-rain.png",
    "light intensity drizzle": "icon-rain.png",
    "drizzle": "icon-rain.png",
    "heavy intensity drizzle": "icon-rain.png",
    "light intensity drizzle rain": "icon-rain.png",
    "drizzle rain": "icon-rain.png",
    "heavy intensity drizzle rain": "icon-rain.png",
    "shower rain and drizzle": "icon-rain.png",
    "heavy shower rain and drizzle": "icon-rain.png",
    "shower drizzle": "icon-rain.png",
    "light snow": "icon-snow.png",
    "snow": "icon-snow.png",
    "heavy snow": "icon-snow.png",
    "sleet": "icon-snow.png",
    "light shower sleet": "icon-snow.png",
    "shower sleet": "icon-snow.png",
    "light rain and snow": "icon-snow.png",
    "rain and snow": "icon-snow.png",
    "light shower snow": "icon-snow.png",
    "shower snow": "icon-snow.png",
    "heavy shower snow": "icon-snow.png",
    "mist": "icon-mist.png",
    "smoke": "icon-mist.png",
    "haze": "icon-mist.png",
    "sand/dust whirls": "icon-mist.png",
    "fog": "icon-mist.png",
    "sand": "icon-mist.png",
    "dust": "icon-mist.png",
    "ash": "icon-mist.png",
    "squalls": "icon-mist.png",
    "tornado": "icon-storm.png",
    "clear sky": "icon-sun.png",
    "few clouds": "icon-thin-cloud.png",
    "scattered clouds": "icon-thin-cloud.png",
    "broken clouds": "icon-cloud.png",
    "overcast clouds": "icon-cloud.png",
}


class InkyPage(ABC):
    def __init__(
        self,
        inky_display: InkyPHAT,
        influxdb_connectors: Dict[str, InfluxDBConnector],
        resources_path: str,
        font: str,
        refresh_period: int,
    ) -> None:
        self.inky_display = inky_display
        self.influxdb_connectors = influxdb_connectors

        self.resources_path = resources_path
        self.font = os.path.join(self.resources_path, font)

        self.refresh_period = refresh_period
        self.scheduler = NewThreadScheduler()
        self.rx_event = None

        self.enabled = False

    @abstractmethod
    def get_data(self):
        pass

    def get_icon(self, weather_description: str, resize_dim: Tuple[int] = None):
        icon = Image.open(
            os.path.join(self.resources_path, MAPPING_ICON_ID[weather_description])
        ).convert("P")
        icon = icon.crop((4, 4, 38, 43))
        if resize_dim is not None:
            icon = icon.resize(resize_dim)
        mask = Image.fromarray(
            np.where(np.array(icon) == 3, 0, 255).astype(np.uint8)
        ).convert("1")

        return icon, mask

    def get_image(self, data: Dict) -> Image:
        img = Image.new("P", (self.inky_display.WIDTH, self.inky_display.HEIGHT))
        draw = ImageDraw.Draw(img)

        # Can be useful for debugging
        img.putpalette([255, 255, 255, 0, 0, 0, 233, 245, 66])

        draw.rectangle(
            (0, 0, self.inky_display.WIDTH, self.inky_display.HEIGHT),
            fill=self.inky_display.BLACK,
            outline=self.inky_display.BLACK,
        )

        return img

    def display_image(self, data: Dict, rotate: bool = True) -> None:
        img = self.get_image(data)

        if rotate:
            img = img.rotate(180)

        print("Created image")
        self.inky_display.set_image(img)
        self.inky_display.show()

    def refresh(self) -> None:
        data = self.get_data()
        print("Retrieved data")
        self.display_image(data)

    def enable_auto_refresh(self) -> None:
        self.refresh()

        # ? maybe implement catch / retry
        self.rx_event = (
            rx.interval(period=timedelta(seconds=self.refresh_period))
            .pipe(
                operators.map(lambda i: self.get_data()),
                operators.subscribe_on(self.scheduler),
            )
            .subscribe(lambda data: self.display_image(data))
        )

        self.enabled = True

    def disable_auto_refresh(self) -> None:
        self.rx_event.dispose()
        self.enabled = False
