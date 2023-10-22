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


def load_cloud_metadata(year: int, n=0, exclude_list: list[str] = []):
    base_path = f"gs://pblc_data/localnet/meetings.{year}.csv"
    logger.debug("Loading file: %s", base_path)
    headers = [*pd.read_csv("sample.csv", nrows=1)]
    data = pd.read_csv(
        base_path,
        header=0,
        sep=",",
        skiprows=n,
        usecols=[c for c in headers if c not in exclude_list],
    )
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


EXCLUDE_LIST = []


def load_metadata(years=YEARS, exclude_list=EXCLUDE_LIST):
    """TODO: Run this async"""
    df_dict = {}
    #  async with Pool() as pool:
    #     async for result in pool.map(get, urls):
    #         ...  # process result
    for year in years:
        data = load_cloud_metadata(year, exclude_list=exclude_list)
        df_dict[year] = data
        logger.info("Successfully loaded data: %s", year)
    return df_dict


if __name__ == "__main__":
    # test csv issue
    YEARS = range(2006, 2023)
    data = load_all(years=range(2006, 2007))  # [2006, 2007] also works just fine.
    logger.info(data.keys())
