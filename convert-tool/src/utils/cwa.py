'''
Find cwa_file and mov_file from a list of file
'''
import functools
import os
import pathlib
from dataclasses import dataclass

import pandas as pd
from openmovement.load import CwaData

from env import env_config, FIRST_SENSOR_PREFIX, SECOND_SENSOR_PREFIX
from utils.paths import get_dataset_upload_dir


@dataclass
class CwaDataType:
    samples: pd.DataFrame
    time_min: int
    time_max: int


@functools.lru_cache(maxsize=16)
def get_cwa_data_from_file(cwa_file) -> CwaDataType:
    with CwaData(cwa_file, include_gyro=False, include_temperature=True) as cwa_data:
        samples = cwa_data.get_samples()
        return CwaDataType(
            samples=samples,
            time_min=samples['time'].min(),
            time_max=samples['time'].max()
        )


def find_file_in_dataset(dataset_id: str):
    cwa_file_1, cwa_file_2, mp4_file = None, None, None

    dataset_path = get_dataset_upload_dir(dataset_id)
    if not os.path.exists(dataset_path):
        return None, None, None
    file_list = os.listdir(dataset_path)

    for file in file_list:
        file_path = os.path.join(dataset_path, file)
        extension = pathlib.Path(file_path).suffix.lower()
        if extension == '.cwa':
            if file.startswith(FIRST_SENSOR_PREFIX):
                cwa_file_1 = file_path
            elif file.startswith(SECOND_SENSOR_PREFIX):
                cwa_file_2 = file_path
        elif extension == '.mp4':
            mp4_file = file_path
    return cwa_file_1, cwa_file_2, mp4_file
