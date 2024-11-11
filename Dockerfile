# Use Python 3.10 slim image based on Debian Buster
FROM python:3.10.8-slim-buster

# Install necessary dependencies
RUN apt update && apt install -y \
    git \
    build-essential \
    libpq-dev && \
    apt clean && rm -rf /var/lib/apt/lists/*

# Set the working directory for the app
WORKDIR /VJ-Post-Search-Bot

# Copy the requirements.txt file first to leverage Docker cache
COPY requirements.txt /requirements.txt

# Upgrade pip and install Python dependencies
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /VJ-Post-Search-Bot

# Expose the port your app will run on
EXPOSE 8000

# Use CMD to run both Gunicorn and your main app
CMD gunicorn app:app --bind 0.0.0.0:8000 & python3 main.py
