#!/usr/bin/env python
# coding: utf-8

from dask.distributed import Client
from glob import glob
import dask.dataframe as dd
import json
import numpy as np
import os
import os.path


csv_schema = """trip_duration,start_time,stop_time,start_station_id,
start_station_name,start_station_latitude,start_station_longitude,
end_station_id,end_station_name,end_station_latitude,
end_station_longitude,bike_id,user_type,birth_year,gender""".split(',')
csv_schema = [x.strip() for x in csv_schema]

dtype_list = {
    'trip_duration':                     np.int32,
    'start_station_id':                  np.int32,
    'start_station_name':                object,
    'start_station_latitude':            np.float32,
    'start_station_longitude':           np.float32,
    'end_station_id':                    np.int32,
    'end_station_name':                  object,
    'end_station_latitude':              np.float32,
    'end_station_longitude':             np.float32,
    'bike_id':                           np.int32,
    'user_type':                         object,
    'birth_year':                        np.float32,
    'gender':                            np.int32,
}

with open('config.json', 'r') as fh:
    config = json.load(fh)


def main(client):
    df = dd.read_csv(
        sorted(
            glob(os.path.join(config["citibike_raw_data_path"],
                              '2*iti*.csv'))),
        parse_dates=[1, 2, ],
        infer_datetime_format=True,
        na_values=["\\N"],
        header=0,
        names=csv_schema,
        dtype=dtype_list
    )


    for fieldName in csv_schema:
        if fieldName in dtype_list:
            df[fieldName] = df[fieldName].astype(dtype_list[fieldName])

    df['start_time'] = df.start_time.astype(str)
    df['stop_time'] = df.stop_time.astype(str)

    df['start_station_name'] = df.start_station_name.str.strip('"')
    df['end_station_name'] = df.end_station_name.str.strip('"')

    df.to_parquet(
        os.path.join(config['parquet_output_path'], 'citibike.parquet'),
        compression="GZIP", object_encoding='json')

    df = dd.read_parquet(os.path.join(
        config['parquet_output_path'], 'citibike.parquet'))

    df.to_csv(
        os.path.join(config["parquet_output_path"], 'csv/citibike-*.csv.gz'), 
        index=False,
        name_function=lambda l: '{0:04d}'.format(l),
        compression='gzip'
        )



if __name__ == '__main__':
    client = Client()
    main(client)
