import bisect
import json
import math
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from moviepy.editor import VideoFileClip
from openmovement.load import CwaData
import shutil
import pathlib
from utils.Extraction import ExtractData

app = Flask(__name__)

# Set the path for storing uploaded files
UPLOAD_FOLDER = 'uploads/'
DOWNLOAD_FOLDER = 'downloads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['STORAGE_FOLDER'] = os.environ.get('STORAGE_FOLDER', 'C:\\Users\\ADMIN\\label-studio\\data\\storage')

STORAGE_INPUT_FOLDER = os.path.join(app.config['STORAGE_FOLDER'], "input")

FIRST_SENSOR_PREFIX = 'sensor1_'
SECOND_SENSOR_PREFIX = 'sensor2_'

print('app.config', app.config)

'''
Find cwa_file and mov_file from a list of file
'''
def find_file(file_list):
    cwa_file_1, cwa_file_2, mov_file = None, None, None

    for file in file_list:
        if pathlib.Path(file).suffix.lower() == '.cwa':
            if file.startswith(FIRST_SENSOR_PREFIX):
                cwa_file_1 =  os.path.join(app.config['UPLOAD_FOLDER'], file)
            elif file.startswith(SECOND_SENSOR_PREFIX):
                cwa_file_2 = os.path.join(app.config['UPLOAD_FOLDER'], file)
        elif pathlib.Path(file).suffix.lower() == '.mov':
            mov_file = os.path.join(app.config['UPLOAD_FOLDER'], file)
    return cwa_file_1, cwa_file_2, mov_file

def delete_and_recreate_dir(path):
    # Delete the folder together with all the files
    if os.path.exists(path):
        shutil.rmtree(path)
    # Recreate the folder
    os.makedirs(path)

# Get file name without extension. Example: a/b/c.txt -> c
def get_file_name_from_path(path):
    return os.path.splitext(os.path.split(path)[1])[0]

# Get folder path from full path. Example: a/b/c.txt -> a/b
def get_folder_from_path(path):
    return os.path.split(path)[0]

@app.route('/')
def index(message: str = ''):
    print('message', message)
    return render_template('index.html', message=message)


@app.route('/', methods=['POST'])
def upload_file():
    # Check if a file is uploaded
    if 'file_mov' not in request.files or 'file_cwa_1' not in request.files or 'file_cwa_2' not in request.files:
        return redirect(request.url)
    
    file_mov = request.files['file_mov']
    file_cwa_1 = request.files['file_cwa_1']
    file_cwa_2 = request.files['file_cwa_2']
    
    # Check if the file is selected
    print('file_mov', file_mov.filename)
    print('file_cwa_1', file_cwa_1.filename)
    print('file_cwa_2', file_cwa_2.filename)

    # Delete and recreate the upload folder
    delete_and_recreate_dir(app.config['UPLOAD_FOLDER'])

    # Delete and recreate the download folder
    delete_and_recreate_dir(app.config['DOWNLOAD_FOLDER'])

    # Save the file to the upload folder
    file_mov.save(os.path.join(app.config['UPLOAD_FOLDER'], file_mov.filename))
    file_cwa_1.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{FIRST_SENSOR_PREFIX}{file_cwa_1.filename}"))
    file_cwa_2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{SECOND_SENSOR_PREFIX}{file_cwa_2.filename}"))
    return redirect(url_for('list_upload'))

    
@app.route('/download/<filename>')
def download_file(filename):
    from_directory = request.args.get('from_directory', app.config['DOWNLOAD_FOLDER'])
    return send_from_directory(from_directory, filename, as_attachment=True)

@app.route('/delete-downloads')
def delete_download_files():
    files = os.listdir(app.config['DOWNLOAD_FOLDER'])
    for file in files:
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], file)
        os.remove(file_path)
    
    return redirect(url_for('list_download'))

@app.route('/delete-uploads')
def delete_upload_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    for file in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
        os.remove(file_path)
    
    return redirect(url_for('list_upload'))

