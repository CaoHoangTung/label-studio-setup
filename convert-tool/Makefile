start:
	(trap 'kill 0' SIGINT; \
		STORAGE_FOLDER=.data/storage python3 ./src/app.py & \
		tailwindcss -i ./src/static/input.css -o ./src/static/output.css --watch & \
		wait \
	)

deps:
	pip3 install -r convert-tool/requirements.txt