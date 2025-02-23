#!/bin/bash

echo "Installing Label Studio & Convert tool"

docker compose up -d

echo "Label Studio setup completed. Please navigate to your browser to continue."
echo "  - To open the convert tool, go to http://localhost:5000"
echo "  - To open Label Studio, go to http://localhost:8080"

echo ""
echo "Note: The projects are created automatically. Project names are used by convert tool to identify projects.
Do not rename the projects"

