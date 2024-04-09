import os
import pathlib
import shutil
import time

from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from env import env_config, STORAGE_INPUT_FOLDER, FIRST_SENSOR_PREFIX, SECOND_SENSOR_PREFIX
from utils.cwa import find_file_in_dataset, get_cwa_data_from_file
from utils.dataset import get_file_name_from_path, delete_and_recreate_dir
from utils.process import process_mov, create_import_file, process_csv

app = Flask(__name__)
app.config.update(env_config)


@app.route('/static/<filename>')
def serve_static_file(filename):
    return send_from_directory("static", filename)


@app.route("/")
def index():
    datasets = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template(
        'dataset/list.html',
        datasets=datasets
    )


@app.route('/dataset/<dataset_id>')
def dataset(dataset_id: str):
    cwa_file_1, cwa_file_2, mp4_file = find_file_in_dataset(dataset_id)

    if cwa_file_1 is None or cwa_file_2 is None or mp4_file is None:
        return render_template('404.html', message="Dataset not found"), 404

    cwa_data_1 = get_cwa_data_from_file(cwa_file_1).samples
    cwa_data_2 = get_cwa_data_from_file(cwa_file_2).samples

    return render_template(
        'dataset/detail.html',
        mp4_file=os.path.basename(mp4_file),
        sensor1_data=cwa_data_1,
        sensor2_data=cwa_data_2,
    )


@app.route('/dataset/upload')
def dataset_upload(message: str = ''):
    return render_template('dataset/upload.html', message=message)


@app.route('/dataset/upload', methods=['POST'])
def upload_file():
    # Check if a file is uploaded
    if 'file_mov' not in request.files or 'file_cwa_1' not in request.files or 'file_cwa_2' not in request.files:
        return redirect(request.url)

    file_mov = request.files['file_mov']
    file_cwa_1 = request.files['file_cwa_1']
    file_cwa_2 = request.files['file_cwa_2']

    dataset_id = str(int(time.time()))

    # Delete and recreate the upload folder
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], dataset_id)
    delete_and_recreate_dir(upload_dir)

    # Delete and recreate the download folder
    download_dir = os.path.join(app.config['DOWNLOAD_FOLDER'], dataset_id)
    delete_and_recreate_dir(download_dir)

    # Save the file to the upload folder
    mov_path = os.path.join(upload_dir, file_mov.filename)
    file_mov.save(mov_path)

    # Convert to mp4
    mp4_path = os.path.join(upload_dir, os.path.splitext(file_mov.filename)[0] + '.mp4')
    process_mov(mov_path, mp4_path)

    # Save signal files
    file_cwa_1.save(os.path.join(upload_dir, f'{FIRST_SENSOR_PREFIX}{file_cwa_1.filename}'))
    file_cwa_2.save(os.path.join(upload_dir, f'{SECOND_SENSOR_PREFIX}{file_cwa_2.filename}'))
    return redirect(url_for('dataset', dataset_id=dataset_id))


@app.route('/download/<filename>')
def download_file(filename):
    from_directory = request.args.get('from_directory', app.config['DOWNLOAD_FOLDER'])
    absolute_path = pathlib.Path(os.getcwd(), from_directory)
    return send_from_directory(absolute_path, filename, as_attachment=True)


@app.route('/dataset/<dataset_id>/downloads/', methods=['DELETE'])
def dataset_delete():
    files = os.listdir(app.config['DOWNLOAD_FOLDER'])
    for file in files:
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], file)
        os.remove(file_path)

    return redirect(url_for('list_download'))


@app.route('/dataset/upload/', methods=['DELETE'])
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


def append_with_datetime_prefix(csv_path, start_datetime, end_datetime):
    filename = os.path.basename(csv_path)
    return os.path.join(os.path.dirname(csv_path), f'{start_datetime}-{end_datetime}-{filename}')


# Process to create import file
@app.route('/import', methods=['POST'])
def import_label_studio():
    files = os.listdir(app.config['UPLOAD_FOLDER'])

    cwa_file_1, cwa_file_2, mov_file = find_file_in_dataset(files)

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

        print("Creating import file")

        # Setting default offset=0. The index would be the index of the csv bandpass file
        create_import_file(import_filename_1, csv_path_1, csv_path_2, csv_filename_1, mp4_filename, sensor=1)

        return redirect(url_for('final_instruction'))

    except Exception as e:
        print('Error', e)
        return f'Error converting file: {str(e)}'


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=not os.environ.get("PRODUCTION", False))
