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


class StoreGCS:
    def __init__(self) -> None:
        self.client = storage.Client(project=GCS_PROJECT)
        self.gcs_bucket_name = GCS_BUCKET
        self.gcs_file_prefix = GCS_PREFIX
        self.gcs_region = GCS_REGION

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
