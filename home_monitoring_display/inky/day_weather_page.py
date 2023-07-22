


class DayWeatherPage(InkyPage):
    def __init__(
        self,
        inky_display: InkyPHAT,
        influxdb_connectors: Dict[str, InfluxDBConnector],
        font: str,
        refresh_period: int,
        cities: List[str],
    ) -> None:
        self.fields_configuration = fields_configuration
        super().__init__(inky_display, influxdb_connectors, font, refresh_period)

    def get_data(self) -> Dict:
        data = {}