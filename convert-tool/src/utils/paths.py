import glob
import json
import os
from typing import List

from env import env_config, FIRST_SENSOR_PREFIX, SECOND_SENSOR_PREFIX


def get_dataset_dir(dataset_id):
    return os.path.join(os.getcwd(), env_config['DATASET_FOLDER'], dataset_id)


def get_dataset_upload_dir(dataset_id):
    return os.path.join(os.getcwd(), env_config['DATASET_FOLDER'], dataset_id, "upload")


def get_dataset_metadata_json_path(dataset_id):
    dataset_dir = get_dataset_dir(dataset_id)
    return os.path.join(dataset_dir, "processed", 'metadata.json')


def get_dataset_metadata(dataset_id):
    with open(get_dataset_metadata_json_path(dataset_id), "r") as file:
        return json.load(file)


def get_dataset_processed_dir(dataset_id):
    return os.path.join(os.getcwd(), env_config['DATASET_FOLDER'], dataset_id, "processed")


def get_dataset_matches_dir(dataset_id):
    return os.path.join(os.getcwd(), env_config['DATASET_FOLDER'], dataset_id, "match")


def get_match_dir(dataset_id, match_id):
    return os.path.join(get_dataset_matches_dir(dataset_id), match_id)


def get_dataset_chunk_list_dir(dataset_id):
    return os.path.join(os.getcwd(), env_config['DATASET_FOLDER'], dataset_id, "chunk")


def get_dataset_chunk_dir(dataset_id, chunk_id):
    return os.path.join(os.getcwd(), env_config['DATASET_FOLDER'], dataset_id, "chunk", chunk_id)


def first(lst: List[any]) -> any:
    return lst[0] if lst and len(lst) > 0 else None


def list_numeric(directory: str) -> List[str]:
    if not os.path.isdir(directory):
        return []
    return sorted([d for d in os.listdir(directory) if d.isdigit()])


def find_file_in_dataset(dataset_id: str):
    uploaded_dir = get_dataset_upload_dir(dataset_id)
    if not os.path.exists(uploaded_dir):
        return None, None, None

    processed_dir = get_dataset_processed_dir(dataset_id)
    if not os.path.exists(processed_dir):
        return None, None, None

    cwa_file_1 = first(glob.glob(uploaded_dir + f"/{FIRST_SENSOR_PREFIX}*.cwa"))
    cwa_file_2 = first(glob.glob(uploaded_dir + f"/{SECOND_SENSOR_PREFIX}*.cwa"))
    mp4_file = first(glob.glob(processed_dir + f"/*.mp4"))
    return cwa_file_1, cwa_file_2, mp4_file
