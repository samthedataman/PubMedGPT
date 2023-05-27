import requests
from typing import Any, Dict, List, Optional, TypedDict
import pprint
from selenium import webdriver
import ast
import time
import pandas as pd
import re
import datetime
import json
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import pandas as pd
import openai
import os
import pandas_gbq
import streamlit as st
from selenium.webdriver.chrome.options import Options
from conditionslist import diseaseslist


def get_treatments(condition):
    print(condition)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(
        "/Users/samsavage/Downloads/chromedriver_mac_arm64 (1)/chromedriver",
        options=chrome_options,
    )

    driver.get(f"https://www.stuffthatworks.health/{condition}/treatments?tab=MostEffective")

    print(f"found {condition} most tried page scraping")

    time.sleep(2)
    try:
        if driver.execute_script(
            "return document.querySelectorAll(\"[class*='view-more-wrapper']\")[0];"
        ).is_displayed():
            click_counter = 0
            for i in range(0, 10):
                try:
                    time.sleep(2)
                    driver.execute_script(
                        "document.querySelectorAll(\"[class*='view-more-wrapper']\")[0].click();"
                    )
                    click_counter += 1
                    print(f"clicking {click_counter} times")
                except:
                    continue
        else:
            print("click moving on to second clicker")
    except:
        pass
    ###################################
    try:
        if driver.execute_script(
            "return document.querySelectorAll(\"[class*='view-more-wrapper']\")[1];"
        ).is_displayed():
            click_counter = 0
            for i in range(0, 10):
                try:
                    time.sleep(2)
                    driver.execute_script(
                        "document.querySelectorAll(\"[class*='view-more-wrapper']\")[1].click();"
                    )
                    click_counter += 1
                    print(f"clicking {click_counter} times")
                except:
                    continue
        else:
            tile_list = []
            tiles = driver.execute_script(
                "return document.querySelectorAll(\"[class*='treatment-view-row']\");"
            )
    except:
        print("no extra conditions")

    tiles = driver.execute_script(
        "return document.querySelectorAll(\"[class*='treatment-view-row']\");"
    )
    time.sleep(2)

    print(f"length of tiles ======= {len(tiles)}")
    ranking_list = []
    treatments_list = []
    num_reports_list = []
    conditions_list = []
    treatment_type_list = []

    pattern = r"^#(\d+)(.*?)(\d+)\s+reports(?:\s*(\d+)%?)?$"

    for tile in tiles:
        match = re.match(pattern, tile.get_attribute("textContent"))

        if match:
            ranking = match.group(1)
            treatments = match.group(2)
            num_reports = match.group(3)
            percentage = match.group(4)
            print(f"Ranking: {ranking}")
            print(f"Treatments: {treatments}")
            print(f"Number of Reports: {num_reports}")

            if percentage:
                good_or_bad_treatment = "Detrimental"
            else:
                good_or_bad_treatment = "Beneficial"
        else:
            print("No match found")
            ranking = None
            treatments = None
            num_reports = None
            good_or_bad_treatment = None

        treatment_type_list.append(good_or_bad_treatment)
        ranking_list.append(ranking)
        treatments_list.append(treatments)
        num_reports_list.append(num_reports)
        conditions_list.append(condition)

    df = pd.DataFrame(
        {
            "rankings": ranking_list,
            "treatments": treatments_list,
            "num_reports": num_reports_list,
            "conditions": conditions_list,
            "TreatmentType": treatment_type_list,
            "TimeScraped": datetime.datetime.now(),
            "DateScraped": datetime.datetime.today().strftime("%m/%d/%Y"),
        }
    )
    return df


def insert_dataframe_into_table(df):
    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"
    dataset_name = "DEV"
    table_id = f"{dataset_name}.STUFF_THAT_WORKS_TREATMENTS_DEV_FULL"
    key_path = "/Users/samsavage/NHIB Scraper/airflow-test-371320-dad1bdc01d6f.json"
    creds = Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)

    pandas_gbq.to_gbq(
        df,
        table_id,
        project_id="airflow-test-371320",
        if_exists="append",
        credentials=creds,
        chunksize=None,
    )


def push_treatment_data_to_gbq():
    df = pd.read_csv("/Users/samsavage/PythonProjects/PubMedGPT/full_frame.csv")

    print(df.head().T)

    results = df["urlId"].unique()

    print(f"We are scraping for:{len(results)} conditions")

    for condition in results:
        print(condition)
        try:
            counter_for_me = 0
            treatments_frame = get_treatments(condition)
            counter_for_me += 1
            if len(treatments_frame) > 0:
                print(len(treatments_frame))
                insert_dataframe_into_table(treatments_frame)

                print(
                    f"We are ::::::{((counter_for_me/len(results))*100)}:::::completed"
                )
            else:
                print(f"frame is empty for {condition}")
            print(f"finish with {condition}!!!")
        except Exception as e:
            print(f"{condition} was {e} not valid moving on")
            continue


push_treatment_data_to_gbq()
