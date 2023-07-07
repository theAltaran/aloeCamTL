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
ENV URL=https://cam.aloecam.duckdns.org/
ENV CAP_PROP_FRAME_WIDTH=1280
ENV CAP_PROP_FRAME_HEIGHT=720
ENV VIDEO_THRESHOLD=50
ENV WEEKLY_VIDEO_THRESHOLD=350
ENV MONTHLY_VIDEO_THRESHOLD=1500
ENV YEARLY_VIDEO_THRESHOLD=18250
ENV VIDEO_DELAY=1
ENV SLEEP_DURATION=1005
ENV IMAGE_FOLDER=/dockerData/aloeCamVideoRecorder/daily/images
ENV VIDEO_FOLDER=/dockerData/aloeCamVideoRecorder/daily/videos
ENV WEEKLY_VIDEO_FOLDER=/dockerData/aloeCamVideoRecorder/weekly/videos
ENV MONTHLY_VIDEO_FOLDER=/dockerData/aloeCamVideoRecorder/monthly/videos
ENV YEARLY_VIDEO_FOLDER=/dockerData/aloeCamVideoRecorder/yearly/videos
ENV TZ=America/New_York
ENV IMAGE_PREFIX=daily-
ENV WEEKLY_FOLDER=/dockerData/aloeCamVideoRecorder/weekly/images
ENV MONTHLY_FOLDER=/dockerData/aloeCamVideoRecorder/monthly/images
ENV YEARLY_FOLDER=/dockerData/aloeCamVideoRecorder/yearly/images




# Create a user and group
RUN groupadd -g 1000 altaran && \
    useradd -u 1000 -g altaran -m -s /bin/bash altaran

# Change ownership of the app directory to the altaran user and group
RUN chown -R altaran:altaran /app

# Change to the altaran user
USER altaran

# Run the Python program
CMD [ "python", "main.py" ]
