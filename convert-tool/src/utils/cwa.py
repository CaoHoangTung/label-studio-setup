'''
Find cwa_file and mov_file from a list of file
'''
import functools
from dataclasses import dataclass

import pandas as pd
from openmovement.load import CwaData


@dataclass
class CwaDataType:
    samples: pd.DataFrame
    time_min: int
    time_max: int
    sample_rate: float


@functools.lru_cache(maxsize=16)
def get_cwa_data_from_file(cwa_file) -> CwaDataType:
    with CwaData(cwa_file, include_gyro=False, include_temperature=True) as cwa_data:
        samples = cwa_data.get_samples()
        return CwaDataType(
            samples=samples,
            time_min=samples['time'].min(),
            time_max=samples['time'].max(),
            sample_rate=cwa_data.get_sample_rate()
        )