@app.route('/final-instruction')
def final_instruction():
    files = os.listdir(app.config['DOWNLOAD_FOLDER'])
    return render_template('final_instruction.html', files=files)


# Get time_min and time_max from samples, read from cwa file
def get_time_range_from_cwa_file(cwa_file):
    with CwaData(cwa_file, include_gyro=False, include_temperature=True) as cwa_data:
        samples = cwa_data.get_samples()
        time_min, time_max = (samples['time'].min(), samples['time'].max())
        return time_min, time_max

def get_cwa_data_from_file(cwa_file):
    with CwaData(cwa_file, include_gyro=False, include_temperature=True) as cwa_data:
        samples = cwa_data.get_samples()
        return samples

@app.route('/list-upload')
def list_upload():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    cwa_file_1, cwa_file_2, mov_file = find_file(files)

    if cwa_file_1 is None or cwa_file_2 is None or mov_file is None:
        return render_template('list_upload.html', files=files, message='Cannot find cwa and mov file. Please go back to home page and try again')

    time_min_1, time_max_1 = get_time_range_from_cwa_file(cwa_file_1)
    time_min_2, time_max_2 = get_time_range_from_cwa_file(cwa_file_2)

    cwa_data_1 = get_cwa_data_from_file(cwa_file_1)
    cwa_data_2 = get_cwa_data_from_file(cwa_file_2)

    return render_template(
        'list_upload.html', 
        mov_filename=os.path.basename(mov_file),
        sensor1_data=cwa_data_1,
        sensor2_data=cwa_data_2,
        date_range_1=[
            {
                'time': time_min_1.strftime('%H:%M:%S'),
                'date': time_min_1.strftime('%Y-%m-%d')
            },
            {
                'time': time_max_1.strftime('%H:%M:%S'),
                'date': time_max_1.strftime('%Y-%m-%d')
            }
        ],
        date_range_2=[
            {
                'time': time_min_2.strftime('%H:%M:%S'),
                'date': time_min_2.strftime('%Y-%m-%d')
            },
            {
                'time': time_max_2.strftime('%H:%M:%S'),
                'date': time_max_2.strftime('%Y-%m-%d')
            }
        ]
    )

"""
Process mov file and write to mp4 file
"""
def process_mov(mov_file: str, mp4_path: str, start_second: float, end_second: float):
    video = VideoFileClip(mov_file).subclip(start_second, end_second)
    video.write_videofile(mp4_path, codec='libx264')
    video.close()

"""
Read data from cwa path, output result to csv path wrt the filtered date from request
"""
def process_csv(cwa_path, csv_path, start_index, end_index):
    with CwaData(cwa_path, include_gyro=False, include_temperature=True) as cwa_data: #Convert cwa format into ndarray
        # As a pandas DataFrame
        samples = cwa_data.get_samples()
        sensor_data = cwa_data.get_sample_values()

        record_start_time=samples['time'][0]

        filtered_samples = samples.iloc[start_index:end_index+1]

        if filtered_samples.shape[0] == 0:
            return "Invalid time. Please try again"

        #Get number of days captured in an integer
        participant_id = "sample_participant"
        participant_id = participant_id.split('.')[0]  #--> Remove any extension
        #Get time
        starting_hour = int(record_start_time.strftime("%H"))+int(record_start_time.strftime("%M"))/60

        selected_sensor_data = sensor_data[start_index:end_index+1,0:4]

        AX3_application, AX3Data, AX3Data_Bandpass, sleep_period_time_hr, bedtime, NWT_hr = ExtractData(selected_sensor_data, 1,participant_id,starting_hour) 

        result = pd.DataFrame()

        ax3_value_size = AX3Data.shape[-1]
        for i in range(ax3_value_size):
            result[f'ax3_{i}'] = AX3Data[:,i]

        result['ax3_bandpass'] = list(AX3Data_Bandpass)
        result['original_index'] = [i for i in range(len(AX3Data))]

        result.to_csv(csv_path, index=True, index_label='index')
    
