from typing import List

import pandas as pd
import pytz

import logging


class MultiViewConnector:
    def __init__(self, **influxdb_connectors):
        self.influxdb_connectors = influxdb_connectors

        self.schema = dict()
        for connector_name, connector in self.influxdb_connectors.items():
            connector_schema = connector.get_schema()
            for measurement, measurement_schema in connector_schema.items():
                self.schema[(connector_name, measurement)] = measurement_schema

        self.timezone = pytz.timezone(
            list(self.influxdb_connectors.values())[0].timezone
        )
        self._cached_queries = {}

    def get_first_date(self):
        return min(
            *[
                measurement_schema["first_date"]
                for measurement_schema in self.schema.values()
            ]
        )

    def get_last_date(self):
        return max(
            *[
                measurement_schema["last_date"]
                for measurement_schema in self.schema.values()
            ]
        )

    def query_measure(
        self, connector_name: str, measurement: str, field: str, start: str, stop: str
    ) -> pd.DataFrame:
        start = start.replace(tzinfo=self.timezone)
        stop = stop.replace(tzinfo=self.timezone)

        influxdb_connector = self.influxdb_connectors[connector_name]

        if connector_name not in self._cached_queries:
            self._cached_queries[connector_name] = dict()

        if measurement not in self._cached_queries[connector_name]:
            self._cached_queries[connector_name][measurement] = dict()

        if field not in self._cached_queries[connector_name][measurement]:
            # Retrieve data from influxdb
            df_query = influxdb_connector.query_field(
                measurement, field, start, stop=stop
            )
            # start and stop must be local time timezone unaware datetime

            field_cache = {"cache": df_query, "start": start, "stop": stop}

            self._cached_queries[connector_name][measurement][field] = field_cache
            return df_query
        else:
            # Retrieve data from cache
            field_cache = self._cached_queries[connector_name][measurement][field]

            cached_start = field_cache["start"]
            cached_stop = field_cache["stop"]

            # Query missing data
            if start < cached_start:
                field_cache["cache"] = pd.concat(
                    [
                        influxdb_connector.query_field(
                            measurement, field, start, stop=cached_start
                        ),
                        field_cache["cache"],
                    ],
                    ignore_index=True,
                )

                field_cache["start"] = start

            if stop > cached_stop:
                field_cache["cache"] = pd.concat(
                    [
                        field_cache["cache"],
                        influxdb_connector.query_field(
                            measurement, field, cached_stop, stop=stop
                        ),
                    ],
                    ignore_index=True,
                )

                field_cache["stop"] = stop

            df_cache = field_cache["cache"]

            return df_cache[(df_cache["_time"] >= start) & (df_cache["_time"] <= stop)]
