import json
import os
import time

from werkzeug.datastructures import FileStorage

from env import env_config, FIRST_SENSOR_PREFIX, SECOND_SENSOR_PREFIX
from utils.cwa import get_cwa_data_from_file
from utils.dataset import delete_and_recreate_dir
from utils.paths import get_dataset_upload_dir, get_dataset_download_dir
from utils.process import process_mov


def process_dataset_files(dataset_id: str, cwa_file1: FileStorage, cwa_file2: FileStorage, mov_file: FileStorage):
    # Delete and recreate the upload folder
    upload_dir = get_dataset_upload_dir(dataset_id)
    delete_and_recreate_dir(upload_dir)

    # Save the file to the upload folder
    mov_path = os.path.join(upload_dir, mov_file.filename)
    mov_file.save(mov_path)

    # Convert to mp4
    mp4_path = os.path.join(upload_dir, 'converted.mp4')
    process_mov(mov_path, mp4_path)

    # Save signal files
    cwa_file1_path = os.path.join(upload_dir, f'{FIRST_SENSOR_PREFIX}{cwa_file1.filename}')
    cwa_file1.save(cwa_file1_path)
    cwa_file2_path = os.path.join(upload_dir, f'{SECOND_SENSOR_PREFIX}{cwa_file2.filename}')
    cwa_file2.save(cwa_file2_path)

    cwa_data_1 = get_cwa_data_from_file(cwa_file1_path).samples
    cwa_data_2 = get_cwa_data_from_file(cwa_file2_path).samples

    sensor_data = {
        'sensor1': {
            "x": cwa_data_1['accel_x'].tolist(),
            "y": cwa_data_1['accel_y'].tolist(),
            "z": cwa_data_1['accel_z'].tolist(),
            "time": cwa_data_1['time'].astype(str).tolist(),
            "size": cwa_data_1.shape[0]
        },
        'sensor2': {
            "x": cwa_data_2['accel_x'].tolist(),
            "y": cwa_data_2['accel_y'].tolist(),
            "z": cwa_data_2['accel_z'].tolist(),
            "time": cwa_data_2['time'].astype(str).tolist(),
            "size": cwa_data_2.shape[0]
        }
    }

    cwa_file_json_path = os.path.join(upload_dir, 'sensor.json')
    with open(cwa_file_json_path, "w") as file:
        json.dump(sensor_data, file)

    return dataset_id

# def process_sensor_data(sensor1_data: dict, sensor2_data: dict) -> dict:
