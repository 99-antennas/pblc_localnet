import logging
import os
import tempfile

from google.cloud import storage
from pytube import YouTube

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

VID_PREFIX = "https://www.youtube.com/watch?v="
GCS_PROJECT = "pblc"
GCS_REGION = None  # no default set
GCS_BUCKET = "pblc_data"
GCS_PREFIX = "localnet"


class VidExtract:
    def __init__(self, video_url: str, gcs_bucket_name: str, temp_dir: str):
        """
        Initialize the VidExtract object.

        Args:
            video_url (str): The URL of the YouTube video.
            gcs_bucket_name (str): The name of the Google Cloud Storage bucket.
        """
        self.video_url = video_url
        self.gcs_bucket_name = gcs_bucket_name
        self.yt = YouTube(self.video_url)
        self.client = storage.Client(project=GCS_PROJECT)
        self.gcs_bucket_name = GCS_BUCKET
        self.gcs_file_prefix = GCS_PREFIX
        self.gcs_region = GCS_REGION

        self.temp_dir = temp_dir
        if self.temp_dir:
            self._create_temp_dir()
        else:
            self.temp_dir = "."

    def _create_temp_dir(self):
        os.makedirs(self.temp_dir, exist_ok=True)

    def download_video(self):
        """
        Download the highest resolution video from YouTube.

        Returns:
            str: The local path to the downloaded video file.
        """
        stream = self.yt.streams.get_highest_resolution()
        video_title = self.yt.title.replace(" ", "_").lower()
        video_filename = f"{video_title}_vid.mp4"
        gcs_path = f"{self.gcs_file_prefix}/{video_filename}"
        with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_dir:
            output_file_path = os.path.join(temp_dir, video_filename)
            stream.download(
                output_path=temp_dir,
                filename=video_filename,
                filename_prefix=None,
                skip_existing=True,
                timeout=300,  # 6min
                max_retries=0,
            )

            logging.info(f"Downloaded video: {output_file_path}")
            gcs_file_path = self.upload_to_gcs(output_file_path, gcs_path=gcs_path)

            return output_file_path, gcs_file_path

    def extract_audio(self, video_path):
        """
        Extract audio from the downloaded video.

        Args:
            video_path (str): The local path to the downloaded video file.

        Returns:
            str: The local path to the extracted audio file.
        """
        audio = self.yt.streams.filter(only_audio=True).first()
        audio_filename = video_path.split("/")[-1].replace("_vid.mp4", "_aud.mp3")
        gcs_path = f"{self.gcs_file_prefix}/{audio_filename}"
        with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_dir:
            output_audio_path = os.path.join(temp_dir, audio_filename)
            audio.download(output_path=temp_dir, filename=audio_filename)

            logging.info(f"Extracted audio: {output_audio_path}")
            gcs_file_path = self.upload_to_gcs(output_audio_path, gcs_path=gcs_path)
            return gcs_file_path

    def upload_to_gcs(self, local_path, gcs_path):
        """
        Upload a local file to Google Cloud Storage.

        Args:
            local_path (str): The local path to the file to be uploaded.
            gcs_path (str): The destination path in Google Cloud Storage.

        Returns:
            str: The GCS path of the uploaded file.
        """
        bucket = self.client.bucket(self.gcs_bucket_name)
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)
        os.remove(local_path)
        logging.info(f"Local file {local_path} removed.")

        gcs_file_path = f"gs://{self.gcs_bucket_name}/{gcs_path}"
        logging.info(f"Uploaded to GCS: {gcs_file_path}")
        return gcs_file_path


# Example usage
if __name__ == "__main__":
    VID_ID = "JSTYbP5HvZQ"
    VID_PREFIX = "https://www.youtube.com/watch?v="
    VIDEO_URL = f"{VID_PREFIX}{VID_ID}"
    TEMP_DIR = "/tmp/localnets"

    downloader = VidExtract(
        video_url=VIDEO_URL, gcs_bucket_name=GCS_BUCKET, temp_dir=TEMP_DIR
    )

    video_path, video_gcs_path = downloader.download_video()  # Download the video
    audio_gcs_path = downloader.extract_audio(
        video_path
    )  # Extract audio from the video
    logging.info(f"Uploaded video to GCS: {video_gcs_path}")
    logging.info(f"Uploaded audio to GCS: {audio_gcs_path}")
