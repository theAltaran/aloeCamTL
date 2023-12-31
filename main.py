import cv2
import os
import time
import logging
from dotenv import load_dotenv
import datetime
from natsort import natsorted
import glob
import shutil
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip

import warnings
warnings.filterwarnings("ignore", category=UserWarning)


# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def capture_frame(url, folder, width, height):
    now = datetime.datetime.now()
    start_time = now.replace(hour=8, minute=1, second=0, microsecond=0)
    end_time = now.replace(hour=21, minute=59, second=0, microsecond=0)

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


def create_video(image_folder, video_folder, threshold, delay, audio_file, video_prefix, constant_image_path):
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
        video_name = f"{video_prefix}-aloeCam{count}"
        video_filename = os.path.join(video_folder, f"{video_name}.mp4")
        if not os.path.exists(video_filename):
            break
        count += 1

    video_clips = []
    for image in images:
        img_path = os.path.join(image_folder, image)
        video_clip = VideoFileClip(img_path)
        video_clips.append(video_clip.subclip(0, delay))

    # Calculate the remaining duration for the last frame
    remaining_duration = 59 - sum(clip.duration for clip in video_clips)

    # Adjust the duration of the last frame to fit within the remaining time
    if remaining_duration < 0:
        last_clip = video_clips[-1]
        last_clip = last_clip.resize(duration=last_clip.duration + remaining_duration)
        video_clips[-1] = last_clip

    # Add a constant image for the last frame if there is remaining duration
    if remaining_duration > 0:
        constant_image = ImageClip(constant_image_path).set_duration(remaining_duration)
        video_clips.append(constant_image)

    final_clip = concatenate_videoclips(video_clips)
    final_clip.write_videofile(video_filename, codec="libx264", audio=audio_file)

    logging.info(f"Video saved as {video_filename}")


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
    weekly_video_delay = float(os.getenv("WEEKLY_VIDEO_DELAY", 1.0))  # 1 second by default (as float)
    monthly_video_delay = float(os.getenv("MONTHLY_VIDEO_DELAY", 1.0))  # 1 second by default (as float)
    yearly_video_delay = float(os.getenv("YEARLY_VIDEO_DELAY", 1.0))  # 1 second by default (as float)
    audio_file = os.getenv("AUDIO_FILE")  # Path to the MP3 audio file
    constant_image_path = os.getenv("CONSTANT_IMAGE_PATH")  # Path to the constant JPG image

    # Create the images and videos folders if they don't exist
    os.makedirs(image_folder, exist_ok=True)
    os.makedirs(video_folder, exist_ok=True)

    while True:
        logging.info("Attempting to capture frame...")
        if capture_frame(url, image_folder, width, height):
            logging.info("Frame captured successfully")
        else:
            logging.info("Failed to capture frame")

        daily_image_count = len([img for img in os.listdir(image_folder) if img.endswith(".jpg")])
        weekly_image_count = len([img for img in os.listdir(os.getenv("WEEKLY_FOLDER")) if img.endswith(".jpg")])
        monthly_image_count = len([img for img in os.listdir(os.getenv("MONTHLY_FOLDER")) if img.endswith(".jpg")])
        yearly_image_count = len([img for img in os.listdir(os.getenv("YEARLY_FOLDER")) if img.endswith(".jpg")])

        # Calculate the video thresholds
        weekly_video_threshold = int(os.getenv("WEEKLY_VIDEO_THRESHOLD"))
        monthly_video_threshold = int(os.getenv("MONTHLY_VIDEO_THRESHOLD"))
        yearly_video_threshold = int(os.getenv("YEARLY_VIDEO_THRESHOLD"))

        logging.info(
            f"Total images - Daily: {daily_image_count}/{threshold}, Weekly: {weekly_image_count}/{weekly_video_threshold}, Monthly: {monthly_image_count}/{monthly_video_threshold}, Yearly: {yearly_image_count}/{yearly_video_threshold}"
        )

        # Check if the daily video threshold is met and create the video
        if daily_image_count >= threshold:
            create_video(image_folder, video_folder, threshold, delay, audio_file, "daily", constant_image_path)

        # Move the captured images and check thresholds after creating the video
        if daily_image_count >= threshold:
            # Move the captured images to weekly folder after creating daily video
            logging.info("Moving files to weekly folder...")
            weekly_folder = os.getenv("WEEKLY_FOLDER")
            for image in os.listdir(image_folder):
                img_path = os.path.join(image_folder, image)
                dst_path = os.path.join(weekly_folder, image)
                shutil.move(img_path, dst_path)
            logging.info("Files moved to weekly folder.")

            # Check if the weekly video threshold is met
            weekly_images = glob.glob(os.path.join(weekly_folder, "*.jpg"))
            if len(weekly_images) >= weekly_video_threshold:
                logging.info(f"Weekly video threshold met. Proceed to create weekly video.")
                create_video(weekly_folder, video_folder, weekly_video_threshold, weekly_video_delay, audio_file, "weekly", constant_image_path)

            # Move the captured images to monthly folder after creating weekly video
            logging.info("Moving files to monthly folder...")
            monthly_folder = os.getenv("MONTHLY_FOLDER")
            for image in weekly_images:
                img_path = os.path.join(weekly_folder, image)
                dst_path = os.path.join(monthly_folder, image)
                shutil.move(img_path, dst_path)
            logging.info("Files moved to monthly folder.")

            # Check if the monthly video threshold is met
            monthly_images = glob.glob(os.path.join(monthly_folder, "*.jpg"))
            if len(monthly_images) >= monthly_video_threshold:
                logging.info(f"Monthly video threshold met. Proceed to create monthly video.")
                create_video(monthly_folder, video_folder, monthly_video_threshold, monthly_video_delay, audio_file, "monthly", constant_image_path)

            # Move the captured images to yearly folder after creating monthly video
            logging.info("Moving files to yearly folder...")
            yearly_folder = os.getenv("YEARLY_FOLDER")
            for image in monthly_images:
                img_path = os.path.join(monthly_folder, image)
                dst_path = os.path.join(yearly_folder, image)
                shutil.move(img_path, dst_path)
            logging.info("Files moved to yearly folder.")

            # Check if the yearly video threshold is met
            yearly_images = glob.glob(os.path.join(yearly_folder, "*.jpg"))
            if len(yearly_images) >= yearly_video_threshold:
                logging.info(f"Yearly video threshold met. Proceed to create yearly video.")
                create_video(yearly_folder, video_folder, yearly_video_threshold, yearly_video_delay, audio_file, "yearly", constant_image_path)

        logging.info(f"Waiting for {sleep_duration} seconds...")
        time.sleep(sleep_duration)  # Sleep for the specified duration


if __name__ == "__main__":
    main()
