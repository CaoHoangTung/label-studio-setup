"""
Process mov file and write to mp4 file
"""
import os

from moviepy.video.io.VideoFileClip import VideoFileClip
from openmovement.load import CwaData

from env import env_config


def process_mov(mov_file: str, mp4_path: str, start_second: float = None, end_second: float = None):
    video = VideoFileClip(mov_file)
    if start_second and end_second:
        video = video.subclip(start_second, end_second)
    video.write_videofile(mp4_path, codec='libx264')
    video.close()


"""
Read data from cwa path, output result to csv path wrt the filtered date from request
"""


def process_csv(cwa_path, csv_path, start_index, end_index):
    with CwaData(cwa_path, include_gyro=False, include_temperature=True) as cwa_data:  # Convert cwa format into ndarray
        # As a pandas DataFrame
        samples = cwa_data.get_samples()
        sensor_data = cwa_data.get_sample_values()

        record_start_time = samples['time'][0]

        filtered_samples = samples.iloc[start_index:end_index + 1]
        if len(filtered_samples) == 0:
            raise Exception("Duration too short")

        selected_start_datetime = str(filtered_samples.head(1).time.tolist()[0]).replace(' ', '_').replace('-',
                                                                                                           '_').replace(
            ':', '_')
        selected_end_datetime = str(filtered_samples.tail(1).time.tolist()[0]).replace(' ', '_').replace('-',
                                                                                                         '_').replace(
            ':', '_')

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
        return selected_start_datetime, selected_end_datetime


# Write content to import file
"""
import_filename: name of import file
csv_path: path to filtered csv data of sensor 1
csv_path_2: path to filtered csv data of sensor 2
mp4_filename: name of the mp4 file
sensor: sensor name
"""


def create_import_file(import_filename, csv_path, csv_path_2, csv_filename, mp4_filename, sensor="unknown"):
    with open("../static/import_template.json") as f_template:
        template_content = f_template.read()

        import_content = template_content.replace('[[csv_filename]]', csv_filename). \
            replace('[[mp4_filename]]', mp4_filename). \
            replace('[[csv_path]]', csv_path.replace('\\', '\\\\')). \
            replace('[[csv_path_2]]', csv_path_2.replace('\\', '\\\\')). \
            replace('[[sensor]]', str(sensor))
        with open(os.path.join(env_config['DOWNLOAD_FOLDER'], import_filename), 'w') as file:
            file.write(import_content)


def append_datetime_prefix(filename, start_date, start_time, end_date, end_time):
    start_time = start_time.replace(':', '-')
    end_time = end_time.replace(':', '-')
    return f'{start_date}-{start_time}_{end_date}-{end_time}_{filename}'
