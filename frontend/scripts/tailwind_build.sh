#!/bin/bash

# -----
# Script to build and minify tailwind.css for production
# Call this from the GCS repository root folder
# -----

./third_party/tailwindcss --cwd ./frontend -i ./config/tailwind.input.css -o ./static/css/tailwind.css --minify