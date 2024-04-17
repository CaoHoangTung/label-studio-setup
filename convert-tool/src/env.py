import os
from dotenv import load_dotenv

env_config = {
    'DATASET_FOLDER': os.environ.get('DATASET_FOLDER', './.data/dataset'),
    'STORAGE_FOLDER': os.environ.get('STORAGE_FOLDER', './.data/storage'),
    'DOWNLOAD_FOLDER': os.environ.get('STORAGE_FOLDER', './.data/download')
}

DOTENV_FILE = os.environ.get("DOTENV_FILE")
if DOTENV_FILE is not None:
    load_dotenv(DOTENV_FILE)

os.makedirs(env_config['DATASET_FOLDER'], exist_ok=True)
os.makedirs(env_config['STORAGE_FOLDER'], exist_ok=True)
os.makedirs(env_config['DOWNLOAD_FOLDER'], exist_ok=True)

FIRST_SENSOR_PREFIX = 'sensor1_'
SECOND_SENSOR_PREFIX = 'sensor2_'

LABEL_STUDIO_HOST = os.environ.get('LABEL_STUDIO_HOST', 'http://localhost:8080')
LABEL_STUDIO_EMAIL = os.environ.get('LABEL_STUDIO_EMAIL', 'upwatcher@gmail.com')
LABEL_STUDIO_PASSWORD = os.environ.get('LABEL_STUDIO_PASSWORD', 'upwatch')
LABEL_STUDIO_USER_TOKEN = os.environ.get('LABEL_STUDIO_USER_TOKEN')
LABEL_STUDIO_SEGMENT_MATCH_PROJECT_ID = os.environ.get('LABEL_STUDIO_SEGMENT_MATCH_PROJECT_ID')
LABEL_STUDIO_SEGMENT_CLASSIFY_PROJECT_ID = os.environ.get('LABEL_STUDIO_SEGMENT_CLASSIFY_PROJECT_ID')
