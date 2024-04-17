import json
import os
import time
from typing import Iterable

import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip

from ls_client import LSSegmentClassifyProject
from utils.paths import get_dataset_match_dir, get_dataset_dir, get_dataset_chunk_dir


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
    match_dir = get_dataset_match_dir(dataset_id, match_id)
    with open(os.path.join(match_dir, "import.json")) as json_file:
        metadata = json.load(json_file)[0]
        sample_rate1, sample_rate2 = metadata.get("sample_rate1", 100), metadata.get("sample_rate2", 100)

    sensor1 = pd.read_csv(os.path.join(match_dir, "sensor1.csv"))
    sensor2 = pd.read_csv(os.path.join(match_dir, "sensor2.csv"))
    sensor1_chunks = chunk_pandas_dataframe(sensor1, int(sample_rate1 * chunk_size_second))
    sensor2_chunks = chunk_pandas_dataframe(sensor2, int(sample_rate2 * chunk_size_second))
    video_chunks = chunk_video(os.path.join(match_dir, "converted.mp4"), chunk_size_second)
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
        chunk_tasks.append({
            "csv": f"/data/local-files/?d=storage/{dataset_id}/chunk/{chunk_id}/{idx}/sensor1.csv",
            "csv2": f"/data/local-files/?d=storage/{dataset_id}/chunk/{chunk_id}/{idx}/sensor2.csv",
            "video": f"<video src='/data/local-files/?d=storage/{dataset_id}/chunk/{chunk_id}/{idx}/video.mp4' type='video/quicktime' width='100%' controls " + "onloadeddata=\"setTimeout(function(){ts=Htx.annotationStore.selected.names.get('ts');t=ts.data.index;v=document.getElementsByTagName('video')[0];w=parseInt(t.length*(5/v.duration));l=t.length-w;ts.updateTR([t[0], t[w]], 1.001);r=$=>ts.brushRange.map(n=>(+n).toFixed(2));_=r();setInterval($=>r().some((n,i)=>n!==_[i])&&(_=r())&&(v.currentTime=v.duration*(r()[0]-t[0])/(t.slice(-1)[0]-t[0]-(r()[1]-r()[0]))),300); console.log('video is loaded, starting to sync with time series')}, 3000); \" />",
            "sensor1_sample_rate": sample_rate1,
            "sensor2_sample_rate": sample_rate2,
        })

    with open(f"{chunk_dir}/imports.json", "w") as file:
        json.dump(chunk_tasks, file)

    LSSegmentClassifyProject.import_tasks(chunk_tasks)

    return chunk_id
