#!/bin/bash

# Install gdown if not installed
pip install gdown

# Download the model
echo "Downloading model files..."
gdown https://drive.google.com/uc?id=1fiB7AXvtc8CA9NRbtLJVJ4loBExP8Yyq -O model.pkl

