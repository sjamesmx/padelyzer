#!/bin/bash

# List of ML dependencies to install
deps=(
    "opencv-python==4.8.1.78"
    "mediapipe==0.10.18"
    "tensorflow==2.19.0"
    "numpy==1.26.1"
    "pandas==2.1.2"
    "scikit-learn==1.3.2"
    "matplotlib"
    "opencv-contrib-python"
    "ultralytics==8.0.196"
    "deep-sort-realtime==1.3.2"
    "torch>=1.8.0"
    "torchvision>=0.9.0"
    "thop>=0.1.1"
)

# Install each dependency
for dep in "${deps[@]}"; do
    echo "Installing $dep..."
    pip install --no-cache-dir "$dep"
    if [ $? -eq 0 ]; then
        echo "Successfully installed $dep"
    else
        echo "Failed to install $dep"
        exit 1
    fi
done 