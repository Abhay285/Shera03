# Use Python 3.10 slim image
FROM python:3.10.8-slim-buster

# Update system and install dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Set work directory for application code
WORKDIR /VJ-Post-Search-Bot

# Copy the requirements file and install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip3 install -U pip && pip3 install -r requirements.txt

# Copy the rest of the application code
COPY . /VJ-Post-Search-Bot

# Expose the port that the app will run on
EXPOSE 8000

# Use a script to run both Gunicorn and your Python script
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:8000 app:app & python3 main.py"]
