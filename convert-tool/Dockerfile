FROM node:20 as tailwind-builder

COPY package.json yarn.lock ./

RUN yarn

COPY . .

RUN yarn tailwindcss -c tailwind.config.js -i src/static/input.css -o output.css


# Use lightweight Python layout image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install patch

# Copy the application code to the container
COPY . .

COPY --from=tailwind-builder output.css ./src/static/output.css

RUN patch  /usr/local/lib/python3.11/site-packages/label_studio_sdk/client.py ls-sdk.patch

EXPOSE 5000

# Set the entry point for the container
CMD ["python", "src/app.py"]