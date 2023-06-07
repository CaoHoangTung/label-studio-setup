# Label studio guideline

## Docker installation

## Setup label studio

### Run the tool
Inside the project root directory, run the label studio server with Docker

```bash
docker run --env-file ./.env -it -p 8080:8080 -v $(pwd)/data:/label-studio/data heartexlabs/label-studio:latest label-studio --log-level DEBUG
```

### Configure the project

#### Add local storage
Go to project -> Settings -> Cloud Storage.

Choose `Local Files`

Add storage input path: `/label-studio/data/storage/input`
Add storage output path: `/label-studio/data/storage/output`
