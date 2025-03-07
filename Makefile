start:
	(trap 'kill 0' SIGINT; \
		DOTENV_FILE=./.env \
		DATASET_FOLDER=./.docker/convert-tool/dataset \
		STORAGE_FOLDER=./.docker/convert-tool/dataset \
		DOWNLOAD_FOLDER=./.docker/convert-tool/dataset \
		python3 ./convert-tool/src/app.py & \
		(cd convert-tool && tailwindcss -c tailwind.config.js -i src/static/input.css -o src/static/output.css --watch) & \
		wait \
	)

deps:
	pip3 install -r convert-tool/requirements.txt

label_studio:
	docker compose -f docker-compose.dev.yml up -d

label_studio_down:
	docker compose -f docker-compose.dev.yml down

dev_services:
	docker compose up -d nginx app db

dev:
	python convert-tool/src/app.py