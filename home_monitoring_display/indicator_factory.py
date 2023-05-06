from typing import Dict, List

import panel as pn

from home_monitoring_display.query_influxdb import InfluxDBConnector

TIME_IND_MULT = {
    "w": 7 * 24 * 60 * 60 * 1000,
    "d": 24 * 60 * 60 * 1000,
    "h": 60 * 60 * 1000,
    "m": 60 * 1000,
    "s": 1000,
}


def strtime_to_ms(strtime: str) -> int:
    number = int(strtime[:-1])
    time_ind = strtime[-1]

    if time_ind not in TIME_IND_MULT:
        raise ValueError(f"Incorrect time format, got following string : {strtime}")

    return number * TIME_IND_MULT[time_ind]


class IndicatorFactory:
    def __init__(self, window_size: str = "10m") -> None:
        self.window_size = window_size

    def create_trend(
        self,
        influxdb_connector: InfluxDBConnector,
        measurement: str,
        field: str,
        refresh_rate: str,
        title: str = "",
    ) -> pn.indicators.Trend:
        df_init = influxdb_connector.query_field(measurement, field, self.window_size)
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
        self,
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

        mean_value = influxdb_connector.query_mean_field(
            measurement, field, refresh_rate
        )
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
        self,
        influxdb_connector: InfluxDBConnector,
        measurement: str,
        field: str,
        refresh_rate: int,
        bounds: List,
        name: str = "",
        format_suffix: str = "",
        thresholds: Dict = None):

        if thresholds is not None:
            thresholds = list(thresholds.items())
            
        mean_value = influxdb_connector.query_mean_field(
            measurement, field, refresh_rate
        )

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