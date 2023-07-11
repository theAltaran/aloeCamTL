# Use the official Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code into the container
COPY . .

# Set the environment variables

# Address of what to frame capture
ENV URL=https://cam.aloecam.duckdns.org/
# What size pic to capture
ENV CAP_PROP_FRAME_WIDTH=1280
ENV CAP_PROP_FRAME_HEIGHT=720
# Title prefix for daily images.
ENV IMAGE_PREFIX=daily-
# Number of frames to take/collect before making video and moving photos.
ENV VIDEO_THRESHOLD=50
ENV WEEKLY_VIDEO_THRESHOLD=350
ENV MONTHLY_VIDEO_THRESHOLD=1500
ENV YEARLY_VIDEO_THRESHOLD=18250
# How long each frame shows in a video. In Seconds.
ENV VIDEO_DELAY=1             
ENV WEEKLY_VIDEO_DELAY=0.143
ENV MONTHLY_VIDEO_DELAY=0.0334
ENV YEARLY_VIDEO_DELAY=0.00274
# Time between daily pictures to equal 50 in a day
ENV SLEEP_DURATION=980
# Where the program will store the photos its working with
ENV IMAGE_FOLDER=/data/daily
ENV WEEKLY_FOLDER=/data/weekly
ENV MONTHLY_FOLDER=/data/monthly
ENV YEARLY_FOLDER=/data/yearly
# Where to store finished videos
ENV VIDEO_FOLDER=/data/videos/daily
ENV WEEKLY_VIDEO_FOLDER=/data/videos/weekly
ENV MONTHLY_VIDEO_FOLDER=/data/videos/monthly
ENV YEARLY_VIDEO_FOLDER=/data/videos/yearly
# Which mp3 to play during video
ENV AUDIO_FILE=/data/assets/aloeTL.mp3
ENV CONSTANT_IMAGE_PATH=/data/assets/aloe.jpg
ENV TZ=America/New_York

# Run the Python program
CMD [ "python", "main.py" ]
