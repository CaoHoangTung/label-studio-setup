"""
Process mov file and write to mp4 file
"""
import json
import os

import pandas as pd
from flask import render_template
from moviepy.video.io.VideoFileClip import VideoFileClip
from openmovement.load import CwaData

from utils.Extraction import ExtractData


def process_video(input_file: str, output_file: str, start_second: float = None, end_second: float = None):
    video = VideoFileClip(input_file)
    if start_second and end_second:
        video = video.subclip(start_second, end_second)
    video.write_videofile(output_file, codec='libx264')
    video.close()


"""
Read data from cwa path, output result to csv path wrt the filtered date from request
"""


def trim_cwa_file_and_export_csv(cwa_path, csv_path, start_index, end_index):
    with CwaData(cwa_path, include_gyro=False, include_temperature=True) as cwa_data:  # Convert cwa format into ndarray
        # As a pandas DataFrame
        samples = cwa_data.get_samples()
        sensor_data = cwa_data.get_sample_values()

        record_start_time = samples['time'][0]

        filtered_samples = samples.iloc[start_index:end_index + 1]
        if len(filtered_samples) == 0:
            raise Exception("Duration too short")

        selected_start_datetime = str(filtered_samples.head(1).time.tolist()[0]) \
            .replace(' ', '_') \
            .replace('-', '_') \
            .replace(':', '_')
        selected_end_datetime = str(filtered_samples.tail(1).time.tolist()[0]) \
            .replace(' ', '_') \
            .replace('-', '_') \
            .replace(':', '_')

        # Get number of days captured in an integer
        participant_id = "sample_participant"
        participant_id = participant_id.split('.')[0]  # --> Remove any extension
        # Get time
        starting_hour = int(record_start_time.strftime("%H")) + int(record_start_time.strftime("%M")) / 60

        selected_sensor_data = sensor_data[start_index:end_index + 1, 0:4]

        AX3_application, AX3Data, AX3Data_Bandpass, sleep_period_time_hr, bedtime, NWT_hr = ExtractData(
            selected_sensor_data, 1, participant_id, starting_hour)

        result = pd.DataFrame()

        ax3_value_size = AX3Data.shape[-1]
        for i in range(ax3_value_size):
            result[f'ax3_{i}'] = AX3Data[:, i]

        result['ax3_bandpass'] = list(AX3Data_Bandpass)
        result['original_index'] = [i for i in range(len(AX3Data))]

        result.to_csv(csv_path, index=True, index_label='index')
        return csv_path, cwa_data.get_sample_rate()

    # Write content to import file


"""
import_filename: name of import file
csv_path: path to filtered csv data of sensor 1
csv_path_2: path to filtered csv data of sensor 2
mp4_filename: name of the mp4 file
sensor: sensor name
"""

video_script = ""


def create_import_file(
        dataset_id, match_id,
        import_file_path,
        sample_rate1, sample_rate2,
        csv_path1, csv_path2,
        sensor="unknown",
):
    import_data = render_template(
        "import_template.json",
        sensor=str(sensor),
        dataset_id=dataset_id,
        sample_rate1=sample_rate1,
        sample_rate2=sample_rate2,
        match_id=match_id,
        csv_path1=csv_path1,
        csv_path2=csv_path2,
    )


    with open(import_file_path, 'w') as file:
        print(import_data, file=file)
    return import_file_path


def append_datetime_prefix(filename, start_date, start_time, end_date, end_time):
    start_time = start_time.replace(':', '-')
    end_time = end_time.replace(':', '-')
    return f'{start_date}-{start_time}_{end_date}-{end_time}_{filename}'
