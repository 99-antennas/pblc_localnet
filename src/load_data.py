import logging

import aiomultiprocess
import pandas as pd
from aiomultiprocess import pool

logging.basicConfig(level="INFO")
logger = logging.getLogger("__name__")

YEARS = range(2006, 2023)


def load_cloud_data(year: int, n=0):
    base_path = f"gs://pblc_data/localnet/meetings.{year}.csv"
    logger.debug("Loading file: %s", base_path)
    data = pd.read_csv(base_path, header=0, sep=",", skiprows=n)
    logger.debug("Successfully loaded data: %s", year)
    return data


def load_all(years=YEARS):
    """TODO: Run this async"""
    df_dict = {}
    # async with Pool() as pool:
    #     async for result in pool.map(get, urls):
    #         ...  # process result
    for year in years:
        data = load_cloud_data(year)
        df_dict[year] = data
        logger.info("Successfully loaded data: %s", year)
    return df_dict


if __name__ == "__main__":
    # test csv issue
    YEARS = range(2006, 2023)
    data = load_all(years=[2006, 2007])
    logger.info(data.keys())
