from typing import Dict, List
import datetime as dt

import panel as pn

from home_monitoring_display.query_influxdb import InfluxDBConnector

TIME_IND_MULT = {
    "w": 7 * 24 * 60 * 60 * 1000,
    "d": 24 * 60 * 60 * 1000,
    "h": 60 * 60 * 1000,
    "m": 60 * 1000,
    "s": 1000,
}


MAPPING_ICON_ID = {
    "thunderstorm with light rain": "11",
    "thunderstorm with rain": "11",
    "thunderstorm with heavy rain": "11",
    "light thunderstorm": "11",
    "thunderstorm": "11",
    "heavy thunderstorm": "11",
    "ragged thunderstorm": "11",
    "thunderstorm with light drizzle": "11",
    "thunderstorm with drizzle": "11",
    "thunderstorm with heavy drizzle": "11",
    "light rain": "10",
    "moderate rain": "10",
    "heavy intensity rain": "10",
    "very heavy rain": "10",
    "extreme rain": "10",
    "freezing rain": "13",
    "light intensity shower rain": "09",
    "shower rain": "09",
    "heavy intensity shower rain": "09",
    "ragged shower rain": "09",
    "light intensity drizzle": "09",
    "drizzle": "09",
    "heavy intensity drizzle": "09",
    "light intensity drizzle rain": "09",
    "drizzle rain": "09",
    "heavy intensity drizzle rain": "09",
    "shower rain and drizzle": "09",
    "heavy shower rain and drizzle": "09",
    "shower drizzle": "09",
    "light snow": "13",
    "snow": "13",
    "heavy snow": "13",
    "sleet": "13",
    "light shower sleet": "13",
    "shower sleet": "13",
    "light rain and snow": "13",
    "rain and snow": "13",
    "light shower snow": "13",
    "shower snow": "13",
    "heavy shower snow": "13",
    "mist": "50",
    "smoke": "50",
    "haze": "50",
    "sand/dust whirls": "50",
    "fog": "50",
    "sand": "50",
    "dust": "50",
    "ash": "50",
    "squalls": "50",
    "tornado": "50",
    "clear sky": "01",
    "few clouds": "02",
    "scattered clouds": "03",
    "broken clouds": "04",
    "overcast clouds": "04",
}


def strtime_to_ms(strtime: str) -> int:
    number = int(strtime[:-1])
    time_ind = strtime[-1]

    if time_ind not in TIME_IND_MULT:
        raise ValueError(f"Incorrect time format, got following string : {strtime}")

    return number * TIME_IND_MULT[time_ind]


def create_trend(
    influxdb_connector: InfluxDBConnector,
    measurement: str,
    field: str,
    refresh_rate: str,
    window_size: int,
    title: str = "",
) -> pn.indicators.Trend:
    df_init = influxdb_connector.query_field(measurement, field, window_size)
    nb_measures = df_init.shape[0]

    trend = pn.indicators.Trend(
        title=title,
        data=df_init,
        plot_x="_time",
        plot_y=field,
        sizing_mode="stretch_both",
        plot_type="area",
    )

    def update_plot():
        trend.stream(
            influxdb_connector.query_field(measurement, field, refresh_rate),
            rollover=nb_measures,
        )

    pn.state.add_periodic_callback(update_plot, strtime_to_ms(refresh_rate))

    return trend


# TODO Remove duplicate code between number and gauge


def create_number(
    influxdb_connector: InfluxDBConnector,
    measurement: str,
    field: str,
    refresh_rate: int,
    name: str = "",
    string_format: str = "{value:.1f}",
    thresholds: Dict = None,
    math_operation: callable = None,
):
    if thresholds is not None:
        thresholds = list(thresholds.items())

    mean_value = influxdb_connector.query_mean_field(measurement, field, refresh_rate)
    if math_operation is not None:
        mean_value = math_operation(mean_value)

    number = pn.indicators.Number(
        name=name,
        value=mean_value,
        format=string_format,
        sizing_mode="stretch_both",
        colors=thresholds,
    )

    def update_value():
        mean_value = influxdb_connector.query_mean_field(
            measurement, field, refresh_rate
        )
        if math_operation is not None:
            mean_value = math_operation(mean_value)

        number.value = mean_value

    pn.state.add_periodic_callback(update_value, strtime_to_ms(refresh_rate))

    return number


def create_gauge(
    influxdb_connector: InfluxDBConnector,
    measurement: str,
    field: str,
    refresh_rate: int,
    bounds: List,
    name: str = "",
    format_suffix: str = "",
    thresholds: Dict = None,
):
    if thresholds is not None:
        thresholds = list(thresholds.items())

    mean_value = influxdb_connector.query_mean_field(measurement, field, refresh_rate)

    gauge = pn.indicators.Gauge(
        name=name,
        value=int(mean_value),
        format="{value}" + format_suffix,
        bounds=tuple(bounds),
        sizing_mode="stretch_both",
        colors=thresholds,
    )

    def update_value():
        mean_value = influxdb_connector.query_mean_field(
            measurement, field, refresh_rate
        )
        gauge.value = int(mean_value)

    pn.state.add_periodic_callback(update_value, strtime_to_ms(refresh_rate))

    return gauge


def icon_url(weather_description: str) -> str:
    if weather_description not in MAPPING_ICON_ID:
        icon_id = "50"
    else:
        icon_id = MAPPING_ICON_ID[weather_description]

    current_hour = dt.datetime.now().hour
    if 7 < current_hour < 19:
        time_id = "d"
    else:
        time_id = "n"

    return f"https://openweathermap.org/img/wn/{icon_id}{time_id}@4x.png"


def create_weather_icon(
    influxdb_connector: InfluxDBConnector,
    measurement: str,
    field: str,
    refresh_rate: int,
):
    weather_description = influxdb_connector.query_last_field(measurement, field)

    pane_image = pn.pane.PNG(
        icon_url(weather_description),
        max_height=400,
        max_width=400,
        sizing_mode="stretch_both",
    )
    text_description = pn.widgets.StaticText(
        value=f"<h1>{weather_description}</h1>", align="center"
    )

    weather_icon = pn.Column(pane_image, text_description)

    def update_value():
        weather_description = influxdb_connector.query_last_field(measurement, field)

        pane_image.object = icon_url(weather_description)
        text_description.value = weather_description

    pn.state.add_periodic_callback(update_value, strtime_to_ms(refresh_rate))

    return weather_icon
