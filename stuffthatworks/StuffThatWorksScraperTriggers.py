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


def get_symptoms(condition):
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(
        "/Users/samsavage/Downloads/chromedriver_mac_arm64/chromedriver",
        options=chrome_options,
    )

    value = condition

    driver.get(f"https://www.stuffthatworks.health/{value}/triggers?tab=MostReported")

    print(f"found {value} most tried page scraping")
    # try:
    time.sleep(2)
    try:
        if driver.execute_script(
            "return document.querySelectorAll(\"[class*='more-result-button']\")[0];"
        ).is_displayed():
            click_counter = 0
            for i in range(0, 10):
                try:
                    time.sleep(2)
                    driver.execute_script(
                        "document.querySelectorAll(\"[class*='more-result-button']\")[0].click();"
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
            "return document.querySelectorAll(\"[class*='more-result-button']\")[1];"
        ).is_displayed():
            click_counter = 0
            for i in range(0, 10):
                try:
                    time.sleep(2)
                    driver.execute_script(
                        "document.querySelectorAll(\"[class*='more-result-button']\")[1].click();"
                    )
                    click_counter += 1
                    print(f"clicking {click_counter} times")
                except:
                    continue
        else:
            tiles = driver.execute_script(
                "return document.querySelectorAll(\"[class*='normalized-entity']\");"
            )
    except:
        print("no extra conditions")

    tiles = driver.execute_script(
        "return document.querySelectorAll(\"[class*='normalized-entity']\");"
    )
    time.sleep(2)

    print(f"length of tiles ======= {len(tiles)}")

    ranking_list = []
    symptoms_list = []
    num_reports_list = []
    condition_list = []

    pattern = r"^(#\d{1,2})([A-Za-z\s]+)(\d+)\s(reports)$"

    for tile in tiles:
        match = re.match(pattern, tile.get_attribute("textContent"))

        if match:
            ranking = match.group(1)
            condition = match.group(2)
            num_reports = match.group(3)

            print(f"Ranking: {ranking}")
            print(f"Condition: {condition}")
            print(f"Number of Reports: {num_reports}")
        else:
            print("No match found")
            ranking = None
            condition = None
            num_reports = None

        ranking_list.append(ranking)
        condition_list.append(value)
        symptoms_list.append(condition)
        num_reports_list.append(num_reports)

    df = pd.DataFrame(
        {
            "rankings": ranking_list,
            "triggers": symptoms_list,
            "conditions": condition_list,
            "num_reports": num_reports_list,
            "TimeScraped": datetime.datetime.now(),
            "DateScraped": datetime.datetime.today().strftime("%m/%d/%Y"),
        }
    )
    return df


