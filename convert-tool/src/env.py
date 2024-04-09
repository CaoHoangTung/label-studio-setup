import os

env_config = {
    'UPLOAD_FOLDER': os.environ.get('UPLOAD_FOLDER', './.data/upload'),
    'DOWNLOAD_FOLDER': os.environ.get('DOWNLOAD_FOLDER', './.data/download'),
    'STORAGE_FOLDER': os.environ.get('STORAGE_FOLDER', './.data/storage')
}

os.makedirs(env_config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(env_config['DOWNLOAD_FOLDER'], exist_ok=True)
os.makedirs(env_config['UPLOAD_FOLDER'], exist_ok=True)

STORAGE_INPUT_FOLDER = os.path.join(env_config['STORAGE_FOLDER'], "input")
os.makedirs(STORAGE_INPUT_FOLDER, exist_ok=True)

FIRST_SENSOR_PREFIX = 'sensor1_'
SECOND_SENSOR_PREFIX = 'sensor2_'
