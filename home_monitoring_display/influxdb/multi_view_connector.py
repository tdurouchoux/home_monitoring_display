from typing import List

import pandas as pd
import pytz

import logging

class MultiViewConnector:
    def __init__(self, *influxdb_connector_list):
        self.influxdb_connector_list = influxdb_connector_list

        self.measurements_connector = {}
        self.schema = {}

        for connector in self.influxdb_connector_list:
            connector_schema = connector.get_schema()
            self.schema = dict(self.schema, **connector_schema)
            for measurement in connector_schema:
                self.measurements_connector[measurement] = connector

        self.timezone = pytz.timezone(self.influxdb_connector_list[0].timezone)
        self._cached_queries = {}

    def get_measure_options(self, select_types: List[str] = None) -> List[str]:
        if select_types is None:
            measure_options = [
                " | ".join([measurement, field])
                for measurement in self.schema
                for field in self.schema[measurement]["fields"]
            ]
        else:
            measure_options = [
                " | ".join([measurement, field])
                for measurement in self.schema
                for field, field_type in self.schema[measurement]["fields"].items()
                if field_type in select_types
            ]

        return measure_options

    def query_measure(self, measurement, field, start, stop):
        start = start.replace(tzinfo=self.timezone)
        stop = stop.replace(tzinfo=self.timezone)
        
        
        influxdb_connector = self.measurements_connector[measurement]

        if measurement not in self._cached_queries:
            self._cached_queries[measurement] = dict()

        if field not in self._cached_queries[measurement]:
            df_query = influxdb_connector.query_field(
                measurement, field, start, stop=stop
            )
            # start and stop must be local time timezone unaware datetime

            field_cache = {"cache": df_query, "start": start, "stop": stop}

            self._cached_queries[measurement][field] = field_cache
            return df_query
        else:
            field_cache = self._cached_queries[measurement][field]

            cached_start = field_cache["start"]
            cached_stop = field_cache["stop"]

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
