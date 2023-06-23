Window setup
$env:STORAGE_FOLDER='C:\Users\ADMIN\label-studio\data\storage\input' ; python .\app.py

Run with docker
docker stop convert_tool ; docker rm convert_tool  ; docker run --name convert_tool -d --restart always -p 5000:5000 -e PRODUCTION=true -v C:\Users\ADMIN\label-studio\data\storage:/app/storage convert-tool:latest