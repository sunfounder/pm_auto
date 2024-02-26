from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
import json
import logging

class Database:
    def __init__(self, database, log=None):
        if log is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = log
        try:
            self.client = InfluxDBClient(host='localhost', port=8086)
        except Exception as e:
            self.log.error(f"Failed to connect to influxdb: {e}")
            return
        self.database = database

        databases = self.client.get_list_database()
        if not any(db['name'] == self.database for db in databases):
            self.client.create_database(self.database)
            log(f"Database '{database}' not exit, created successfully")

        self.client.switch_database(self.database)

    def set(self, measurement, data):
        json_body = [
            {
                "measurement": measurement,
                "fields": data
            }
        ]
        try:
            self.client.write_points(json_body)
            return True, json_body
        except InfluxDBClientError as e:
            return False, json.loads(e.content)["error"]
        except Exception as e:
            return False, str(e)

    def get_data_by_time_range(self, measurement, start_time, end_time, key="*"):
        query = f"SELECT {key} FROM {measurement} WHERE time >= {start_time} AND time <= {end_time}"
        print(query)
        result = self.client.query(query)
        return list(result.get_points())

    def if_too_many_nulls(self, result, threshold=0.3):
        for point in result:
            error_length = len([key for key, value in point.items() if value is None])
            error_ratio = error_length / len(point)
            if error_ratio > threshold:
                return True
        return False

    def get(self, measurement, key="*", n=1):
        for _ in range(3):
            query = f"SELECT {key} FROM {measurement} ORDER BY time DESC LIMIT {n}"
            result = self.client.query(query)
            if self.if_too_many_nulls(list(result.get_points())):
                self.log.warning(f"Too many nulls in the result of query: {query}, trying again...")
                continue
            break
        else:
            return None
        if n == 1:
            if len(list(result.get_points())) == 0:
                return None
            if key != "*" and key != "time" and "," not in key:
                return list(result.get_points())[0][key]
            return list(result.get_points())[0]
        
        return list(result.get_points())

    def close_connection(self):
        self.client.close()