# Write content to import file
"""
import_filename: name of import file
csv_path: path to filtered csv data of sensor 1
csv_path_2: path to filtered csv data of sensor 2
mp4_filename: name of the mp4 file
sensor: sensor name
"""
def create_import_file(import_filename, csv_path, csv_path_2, csv_filename, mp4_filename, sensor="unknown"):
    with open("./static/import_template.json") as f_template:
        template_content = f_template.read()
        import_content = template_content.replace('[[csv_filename]]', csv_filename).\
                        replace('[[mp4_filename]]', mp4_filename).\
                        replace('[[csv_path]]', csv_path.replace('\\', '\\\\')).\
                        replace('[[csv_path_2]]', csv_path_2.replace('\\', '\\\\')).\
                        replace('[[sensor]]', str(sensor))
        with open(os.path.join(app.config['DOWNLOAD_FOLDER'], import_filename), 'w') as fout:
            fout.write(import_content)

def append_datetime_prefix(filename, start_date, start_time, end_date, end_time):
    start_time = start_time.replace(':', '-')
    end_time = end_time.replace(':', '-')
    return f'{start_date}-{start_time}_{end_date}-{end_time}_{filename}'

# Process to create import file
@app.route('/import', methods=['POST'])
def import_label_studio():
    files = os.listdir(app.config['UPLOAD_FOLDER'])

    cwa_file_1, cwa_file_2, mov_file = find_file(files)

    mp4_filename = get_file_name_from_path(mov_file) + '.mp4'
    csv_filename_1 = get_file_name_from_path(cwa_file_1) + '.csv'
    csv_filename_2 = get_file_name_from_path(cwa_file_2) + '.csv'
                      
    mp4_path = os.path.join(STORAGE_INPUT_FOLDER, mp4_filename)
    csv_path_1 = os.path.join(STORAGE_INPUT_FOLDER, csv_filename_1)
    csv_path_2 = os.path.join(STORAGE_INPUT_FOLDER, csv_filename_2)

    os.makedirs(app.config['STORAGE_FOLDER'], exist_ok=True)
    os.makedirs(STORAGE_INPUT_FOLDER, exist_ok=True)
    print('mp4_path', mp4_path)
    print('csv_path_1', csv_path_1)
    print('csv_path_2', csv_path_2)

    try:
        video_start, video_end = float(request.form.get('video-start')), float(request.form.get('video-end'))
        process_mov(mov_file, mp4_path, video_start, video_end)

        sensor1_start, sensor1_end = int(request.form.get('sensor1-start')), int(request.form.get('sensor1-end'))
        sensor2_start, sensor2_end = int(request.form.get('sensor2-start')), int(request.form.get('sensor2-end'))
        
        process_csv(cwa_file_1, csv_path_1, sensor1_start, sensor1_end)
        process_csv(cwa_file_2, csv_path_2, sensor2_start, sensor2_end)

        # Now, clear the download directory, 
        # then copy the result csv file and the import.json file to the download directory
        # Delete the upload folder together with all the files

        delete_and_recreate_dir(app.config['DOWNLOAD_FOLDER'])

        # Copy the resulting csv file to the download directory
        print("Copying csv file to download directory")
        shutil.copy(csv_path_1, os.path.join(app.config['DOWNLOAD_FOLDER'], csv_filename_1))
        shutil.copy(csv_path_2, os.path.join(app.config['DOWNLOAD_FOLDER'], csv_filename_2))

        import_filename_1 = f'import_{csv_filename_1}.json'

        print("Creating import file")

        # Setting default offset=0. The index would be the index of the csv bandpass file
        create_import_file(import_filename_1, csv_path_1, csv_path_2, csv_filename_1, mp4_filename, sensor=1)

        return redirect(url_for('final_instruction'))
    
    except Exception as e:
        print('Error', e)
        return f'Error converting file: {str(e)}'
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=not os.environ.get("PRODUCTION", False))
