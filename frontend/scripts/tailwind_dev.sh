#!/bin/bash

# -----
# Watcher for realtime dev/updating of tailwind.css
# Call this from the GCS repository root folder
# -----

./third_party/tailwindcss --cwd ./frontend -i ./config/tailwind.input.css -o ./static/css/tailwind.css --watch --optimize