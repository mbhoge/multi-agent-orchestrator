#!/bin/bash

# Script to set up AWS SDK (Boto3) and other dependencies

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 is not installed. Please install Python3 and rerun the script."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null
then
    echo "pip3 is not installed. Installing pip3..."
    sudo apt-get update && sudo apt-get install -y python3-pip
fi

# Install virtualenv if not installed
if ! pip3 show virtualenv &> /dev/null
then
    echo "virtualenv is not installed. Installing virtualenv..."
    pip3 install virtualenv
fi

# Create and activate a virtual environment
if [ ! -d "venv" ]; then
    echo "Creating a virtual environment..."
    python3 -m virtualenv venv
fi

source venv/bin/activate

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip3 install -r requirements.txt
else
    echo "requirements.txt not found. Installing boto3..."
    pip3 install boto3
fi

echo "Setup complete. AWS SDK (Boto3) and dependencies are installed."

deactivate