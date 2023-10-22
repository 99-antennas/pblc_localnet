import logging

import pandas as pd

from src.load_data import EXCLUDE_LIST, YEARS, load_all_metadata
from src.store_gcs import GCS_BUCKET, StoreGCS

# Configure logging
logging.basicConfig(level=logging.INFO)

import asyncio
import logging

import pandas as pd
from google.cloud import storage

from src.load_data import EXCLUDE_LIST, YEARS, load_cloud_metadata
from src.store_gcs import GCS_BUCKET, StoreGCS

# Configure logging
logging.basicConfig(level=logging.INFO)

FILE_PREFIX = "localnet/metadata"

# Initialize a GCS client
storage_client = storage.Client()


async def download_and_upload_metadata(year, exclude_list, bucket_name, file_prefix):
    # Download the data
    logging.info(f"Downloading data: {year}")
    try:
        data = load_cloud_metadata(year, exclude_list=exclude_list)
        data["year"] = year
    except Exception as error:
        logging.error(f"Unable to download file: {year}")
        data = pd.DataFrame({})
        data["year"] = year

    # Define the GCS object name
    gcs_object_name = f"{file_prefix}/metadata_{year}.csv"

    # Upload the data to GCS
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(gcs_object_name)
    data.to_csv(gcs_object_name, index=False)
    with open(gcs_object_name, "rb") as data_file:
        logging.info(f"Uploading data: {gcs_object_name}")
        blob.upload_from_file(data_file, content_type="application/csv")

    logging.info(
        f"Data for year {year} uploaded to GCS: gs://{bucket_name}/{gcs_object_name}"
    )
    return data


async def main():
    tasks = []
    for year in YEARS:
        task = asyncio.create_task(
            download_and_upload_metadata(year, EXCLUDE_LIST, GCS_BUCKET, FILE_PREFIX)
        )
        tasks.append(task)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