def get_conditions():
    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"

    key_path = "/Users/samsavage/NHIB Scraper/airflow-test-371320-dad1bdc01d6f.json"

    creds = Credentials.from_service_account_file(key_path)

    client = bigquery.Client(credentials=creds, project=project_name)

    query = f"""with all_conditions as (
                                    SELECT DISTINCT conditions
                                    FROM `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_TRIGGERS`
                                    UNION DISTINCT
                                    SELECT DISTINCT conditions
                                    FROM `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_SYMPTOMS`
                                    UNION DISTINCT
                                    SELECT DISTINCT conditions
                                    FROM `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_TREATMENTS`
                                    UNION DISTINCT
                                    SELECT DISTINCT conditions
                                    FROM `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_COMORBIDITIES`)
                                    Select conditions from all_conditions"""

    query_job = client.query(query)

    results = query_job.result().to_dataframe()
    sql_conditions = results["conditions"].to_list()
    results = sql_conditions + [
        "Addison's disease",
        "Atherosclerosis",
        "Barrett's esophagus",
        "Benign prostatic hyperplasia (BPH)",
        "Bruxism",
        "Cardiomyopathy",
        "Carpal tunnel syndrome",
        "Charcot-Marie-Tooth disease",
        "Chronic bronchitis",
        "Chronic fatigue syndrome (CFS)",
        "Chronic obstructive pulmonary disease (COPD)",
        "Chronic sinusitis",
        "Congestive heart failure",
        "Cystic fibrosis",
        "Emphysema",
        "Endometriosis",
        "Essential tremor",
        "Fatty liver disease",
        "Gastroesophageal reflux disease (GERD)",
        "Graves disease",
        "Hypertension (high blood pressure)",
        "Hyperthyroidism",
        "Hypothyroidism",
        "Inflammatory bowel disease (IBD)",
        "Insomnia",
        "Interstitial cystitis",
        "Irritable bowel syndrome (IBS)",
        "Kidney stones",
        "Ménière's disease",
        "Multiple system atrophy (MSA)",
        "Myasthenia gravis",
        "Narcolepsy",
        "Obstructive sleep apnea",
        "Osteoarthritis",
        "Paget's disease of bone",
        "Parkinson's disease",
        "Pelvic inflammatory disease (PID)",
        "Peripheral neuropathy",
        "Peyronie's disease",
        "Pityriasis rosea",
        "Polycystic ovary syndrome (PCOS)",
        "Postural orthostatic tachycardia syndrome (POTS)",
        "Primary biliary cirrhosis (PBC)",
        "Primary sclerosing cholangitis (PSC)",
        "Pulmonary fibrosis",
        "Raynaud's phenomenon",
        "Restless legs syndrome (RLS)",
        "Rheumatic fever",
        "Sarcoidosis",
        "Sjögren's syndrome",
        "Sleep apnea",
        "Spondyloarthritis",
        "Tinnitus",
        "Trigeminal neuralgia",
        "Ulcerative colitis",
        "Urinary incontinence",
        "Varicose veins",
        "Vitiligo",
        "Achalasia",
        "Acromegaly",
        "Adrenoleukodystrophy",
        "Agoraphobia",
        "Alopecia areata",
        "Amyloidosis",
        "Ankylosing spondylitis",
        "Aortic aneurysm",
        "Aplastic anemia",
        "Arnold-Chiari malformation",
        "Atrial fibrillation",
        "Avascular necrosis",
        "Behçet's disease",
        "Bile duct cancer",
        "Bladder cancer",
        "Blepharitis",
        "Buerger's disease",
        "Bullous pemphigoid",
        "Cachexia",
        "Cardiac arrhythmia",
        "Celiac disease",
        "Chagas disease",
        "Charcot foot",
        "Cholangitis",
        "Cholestasis",
        "Chondromalacia patellae",
        "Chronic granulomatous disease",
        "Chronic lymphocytic leukemia",
        "Chronic myelogenous leukemia",
        "Chronic pancreatitis",
        "Chronic venous insufficiency",
        "Colitis",
        "Complex regional pain syndrome (CRPS)",
        "Cystinuria",
        "Dercum's disease",
        "Dermatitis herpetiformis",
        "Diabetic neuropathy",
        "Diffuse idiopathic skeletal hyperostosis (DISH)",
        "Diverticulosis",
        "Dry eye syndrome",
        "Dupuytren's contracture",
        "Dysautonomia",
        "Eczema",
        "Ehlers-Danlos syndrome",
        "Endometrial cancer",
        "Eosinophilic esophagitis",
        "Epidermolysis bullosa",
        "Erythema multiforme",
        "Essential thrombocythemia",
        "Familial hypercholesterolemia",
        "Fanconi anemia",
        "Felty syndrome",
        "Focal segmental glomerulosclerosis",
        "Friedreich's ataxia",
        "Gaucher disease",
        "Giant cell arteritis",
        "Granulomatosis with polyangiitis",
        "Hemochromatosis",
        "Hereditary angioedema",
        "Hereditary hemorrhagic telangiectasia",
        "Hidradenitis suppurativa",
        "Horner's syndrome",
        "Huntington's disease",
        "Hydrocephalus",
        "Hydronephrosis",
        "Hyperparathyroidism",
        "Hypertrophic cardiomyopathy",
        "Hypoparathyroidism",
        "Idiopathic intracranial hypertension",
        "Idiopathic pulmonary fibrosis",
        "Inclusion body myositis",
        "Interstitial cystitis",
        "Kawasaki disease",
        "Klinefelter syndrome",
        "Lichen planus",
        "Lichen sclerosus",
        "Lymphedema",
        "Malignant hyperthermia",
        "Mastocytosis",
        "Ménière's disease",
        "Mitral valve prolapse",
        "Moyamoya disease",
        "Multiple endocrine neoplasia",
        "Myelodysplastic syndromes",
        "Myelofibrosis",
        "Myositis",
        "Nail patella syndrome",
        "Nephrotic syndrome",
        "Neurofibromatosis",
        "Neutropenia",
        "Non-alcoholic fatty liver disease (NAFLD)",
        "Osteogenesis imperfecta",
        "Pemphigus",
    ]

    # Extract the PMIDs from the results
    return results


def insert_dataframe_into_table(df):
    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"
    dataset_name = "DEV"
    table_id = f"{dataset_name}.STUFF_THAT_WORKS_TRIGGERS_DEV"
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
    results = get_conditions()

    results = list(set(results))

    print(f"We are scraping for:{len(results)} conditions")

    for condition in results:
        try:
            counter_for_me = 0
            treatments_frame = get_symptoms(condition)
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


# new_list = []
#     dfs = []

#     list_of_keywords = read_text_file()

#     for i in set(list(list_of_keywords)):

#         i = ast.literal_eval(i)

#         for value in i:
#             new_list.append(value)

#         new_list = list(set(new_list))

#     ll = len(new_list)
#     counter = 0
