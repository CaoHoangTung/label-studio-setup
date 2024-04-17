import os
import shutil
import time
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from controller.chunk import chunk_video_and_sensors
from controller.match import process_dataset_upload, process_match_file
from env import env_config
from utils.jinja import define_jinja_functions
from utils.paths import get_dataset_upload_dir, get_dataset_match_dir, get_dataset_dir, get_dataset_processed_dir, \
    get_dataset_chunk_dir

app = Flask(__name__)
app.config.update(env_config)

define_jinja_functions(app)


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
def dataset_detail(dataset_id: str):
    upload_dir = get_dataset_upload_dir(dataset_id)
    processed_dir = get_dataset_processed_dir(dataset_id)

    if not os.path.exists(upload_dir):
        return render_template('404.html', message="Dataset not found"), 404

    uploaded_files = os.listdir(upload_dir)
    processed_files = os.listdir(processed_dir)

    return render_template(
        'dataset/detail.html',
        dataset_id=dataset_id,
        uploaded_files=uploaded_files,
        processed_files=processed_files,
    )


@app.route('/dataset/<dataset_id>/match')
def dataset_match(dataset_id: str):
    dataset_path = get_dataset_dir(dataset_id)

    if not os.path.exists(dataset_path):
        return render_template('404.html', message="Dataset not found"), 404

    return render_template(
        'dataset/match/match_form.html',
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
    process_dataset_upload(dataset_id, file_cwa_1, file_cwa_2, file_mov)
    return redirect(url_for('dataset_detail', dataset_id=dataset_id))


@app.route('/dataset/<dataset_id>/uploads/<filename>')
def get_dataset_uploaded_file(dataset_id, filename):
    upload_dir = get_dataset_upload_dir(dataset_id)
    return send_from_directory(upload_dir, filename, as_attachment=True)


@app.route('/dataset/<dataset_id>/processed/<filename>')
def get_dataset_processed_file(dataset_id, filename):
    processed_dir = get_dataset_processed_dir(dataset_id)
    return send_from_directory(processed_dir, filename, as_attachment=True)


@app.route('/dataset/<dataset_id>/matches/<match_id>')
def get_match_detail(dataset_id, match_id):
    match_dir = get_dataset_match_dir(dataset_id, match_id)
    files = os.listdir(match_dir)
    return render_template('dataset/match/match_detail.html', dataset_id=dataset_id, match_id=match_id, files=files)


@app.route('/dataset/<dataset_id>/matches/<match_id>/chunks', methods=['GET'])
def form_chunk_matched_data(dataset_id, match_id):
    return render_template("dataset/chunk/chunk_form.html", dataset_id=dataset_id, match_id=match_id)


@app.route('/dataset/<dataset_id>/matches/<match_id>/files/<filename>')
def download_match_file(dataset_id, match_id, filename):
    match_dir = get_dataset_match_dir(dataset_id, match_id)
    return send_from_directory(match_dir, filename, as_attachment=True)


def append_with_datetime_prefix(csv_path, start_datetime, end_datetime):
    filename = os.path.basename(csv_path)
    return os.path.join(os.path.dirname(csv_path), f'{start_datetime}-{end_datetime}-{filename}')


# Process to create import file
@app.route('/dataset/<dataset_id>/match', methods=['POST'])
def process_match_dataset(dataset_id):
    sensor1_start, sensor1_end = int(request.form.get('sensor1-start')), int(request.form.get('sensor1-end'))
    sensor2_start, sensor2_end = int(request.form.get('sensor2-start')), int(request.form.get('sensor2-end'))
    video_start, video_end = int(request.form.get('video-start')), int(request.form.get('video-start'))
    match_id = process_match_file(
        dataset_id, video_start, video_end,
        sensor1_start, sensor1_end, sensor2_start, sensor2_end
    )

    return redirect(url_for("get_match_detail", dataset_id=dataset_id, match_id=match_id))


@app.route('/dataset/<dataset_id>/matches/<match_id>/chunks', methods=['POST'])
def process_chunk_dataset(dataset_id, match_id):
    chunk_id = chunk_video_and_sensors(dataset_id, match_id, int(request.form.get('chunk-size')))
    return redirect(url_for("get_chunk_detail", dataset_id=dataset_id, chunk_id=chunk_id))


@app.route('/dataset/<dataset_id>/chunks/<chunk_id>', methods=['GET'])
def get_chunk_detail(dataset_id, chunk_id):
    chunk_dir = get_dataset_chunk_dir(dataset_id, chunk_id)
    chunks = [d for d in os.listdir(chunk_dir) if os.path.isdir(os.path.join(chunk_dir, d))]
    return render_template("dataset/chunk/chunk_detail.html", dataset_id=dataset_id, chunk_id=chunk_id, chunks=chunks)


@app.route('/dataset/<dataset_id>/chunks/<chunk_id>/files/<chunk>/<filename>', methods=['GET'])
def download_chunk_file(dataset_id, chunk_id, chunk, filename):
    chunk_dir = get_dataset_chunk_dir(dataset_id, chunk_id)
    chunk_path = os.path.join(chunk_dir, chunk)
    return send_from_directory(chunk_path, filename, as_attachment=True)


@app.route('/dataset/<dataset_id>/chunks/<chunk_id>/zip', methods=['GET'])
def download_chunk_zip(dataset_id, chunk_id):
    chunk_dir = get_dataset_chunk_dir(dataset_id, chunk_id)
    file_basename = os.path.join(chunk_dir, f"{dataset_id}")
    file_path = file_basename + ".zip"
    if not os.path.exists(file_path):
        shutil.make_archive(file_basename, "zip", chunk_dir)

    return send_from_directory(chunk_dir, f"{dataset_id}_{chunk_id}.zip", as_attachment=True)


if __name__ == '__main__':
    """Start a background thread that cleans up old tasks."""

    app.run(host="0.0.0.0", debug=not os.environ.get("PRODUCTION", False))
