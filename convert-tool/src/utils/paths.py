import os

from env import env_config


def get_dataset_dir(dataset_id):
    return os.path.join(os.getcwd(), env_config['DATASET_FOLDER'], dataset_id)


def get_dataset_upload_dir(dataset_id):
    return os.path.join(os.getcwd(), env_config['DATASET_FOLDER'], dataset_id, "upload")


def get_dataset_download_dir(dataset_id):
    return os.path.join(os.getcwd(), env_config['DATASET_FOLDER'], dataset_id, "download")
