import cv2
import os
import time
import logging
from dotenv import load_dotenv
import datetime
from natsort import natsorted 
import glob
import shutil

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

def capture_frame(url, folder, width, height):
    now = datetime.datetime.now()
    start_time = now.replace(hour=8, minute=1, second=0, microsecond=0)
    end_time = now.replace(hour=21, minute=59, second=59, microsecond=999)

    if now < start_time or now > end_time:
        logging.info("Skipping capture. Current time is outside the specified range.")
        return False

    cap = cv2.VideoCapture(url)

    # Adjust the resolution to the specified values
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    ret, frame = cap.read()
    cap.release()

    if ret:
        prefix = os.getenv("IMAGE_PREFIX", "")  # Get the IMAGE_PREFIX environment variable
        filename = os.path.join(folder, f"{prefix}{time.strftime('%Y%m%d%H%M%S')}.jpg")
        cv2.imwrite(filename, frame)
        logging.info(f"Image saved as {filename}")
        return True
    else:
        logging.error("Failed to capture frame")
        return False

def create_video(image_folder, video_folder, threshold, delay):
    images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
    if len(images) < threshold:
        return

    # Sort the images based on their file dates in ascending order
    images = natsorted(images, key=lambda x: os.path.getmtime(os.path.join(image_folder, x)))

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, _ = frame.shape

    # Find the next available video filename
    now = datetime.datetime.now()
    video_filename = ""
    count = 1
    while True:
        video_name = f"daily-aloeCam{count}"
        video_filename = os.path.join(video_folder, f"{video_name}.avi")
        if not os.path.exists(video_filename):
            break
        count += 1

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video_writer = cv2.VideoWriter(video_filename, fourcc, 30, (width, height))

    for image in images:
        img_path = os.path.join(image_folder, image)
        frame = cv2.imread(img_path)
        for _ in range(delay * 30):  # 30 frames per second
            video_writer.write(frame)

    video_writer.release()
    logging.info(f"Video saved as {video_filename}")

    # Copy the captured images to weekly folder
    weekly_folder = os.getenv("WEEKLY_FOLDER")
    weekly_videos = glob.glob(os.path.join(weekly_folder, "*.avi"))
    if len(weekly_videos) >= int(os.getenv("WEEKLY_VIDEO_THRESHOLD")):
        create_combined_video(weekly_videos, os.path.join(os.getenv("WEEKLY_VIDEO_FOLDER"), "combined_weekly.avi"))
        for video in weekly_videos:
            os.remove(video)
        logging.info(f"Weekly videos created and images deleted.")

    # Copy the captured images to monthly folder
    monthly_folder = os.getenv("MONTHLY_FOLDER")
    monthly_videos = glob.glob(os.path.join(monthly_folder, "*.avi"))
    if len(monthly_videos) >= int(os.getenv("MONTHLY_VIDEO_THRESHOLD")):
        create_combined_video(monthly_videos, os.path.join(os.getenv("MONTHLY_VIDEO_FOLDER"), "combined_monthly.avi"))
        for video in monthly_videos:
            os.remove(video)
        logging.info(f"Monthly videos created and images deleted.")

    # Copy the captured images to yearly folder
    yearly_folder = os.getenv("YEARLY_FOLDER")
    yearly_videos = glob.glob(os.path.join(yearly_folder, "*.avi"))
    if len(yearly_videos) >= int(os.getenv("YEARLY_VIDEO_THRESHOLD")):
        create_combined_video(yearly_videos, os.path.join(os.getenv("YEARLY_VIDEO_FOLDER"), "combined_yearly.avi"))
        for video in yearly_videos:
            os.remove(video)
        logging.info(f"Yearly videos created and images deleted.")

    # Remove the captured images after creating the video
    for image in images:
        img_path = os.path.join(image_folder, image)
        os.remove(img_path)


    video_writer.release()
    logging.info(f"Video saved as {video_filename}")

    # Copy the captured images to weekly folder
    weekly_folder = os.getenv("WEEKLY_FOLDER")
    for image in images:
        img_path = os.path.join(image_folder, image)
        dst_path = os.path.join(weekly_folder, image)
        shutil.copy(img_path, dst_path)

    # Copy the captured images to monthly folder
    monthly_folder = os.getenv("MONTHLY_FOLDER")
    for image in images:
        img_path = os.path.join(image_folder, image)
        dst_path = os.path.join(monthly_folder, image)
        shutil.copy(img_path, dst_path)

    # Copy the captured images to yearly folder
    yearly_folder = os.getenv("YEARLY_FOLDER")
    for image in images:
        img_path = os.path.join(image_folder, image)
        dst_path = os.path.join(yearly_folder, image)
        shutil.copy(img_path, dst_path)

    # Remove the captured images after creating the video
    for image in images:
        img_path = os.path.join(image_folder, image)
        os.remove(img_path)

def capture_initial_frame(url, folder, width, height):
    if capture_frame(url, folder, width, height):
        image_count = len([img for img in os.listdir(folder) if img.endswith(".jpg")])
        logging.info(f"Initial frame captured. Total images: {image_count}")

def main():
    # Get environment variables
    url = os.getenv("URL")
    image_folder = os.getenv("IMAGE_FOLDER")
    video_folder = os.getenv("VIDEO_FOLDER")
    width = int(os.getenv("CAP_PROP_FRAME_WIDTH"))
    height = int(os.getenv("CAP_PROP_FRAME_HEIGHT"))
    threshold = int(os.getenv("VIDEO_THRESHOLD"))
    delay = int(os.getenv("VIDEO_DELAY", 1))  # 1 second by default
    sleep_duration = int(os.getenv("SLEEP_DURATION", 30))  # 30 seconds by default

    # Create the images and videos folders if they don't exist
    os.makedirs(image_folder, exist_ok=True)
    os.makedirs(video_folder, exist_ok=True)

    # Capture the initial frame
    logging.info("Capturing initial frame...")
    capture_initial_frame(url, image_folder, width, height)

    while True:
        logging.info("Attempting to capture frame...")
        if capture_frame(url, image_folder, width, height):
            image_count = len([img for img in os.listdir(image_folder) if img.endswith(".jpg")])
            if image_count % threshold == 0 or datetime.datetime.now().hour == 21:
                create_video(image_folder, video_folder, threshold, delay)

        logging.info(f"Waiting for {sleep_duration} seconds...")
        time.sleep(sleep_duration)  # Sleep for specified duration

if __name__ == "__main__":
    main()
