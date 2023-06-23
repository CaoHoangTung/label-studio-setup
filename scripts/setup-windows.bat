@echo off
call echo Installing...

::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::: Install label studio ::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::
call echo Installing Label Studio

call set LOCAL_DATA_PATH=%userprofile%\label-studio\data
call set LOCAL_STORAGE_PATH=%LOCAL_DATA_PATH%\storage
call echo Setting LOCAL_DATA_PATH=%LOCAL_DATA_PATH%
call echo Setting LOCAL_STORAGE_PATH=%LOCAL_STORAGE_PATH%

if not exist %LOCAL_DATA_PATH% mkdir %LOCAL_DATA_PATH%
if not exist %LOCAL_STORAGE_PATH% mkdir %LOCAL_STORAGE_PATH%
if not exist %LOCAL_STORAGE_PATH%\input mkdir %LOCAL_STORAGE_PATH%\input
if not exist %LOCAL_STORAGE_PATH%\output mkdir %LOCAL_STORAGE_PATH%\output

call echo Removing existing Label Studio installation...

call docker stop label_studio
call docker rm label_studio

call set LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/label-studio/data

call docker run ^
--name label_studio ^
-e LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true ^
-e LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=%LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT% ^
-d ^
--restart always ^
-p 8080:8080 ^
-v %LOCAL_DATA_PATH%:%LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT% ^
heartexlabs/label-studio:latest ^
label-studio ^
--log-level DEBUG

call echo Label Studio setup completed

::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::: Install convert tool ::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::
call echo Installing Convert Tool

call echo Removing existing Convert Tool installation...

call docker stop convert_tool
call docker rm convert_tool

call docker build -t convert-tool:latest ../../convert-tool

call docker run ^
--name convert_tool ^
-d ^
--restart always ^
-p 5000:5000 ^
-e PRODUCTION=true ^
-v %LOCAL_STORAGE_PATH%:/app/storage ^
convert-tool:latest

call echo Convert Tool setup completed

cmd /k echo App has been setup successfully