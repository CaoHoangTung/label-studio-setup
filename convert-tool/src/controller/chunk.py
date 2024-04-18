import json
import os
import time
from typing import Iterable

import pandas as pd
from flask import render_template
from moviepy.video.io.VideoFileClip import VideoFileClip

from ls_client import LSSegmentClassifyProject
from utils.paths import get_match_dir, get_dataset_dir, get_dataset_chunk_dir, get_dataset_metadata


def float_range(start: float, stop: float, step: float) -> Iterable[float]:
    s = start if start < stop else stop
    e = stop if stop > start else start
    while s < e:
        yield s
        s += step


def chunk_video(video_path, chunk_time_second) -> Iterable[VideoFileClip]:
    with VideoFileClip(video_path) as video:
        for i in float_range(0, video.duration, chunk_time_second):
            end = min(video.duration, i + chunk_time_second)
            yield video.subclip(i, end)


def chunk_pandas_dataframe(df: pd.DataFrame, chunk_size: int) -> Iterable[pd.DataFrame]:
    for i in range(0, df.shape[0], chunk_size):
        yield df[i:i + chunk_size]


def chunk_video_and_sensors(dataset_id, match_id, chunk_size_second):
    if chunk_size_second < 0:
        raise ValueError("chunk_size_second must be a positive number")
    match_dir = get_match_dir(dataset_id, match_id)
    metadata = get_dataset_metadata(dataset_id)
    sample_rate1, sample_rate2 = metadata.get("sample_rate1", 100), metadata.get("sample_rate2", 100)
    sensor1 = pd.read_csv(os.path.join(match_dir, "sensor1.csv"))
    sensor2 = pd.read_csv(os.path.join(match_dir, "sensor2.csv"))
    sensor1_chunks = chunk_pandas_dataframe(sensor1, int(sample_rate1 * chunk_size_second))
    sensor2_chunks = chunk_pandas_dataframe(sensor2, int(sample_rate2 * chunk_size_second))
    video_chunks = chunk_video(os.path.join(match_dir, "video.mp4"), chunk_size_second)
    chunk_id = str(int(time.time()))
    chunk_dir = get_dataset_chunk_dir(dataset_id, chunk_id)
    os.makedirs(chunk_dir, exist_ok=True)

    chunk_tasks = []

    for idx, (video_chunk, sensor1_chunk, sensor2_chunk) in enumerate(
            zip(video_chunks, sensor1_chunks, sensor2_chunks)):
        folder = os.path.join(chunk_dir, f"{idx}")
        os.makedirs(folder, exist_ok=True)
        video_path = os.path.join(folder, "video.mp4")
        sensor1_path = os.path.join(folder, "sensor1.csv")
        sensor2_path = os.path.join(folder, "sensor2.csv")

        video_chunk.write_videofile(video_path)
        sensor1_chunk.to_csv(sensor1_path)
        sensor2_chunk.to_csv(sensor2_path)
        chunk_task = render_template(
            "dataset/chunk/import_template.json",
            dataset_id=dataset_id,
            chunk_id=chunk_id,
            idx=idx,
        )
        chunk_tasks.append(chunk_task)

    chunk_str = ',\n'.join(chunk_tasks)
    chunk_import_data = f"""
    [
        {chunk_str} 
    ]
    """
    chunk_import_file = f"{chunk_dir}/imports.json"
    with open(chunk_import_file, "w") as file:
        print(chunk_import_data, file=file)

    LSSegmentClassifyProject.import_tasks(chunk_import_file)

    return chunk_id


def create_chunk_import_file(
        dataset_id, match_id,
        import_file_path,
        sample_rate1, sample_rate2,
        csv_path1, csv_path2,
        sensor="unknown",
):
    import_data = render_template(
        "dataset/match/import_template.json",
        sensor=str(sensor),
        dataset_id=dataset_id,
        sample_rate1=sample_rate1,
        sample_rate2=sample_rate2,
        match_id=match_id,
        csv_path1=csv_path1,
        csv_path2=csv_path2,
    )

    with open(import_file_path, 'w') as file:
        print(import_data, file=file)
    return import_file_path
