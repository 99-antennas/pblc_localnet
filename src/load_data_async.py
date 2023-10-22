import asyncio
import logging
from io import StringIO

import pandas as pd
from google.cloud import storage

from store_gcs import GCS_BUCKET, GCS_PREFIX, StoreGCS

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


YEARS = range(2006, 2023)
EXCLUDE_LIST = ["caption_text", "caption_text_clean"]


async def store_gcs(
    data: str,  # must be a blob
    gcs_object_name: str,
    bucket_name: str = GCS_BUCKET,
    content_type="application/csv",
):
    """
    Upload file to gcs.
    """
    try:
        logger.info(f"Uploading file {gcs_object_name} to gcs... ")
        # Initialize a GCS client
        storage_client = storage.Client()
        # Upload the data to GCS
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(gcs_object_name)
        logging.info(f"Uploading data: {gcs_object_name}")
        blob.upload_from_string(data, content_type=content_type)
        logging.info(f"Data uploaded to GCS: gs://{bucket_name}/{gcs_object_name}")
    except Exception as error:
        logger.error(f"Failed to upload file {gcs_object_name} to gcs: {error}")


async def download_cloud_data(year: int, n=0) -> pd.DataFrame:
    try:
        base_path = f"gs://pblc_data/localnet/meetings.{year}.csv"
        logger.debug("Downloading file: %s", base_path)
        data: pd.DataFrame = await asyncio.to_thread(
            pd.read_csv, base_path, header=0, sep=",", skiprows=n
        )
        logger.info("Successfully downloaded data: %s", year)
        return data
    except Exception as error:
        logging.error(f"Failed to load file: {year}: {error}")
        # Return an empty dataframe.
        return pd.DataFrame()


async def download_cloud_metadata(year: int, n=0) -> pd.DataFrame:
    try:
        base_path = f"gs://pblc_data/localnet/metadata/metadata_{year}.csv"
        logger.debug("Downloading file: %s", base_path)
        data: pd.DataFrame = await asyncio.to_thread(
            pd.read_csv, base_path, header=0, sep=",", skiprows=n
        )
        logger.info("Successfully downloaded data: %s", year)
        return data
    except Exception as error:
        # Return an empty dataframe
        logging.error(f"Failed to load file: {year}: {error}")
        return pd.DataFrame()


async def upload_cloud_metadata(
    year: int, n=0, exclude_list: list[str] = [], bucket_name=GCS_BUCKET
) -> pd.DataFrame:
    try:
        base_path = f"gs://pblc_data/localnet/meetings.{year}.csv"
        logger.info("Downloading file: %s", base_path)
        headers = [*pd.read_csv(base_path, nrows=1)]
        data: pd.DataFrame = await asyncio.to_thread(
            pd.read_csv,
            base_path,
            header=0,
            sep=",",
            skiprows=n,
            usecols=[c for c in headers if c not in exclude_list],
        )
        # Convert to .csv
        csv_string = data.to_csv(index=False)
        gcs_object_name = f"{GCS_PREFIX}/metadata/metadata_{year}.csv"
        await store_gcs(
            data=csv_string,
            gcs_object_name=gcs_object_name,
            bucket_name=bucket_name,
            content_type="application/csv",
        )
        logger.info("Successfully loaded data: %s", year)
        return data
    except Exception as error:
        logging.error(f"Failed to load file: {year}: {error}")
        # Return an empty dataframe
        return pd.DataFrame()


async def upload_and_combine_metadata(years, exclude_list, bucket_name=GCS_BUCKET):
    """
    Downloads and combines metadata for all years. Returns a combined
    dataframe of all years.
    """
    try:
        logger.info("Loading metadata for all years... ")
        df_list = await asyncio.gather(
            *[upload_cloud_metadata(year, exclude_list=exclude_list) for year in years]
        )
        results = pd.concat(df_list, ignore_index=True)
        logger.info("Completed combining metadata... ")
        csv_string = results.to_csv(index=False)
        gcs_object_name = f"{GCS_PREFIX}/metadata/metadata_all_years.csv"
        await store_gcs(
            data=csv_string,
            gcs_object_name=gcs_object_name,
            bucket_name=bucket_name,
            content_type="application/csv",
        )
        logger.info("Successfully uploaded combined metadata: %s", gcs_object_name)
        return results
    except Exception as error:
        logger.error(f"Failed to combine metadata: {error}")
        return pd.DataFrame()


async def download_all(years):
    """
    Returns a dictionary of dataframes; one for each year.
    """
    df_dict = {}

    # Use asyncio.gather to download data for multiple years concurrently
    tasks = [download_cloud_data(year) for year in years]
    downloaded_data = await asyncio.gather(*tasks)

    # Assign the downloaded data to the dictionary using years as keys
    for year, data in zip(years, downloaded_data):
        df_dict[year] = data

    return df_dict


if __name__ == "__main__":
    # asyncio.run(upload_and_combine_metadata(years=YEARS,
    # exclude_list=EXCLUDE_LIST))
    result = asyncio.run(download_all(years=[2006, 2007]))
    logger.info("Downloaded years: %s", result.keys())
