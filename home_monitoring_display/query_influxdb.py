from typing import Dict
import re
import logging
import datetime as dt

import pytz
from influxdb import DataFrameClient
import pandas as pd


class InfluxDBConnector:
    def __init__(
        self,
        database: str,
        username: str,
        password: str,
        host: str = "localhost",
        port: int = 8086,
        timeout: int = 20_000,
        timezone: str = "Europe/Paris",
        default_group_measurement: Dict = None,
        # logger=logging,
    ) -> None:
        self.database = database
        self.username = username
        self.password = password
        self.timeout = timeout
        self.timezone = timezone

        self.host = host
        self.port = port

        self.client = None

        self.default_group_measurement = default_group_measurement
        # self.logger = logger

    @staticmethod
    def convert_time_cond(time_cond):
        if isinstance(time_cond, dt.datetime):
            time_utc = dt.datetime.utcfromtimestamp(time_cond.timestamp())
            return f"'{time_utc.isoformat()}Z'"
        elif isinstance(time_cond, str):
            if time_cond == "now()":
                return time_cond
            elif bool(re.fullmatch(r"^\d{1,3}[a-zA-Z]$", time_cond)):
                return f"now() - {time_cond}"

        raise ValueError(
            f"""Invalid time condition: {time_cond}.
                Should either be <1-3 number><letter> or be datetime."""
        )

    def _connect(self) -> None:
        if self.client is None:
            self.client = DataFrameClient(
                self.host,
                self.port,
                self.username,
                self.password,
                database=self.database,
                timeout=self.timeout,
            )

    def get_schema(self):
        self._connect()

        query_fields = f"SHOW FIELD KEYS"
        fields_database = self.client.query(query_fields)

        schema = {}
        for measurement, fields_meas in fields_database.items():
            fields = {
                field_dict["fieldKey"]: field_dict["fieldType"]
                for field_dict in fields_meas
            }
            first_field = list(fields.keys())[0]

            query_first = f"SELECT first({first_field}) FROM {measurement[0]}"
            query_last = f"SELECT last({first_field}) FROM {measurement[0]}"

            schema[measurement[0]] = {
                "fields": fields,
                "first_date": (
                    self.client.query(query_first)[measurement[0]]
                    .index[0]
                    .tz_convert(pytz.timezone(self.timezone))
                ),
                "last_date": (
                    self.client.query(query_last)[measurement[0]]
                    .index[0]
                    .tz_convert(pytz.timezone(self.timezone))
                ),
            }

        return schema

    def query_field(
        self,
        measurement: str,
        field: str,
        start: str,
        stop: str = "now()",
        groupby_interval: str = None,
        aggregation_func: str = "mean"
    ) -> pd.DataFrame:
        self._connect()

        if (
            groupby_interval is None
            and self.default_group_measurement is not None
            and measurement in self.default_group_measurement
        ):
            groupby_interval = self.default_group_measurement[measurement]

        if groupby_interval is None:
            query = f"""SELECT {field}
                        FROM {measurement}
                        WHERE time > {self.convert_time_cond(start)}
                        AND time < {self.convert_time_cond(stop)}"""
        else:
            query = f"""SELECT {aggregation_func}({field}) as {field}
                        FROM {measurement}
                        WHERE time > {self.convert_time_cond(start)}
                        AND time < {self.convert_time_cond(stop)}
                        GROUP BY time({groupby_interval}) FILL(null)"""

        query_result = self.client.query(query)

        if len(query_result) == 0:
            return None

        df_query = query_result[measurement]

        df_query = df_query.reset_index(names=["_time"])
        df_query._time = df_query._time.dt.tz_convert(tz=pytz.timezone(self.timezone))

        return df_query

    def query_mean_field(
        self, measurement: str, field: str, start: str, stop: str = "now()"
    ) -> pd.DataFrame:
        self._connect()

        query = f"""SELECT mean({field}) as {field}
                    FROM {measurement}
                    WHERE time > {self.convert_time_cond(start)}
                    AND time < {self.convert_time_cond(stop)}"""
                    
        df_mean_query = self.client.query(query)[measurement]
        return df_mean_query.iloc[0][field]

    def query_last_field(
        self, measurement, field: str,
    ):
        self._connect()
        
        query_last = f"""SELECT last({field}) as {field}
                FROM {measurement}"""
                
        df_query_last = self.client.query(query_last)[measurement]
        
        return df_query_last.iloc[0][field]