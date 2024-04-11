import os

env_config = {
    'DATASET_FOLDER': os.environ.get('DATASET_FOLDER', './.data/dataset'),
    'STORAGE_FOLDER': os.environ.get('STORAGE_FOLDER', './.data/storage'),
    'DOWNLOAD_FOLDER': os.environ.get('STORAGE_FOLDER', './.data/download')
}

os.makedirs(env_config['DATASET_FOLDER'], exist_ok=True)
os.makedirs(env_config['STORAGE_FOLDER'], exist_ok=True)
os.makedirs(env_config['DOWNLOAD_FOLDER'], exist_ok=True)

FIRST_SENSOR_PREFIX = 'sensor1_'
SECOND_SENSOR_PREFIX = 'sensor2_'
