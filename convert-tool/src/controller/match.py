import json
import os
import time

from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import NotFound

from ls_client import LSSegmentMatchProject
from env import FIRST_SENSOR_PREFIX, SECOND_SENSOR_PREFIX
from utils.cwa import get_cwa_data_from_file
from utils.dataset import delete_and_recreate_dir, get_file_name_from_path
from utils.paths import get_dataset_upload_dir, get_match_dir, get_dataset_processed_dir, \
    find_file_in_dataset
from controller.match_utils import process_video, trim_cwa_file_and_export_csv, create_import_file


def process_dataset_upload(dataset_id: str, cwa_file1: FileStorage, cwa_file2: FileStorage, mov_file: FileStorage):
    # Delete and recreate the upload folder
    upload_dir = get_dataset_upload_dir(dataset_id)
    processed_dir = get_dataset_processed_dir(dataset_id)

    delete_and_recreate_dir(upload_dir)
    delete_and_recreate_dir(processed_dir)

    # Save the file to the upload folder
    mov_path = os.path.join(upload_dir, mov_file.filename)
    mov_file.save(mov_path)

    # Convert to mp4
    mp4_path = os.path.join(processed_dir, f'converted.mp4')
    process_video(input_file=mov_path, output_file=mp4_path)

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

    cwa_file_json_path = os.path.join(processed_dir, 'sensor.json')
    with open(cwa_file_json_path, "w") as file:
        json.dump(sensor_data, file)

    return dataset_id


def process_match_file(dataset_id, video_start: float, video_end: float,
                       sensor1_start: int, sensor1_end: int,
                       sensor2_start: int, sensor2_end: int):
    cwa_file1, cwa_file2, mp4_file = find_file_in_dataset(dataset_id)
    if cwa_file1 is None or cwa_file2 is None or mp4_file is None:
        raise NotFound(f"Can't find the dataset {dataset_id} or its files")

    print(video_start, video_end, sensor1_start, sensor1_end, sensor2_start, sensor2_end)

    match_id = str(int(time.time()))
    download_dir = get_match_dir(dataset_id, match_id)
    delete_and_recreate_dir(download_dir)

    output_mp4_path = os.path.join(download_dir, "video.mp4")
    csv_path1 = os.path.join(download_dir, "sensor1.csv")
    csv_path2 = os.path.join(download_dir, "sensor2.csv")

    process_video(mp4_file, output_mp4_path, video_start, video_end)

    csv_path1, sample_rate1 = trim_cwa_file_and_export_csv(
        cwa_file1, csv_path1,
        sensor1_start, sensor1_end
    )
    csv_path2, sample_rate2 = trim_cwa_file_and_export_csv(
        cwa_file2, csv_path2,
        sensor2_start, sensor2_end
    )

    import_file = os.path.join(download_dir, f'import.json')

    # Setting default offset=0. The index would be the index of the csv bandpass file
    import_file_path = create_import_file(
        dataset_id=dataset_id,
        match_id=match_id,
        import_file_path=import_file,
        sample_rate1=sample_rate1,
        sample_rate2=sample_rate2,
        sensor=1,
        csv_path1=csv_path1,
        csv_path2=csv_path2,
    )
    LSSegmentMatchProject.import_tasks(import_file_path)

    return match_id
