#!/bin/bash

echo "Installing..."

###############################################
############### Install Label Studio ##########
###############################################
echo "Installing Label Studio"

LOCAL_DATA_PATH="$HOME/label-studio/data"
LOCAL_STORAGE_PATH="$LOCAL_DATA_PATH/storage"
echo "Setting LOCAL_DATA_PATH=$LOCAL_DATA_PATH"
echo "Setting LOCAL_STORAGE_PATH=$LOCAL_STORAGE_PATH"

mkdir -p "$LOCAL_DATA_PATH"
mkdir -p "$LOCAL_STORAGE_PATH"
mkdir -p "$LOCAL_STORAGE_PATH/input"
mkdir -p "$LOCAL_STORAGE_PATH/output"

echo "Removing existing Label Studio installation..."
docker stop label_studio
docker rm label_studio

docker build -t heartexlabs/label-studio:latest ../label-studio

LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="/label-studio/data"

docker run \
--name label_studio \
-e LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true \
-e LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT" \
-d \
--restart always \
-p 8080:8080 \
-v "$LOCAL_DATA_PATH":"$LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT" \
heartexlabs/label-studio:latest \
label-studio start UpwatchSegmentation \
--init --no-browser --username upwatcher@gmail.com --password upwatch \
--label-config /label-studio/label_studio/annotation_templates/upwatch_video_timeseries/config.xml \
--log-level DEBUG

echo "Label Studio setup completed"

###############################################
############### Install convert tool ###########
###############################################
echo "Installing Convert Tool"

echo "Removing existing Convert Tool installation..."
docker stop convert_tool
docker rm convert_tool

docker build -t convert-tool:latest ../convert-tool

docker run \
--name convert_tool \
-d \
--restart always \
-p 5000:5000 \
-e PRODUCTION=true \
-e STORAGE_FOLDER="$LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT/storage" \
-v "$LOCAL_STORAGE_PATH":"$LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT/storage" \
convert-tool:latest

echo "Convert Tool setup completed"

echo "App has been set up successfully"
