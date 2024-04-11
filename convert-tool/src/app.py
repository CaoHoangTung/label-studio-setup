import os
import shutil
import time
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from controller.process import process_dataset_files
from env import env_config
from utils.cwa import find_file_in_dataset, get_cwa_data_from_file
from utils.dataset import get_file_name_from_path, delete_and_recreate_dir
from utils.paths import get_dataset_upload_dir, get_dataset_download_dir
from utils.process import process_mov, create_import_file, process_csv

app = Flask(__name__)
app.config.update(env_config)


@app.template_filter('ctime')
def timectime(s):
    return datetime.fromtimestamp(int(s)).strftime("%Y-%m-%d %H:%M:%S")


@app.route('/static/<filename>')
def serve_static_file(filename):
    return send_from_directory("static", filename)


@app.route("/")
def index():
    datasets = os.listdir(app.config['DATASET_FOLDER'])
    return render_template(
        'dataset/list.html',
        datasets=datasets
    )


@app.route('/dataset/<dataset_id>')
def dataset(dataset_id: str):
    dataset_path = get_dataset_upload_dir(dataset_id)

    if not os.path.exists(dataset_path):
        return render_template('404.html', message="Dataset not found"), 404

    return render_template(
        'dataset/detail.html',
        dataset_id=dataset_id,
    )


@app.route('/dataset/new')
def dataset_upload(message: str = ''):
    return render_template('dataset/upload.html', message=message)


@app.route('/dataset/new', methods=['POST'])
def upload_file():
    # Check if a file is uploaded
    if 'file_mov' not in request.files or 'file_cwa_1' not in request.files or 'file_cwa_2' not in request.files:
        return redirect(request.url)

    file_mov = request.files['file_mov']
    file_cwa_1 = request.files['file_cwa_1']
    file_cwa_2 = request.files['file_cwa_2']

    dataset_id = str(int(time.time()))
    process_dataset_files(dataset_id, file_cwa_1, file_cwa_2, file_mov)
    return redirect(url_for('dataset', dataset_id=dataset_id))


@app.route('/dataset/<dataset_id>/uploads/<filename>')
def get_dataset_uploaded_file(dataset_id, filename):
    upload_dir = get_dataset_upload_dir(dataset_id)
    return send_from_directory(upload_dir, filename, as_attachment=True)


@app.route('/dataset/<dataset_id>/downloads/<filename>')
def get_dataset_download_file(dataset_id, filename):
    download_dir = get_dataset_download_dir(dataset_id)
    return send_from_directory(download_dir, filename, as_attachment=True)


@app.route('/dataset/<dataset_id>/downloads/', methods=['DELETE'])
def dataset_delete():
    files = os.listdir(app.config['DOWNLOAD_FOLDER'])
    for file in files:
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], file)
        os.remove(file_path)

    return redirect(url_for('list_download'))


@app.route('/dataset/upload/', methods=['DELETE'])
def delete_upload_files():
    files = os.listdir(app.config['DATASET_FOLDER'])
    for file in files:
        file_path = os.path.join(app.config['DATASET_FOLDER'], file)
        os.remove(file_path)

    return redirect(url_for('list_upload'))


@app.route('/final-instruction')
def final_instruction():
    files = os.listdir(app.config['DOWNLOAD_FOLDER'])
    return render_template('final_instruction.html', files=files)


def append_with_datetime_prefix(csv_path, start_datetime, end_datetime):
    filename = os.path.basename(csv_path)
    return os.path.join(os.path.dirname(csv_path), f'{start_datetime}-{end_datetime}-{filename}')


# Process to create import file
@app.route('/dataset/<dataset_id>/convert', methods=['POST'])
def convert_to_labelstudio_package(dataset_id):
    dataset_upload_url = get_dataset_upload_dir(dataset_id)

    mp4_path = os.path.join(video)
    csv_path_1 = os.path.join(STORAGE_INPUT_FOLDER, csv_filename_1)
    csv_path_2 = os.path.join(STORAGE_INPUT_FOLDER, csv_filename_2)

    try:
        video_start, video_end = float(request.form.get('video-start')), float(request.form.get('video-end'))

        process_mov(mov_file, mp4_path, video_start, video_end)

        sensor1_start, sensor1_end = int(request.form.get('sensor1-start')), int(request.form.get('sensor1-end'))
        sensor2_start, sensor2_end = int(request.form.get('sensor2-start')), int(request.form.get('sensor2-end'))

        sensor1_start_datetime, sensor1_end_datetime = process_csv(cwa_file_1, csv_path_1, sensor1_start, sensor1_end)
        sensor2_start_datetime, sensor2_end_datetime = process_csv(cwa_file_2, csv_path_2, sensor2_start, sensor2_end)

        # Now, clear the download directory, 
        # then copy the result csv file and the import.json file to the download directory
        # Delete the upload folder together with all the files

        delete_and_recreate_dir(app.config['DOWNLOAD_FOLDER'])
        # Copy the resulting csv file to the download directory
        print("Copying csv file to download directory")
        shutil.copy(
            csv_path_1,
            os.path.join(app.config['DOWNLOAD_FOLDER'],
                         f'{sensor1_start_datetime}-{sensor1_end_datetime}-{csv_filename_1}')
        )
        shutil.copy(
            csv_path_2,
            os.path.join(app.config['DOWNLOAD_FOLDER'],
                         f'{sensor2_start_datetime}-{sensor2_end_datetime}-{csv_filename_2}')
        )

        import_filename_1 = f'import_{csv_filename_1}.json'

        # Setting default offset=0. The index would be the index of the csv bandpass file
        create_import_file(import_filename_1, csv_path_1, csv_path_2, csv_filename_1, mp4_filename, sensor=1)

        return redirect(url_for('final_instruction'))

    except Exception as e:
        print('Error', e)
        return f'Error converting file: {str(e)}'


if __name__ == '__main__':
    """Start a background thread that cleans up old tasks."""

    app.run(host="0.0.0.0", debug=not os.environ.get("PRODUCTION", False))
