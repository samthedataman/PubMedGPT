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


def get_side_effects(condition, treatment):
    scraped_data = {
        "condition": f"{condition}",
        "treatment": f"{treatment}",
        "brand_names": [],
        "member_reports": [],
        "drug_disease_description": [],
        "most_tried": [],
        "most_effective": [],
        "most_detrimental": [],
        "other_treatment_counts": [],
        "effectiveness_reports_percentage": [],
        "effectiveness_reports_detrimental_percentage": [],
        "member_treatment_quotes": [],
        "sideeffects": [],
        "oftencombinedlist": [],
    }

    chrome_options = Options()
    # chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(
        "/Users/samsavage/Downloads/chromedriver_mac_arm64 (1)/chromedriver",
        options=chrome_options,
    )

    driver.get(f"https://www.stuffthatworks.health/{condition}/treatments/{treatment}")

    print(f"getting static meta-data for {condition}:::{treatment} pair")

    time.sleep(1)
    # Execute script to get brand names
    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='treatment-title-brands']\")[0]"
    ):
        scraped_data["brand_names"].append(
            driver.execute_script(
                "return document.querySelectorAll(\"[class*='treatment-title-brands']\")[0]"
            ).get_attribute("innerText")
        )
    else:
        scraped_data["brand_names"].append("")

    print(scraped_data["brand_names"])

    # Execute script to get member reports
    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='report-number']\")[0]"
    ):
        scraped_data["member_reports"] = driver.execute_script(
            "return document.querySelectorAll(\"[class*='report-number']\")[0]"
        ).get_attribute("innerText")
    else:
        scraped_data["member_reports"].append(None)

    print(scraped_data["member_reports"])

    # Append drug disease description to the dictionary
    scraped_data["drug_disease_description"].append(
        driver.execute_script(
            "return document.querySelectorAll(\"[class*='treatment-description']\")[0]"
        ).get_attribute("innerText")
    )

    print(scraped_data["drug_disease_description"])
    # Append most tried count to the dictionary

    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='entity-ranking-rank tried tried-with-detrimental']\")[0]"
    ):
        scraped_data["most_tried"].append(
            driver.execute_script(
                "return document.querySelectorAll(\"[class*='entity-ranking-rank tried tried-with-detrimental']\")[0]"
            ).get_attribute("innerText")
        )
    else:
        scraped_data["most_tried"].append("")

    print(scraped_data["most_tried"])
    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='entity-ranking-rank effective']\")[0]"
    ):
        # Append most effective count to the dictionary
        scraped_data["most_effective"].append(
            driver.execute_script(
                "return document.querySelectorAll(\"[class*='entity-ranking-rank effective']\")[0]"
            ).get_attribute("innerText")
        )

    print(scraped_data["most_effective"])

    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='entity-ranking-rank show-border-top']\")[0]"
    ):
        # Append most detrimental count to the dictionary
        scraped_data["most_detrimental"].append(
            driver.execute_script(
                "return document.querySelectorAll(\"[class*='entity-ranking-rank show-border-top']\")[0]"
            ).get_attribute("innerText")
        )
    else:
        scraped_data["most_detrimental"].append("")

    print(scraped_data["most_detrimental"])

    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='stw-card cross-condition-entity-link']\")[0]"
    ):
        # Append other treatment counts to the dictionary
        scraped_data["other_treatment_counts"].append(
            driver.execute_script(
                "return document.querySelectorAll(\"[class*='stw-card cross-condition-entity-link']\")[0]"
            ).get_attribute("innerText")
        )
    else:
        scraped_data["other_treatment_counts"].append("")

    print(scraped_data["other_treatment_counts"])

    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='treatment-effectiveness']\")[0]"
    ):
        # Append effectiveness reports percentage to the dictionary
        scraped_data["effectiveness_reports_percentage"].append(
            driver.execute_script(
                "return document.querySelectorAll(\"[class*='treatment-effectiveness']\")[0]"
            ).get_attribute("innerText")
        )
    else:
        scraped_data["effectiveness_reports_percentage"].append("")

    print(scraped_data["effectiveness_reports_percentage"])

    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='treatment-effectiveness detrimental']\")[0]"
    ):
        # Append effectiveness reports detrimental percentage to the dictionary
        scraped_data["effectiveness_reports_detrimental_percentage"].append(
            driver.execute_script(
                "return document.querySelectorAll(\"[class*='treatment-effectiveness detrimental']\")[0]"
            ).get_attribute("innerText")
        )
    else:
        scraped_data["effectiveness_reports_detrimental_percentage"].append("")

    print(scraped_data["effectiveness_reports_detrimental_percentage"])

    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='stw-card quotes-card']\")[0]"
    ):
        # Append member treatment quotes to the dictionary
        scraped_data["member_treatment_quotes"].append(
            driver.execute_script(
                "return document.querySelectorAll(\"[class*='stw-card quotes-card']\")[0]"
            ).get_attribute("innerText")
        )
    else:
        scraped_data["member_treatment_quotes"].append("")

    print(scraped_data["member_treatment_quotes"])

    print(f"scraping the hard stuff for {condition}")
    # Append side effects to the dictionary
    if driver.execute_script(
        "return document.querySelectorAll(\"[class*='show-more-button']\")[0];"
    ).is_displayed():
        print("displayed")
        click_counter = 0
        for i in range(0, 10):
            try:
                time.sleep(2)
                driver.execute_script(
                    "document.querySelectorAll(\"[class*='show-more-button']\")[0].click();"
                )
                click_counter += 1
                print(f"clicking {click_counter} times")
            except:
                continue

        if driver.execute_script(
            "return document.querySelectorAll(\"[class*='treatment-side-effect-row']\")"
        ):
            scraped_data["sideeffects"].append(
                driver.execute_script(
                    "return document.querySelectorAll(\"[class*='treatment-side-effect-row']\")[0]"
                ).get_attribute("innerText")
            )
        else:
            scraped_data["sideeffects"].append("")

        # Append often combined list to the dictionary
        try:
            if driver.execute_script(
                "return document.querySelectorAll(\"[class*='View More']\")[0]"
            ).is_displayed():
                click_counter = 0
                for i in range(0, 10):
                    try:
                        time.sleep(2)
                        driver.execute_script(
                            "return document.querySelectorAll(\"[class*='View More']\")[0].click();"
                        )
                        click_counter += 1

                        print(f"clicking {click_counter} times")
                    except:
                        continue
        except:
            pass

            if driver.execute_script(
                "return document.querySelectorAll(\"[class*='combination']\")[0];"
            ):
                scraped_data["oftencombinedlist"].append(
                    driver.execute_script(
                        "return document.querySelectorAll(\"[class*='combination']\")[0]"
                    ).get_attribute("innerText")
                )
            else:
                scraped_data["oftencombinedlist"].append("")

        print(scraped_data)

    return pd.DataFrame(scraped_data)


df = get_side_effects("ankylosing-spondylitis", "exercise")


# def get_treatments(condition):
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")

#     driver = webdriver.Chrome(
#         "/Users/samsavage/Downloads/chromedriver_mac_arm64/chromedriver",
#         options=chrome_options,
#     )

#     value = condition
#     driver.get(
#         f"https://www.stuffthatworks.health/{value}/treatments?tab=MostEffective"
#     )
#     print(f"found {value} most tried page scraping")
#     # try:
#     time.sleep(2)
#     try:
#         if driver.execute_script(
#             "return document.querySelectorAll(\"[class*='view-more-wrapper']\")[0];"
#         ).is_displayed():
#             click_counter = 0
#             for i in range(0, 10):
#                 try:
#                     time.sleep(2)
#                     driver.execute_script(
#                         "document.querySelectorAll(\"[class*='view-more-wrapper']\")[0].click();"
#                     )
#                     click_counter += 1
#                     print(f"clicking {click_counter} times")
#                 except:
#                     continue
#         else:
#             print("click moving on to second clicker")
#     except:
#         pass
#     ###################################
#     try:
#         if driver.execute_script(
#             "return document.querySelectorAll(\"[class*='view-more-wrapper']\")[1];"
#         ).is_displayed():
#             click_counter = 0
#             for i in range(0, 10):
#                 try:
#                     time.sleep(2)
#                     driver.execute_script(
#                         "document.querySelectorAll(\"[class*='view-more-wrapper']\")[1].click();"
#                     )
#                     click_counter += 1
#                     print(f"clicking {click_counter} times")
#                 except:
#                     continue
#         else:
#             tile_list = []
#             tiles = driver.execute_script(
#                 "return document.querySelectorAll(\"[class*='treatment-view-row']\");"
#             )
#     except:
#         print("no extra conditions")

#     tiles = driver.execute_script(
#         "return document.querySelectorAll(\"[class*='treatment-view-row']\");"
#     )

#     time.sleep(2)

#     print(f"length of tiles ======= {len(tiles)}")
#     ranking_list = []
#     treatments_list = []
#     num_reports_list = []
#     conditions_list = []
#     treatment_type_list = []

#     pattern = r"^#(\d+)(.*?)(\d+)\s+reports(?:\s*(\d+)%?)?$"

#     for tile in tiles:
#         match = re.match(pattern, tile.get_attribute("textContent"))

#         if match:
#             ranking = match.group(1)
#             treatments = match.group(2)
#             num_reports = match.group(3)
#             percentage = match.group(4)
#             print(f"Ranking: {ranking}")
#             print(f"Treatments: {treatments}")
#             print(f"Number of Reports: {num_reports}")

#             if percentage:
#                 good_or_bad_treatment = "Detrimental"
#             else:
#                 good_or_bad_treatment = "Beneficial"
#         else:
#             print("No match found")
#             ranking = None
#             treatments = None
#             num_reports = None
#             good_or_bad_treatment = None

#         treatment_type_list.append(good_or_bad_treatment)
#         ranking_list.append(ranking)
#         treatments_list.append(treatments)
#         num_reports_list.append(num_reports)
#         conditions_list.append(value)

#     df = pd.DataFrame(
#         {
#             "rankings": ranking_list,
#             "treatments": treatments_list,
#             "num_reports": num_reports_list,
#             "conditions": conditions_list,
#             "TreatmentType": treatment_type_list,
#             "TimeScraped": datetime.datetime.now(),
#             "DateScraped": datetime.datetime.today().strftime("%m/%d/%Y"),
#         }
#     )
#     return df


# def read_text_file():
#     with open("/Users/samsavage/NHIB Scraper/list_chronic_conditions.txt", "r") as file:
#         # Read the lines of the file into a list, stripping any newline characters
#         read_list = [line.strip() for line in file]
#         read_list = list(set(read_list))
#     return read_list


# def get_conditions():
#     # Instantiate a client object using credentials
#     project_name = "airflow-test-371320"

#     key_path = "/Users/samsavage/NHIB Scraper/airflow-test-371320-dad1bdc01d6f.json"

#     creds = Credentials.from_service_account_file(key_path)

#     client = bigquery.Client(credentials=creds, project=project_name)

#     query = f"""with all_conditions as (
#                                     SELECT DISTINCT conditions
#                                     FROM `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_TRIGGERS`
#                                     UNION DISTINCT
#                                     SELECT DISTINCT conditions
#                                     FROM `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_SYMPTOMS`
#                                     UNION DISTINCT
#                                     SELECT DISTINCT conditions
#                                     FROM `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_TREATMENTS`
#                                     UNION DISTINCT
#                                     SELECT DISTINCT conditions
#                                     FROM `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_COMORBIDITIES`)
#                                     Select conditions from all_conditions"""

#     query_job = client.query(query)

#     results = query_job.result().to_dataframe()
#     sql_conditions = results["conditions"].to_list()
#     results = sql_conditions + [
#         "Addison's disease",
#         "Atherosclerosis",
#         "Barrett's esophagus",
#         "Benign prostatic hyperplasia (BPH)",
#         "Bruxism",
#         "Cardiomyopathy",
#         "Carpal tunnel syndrome",
#         "Charcot-Marie-Tooth disease",
#         "Chronic bronchitis",
#         "Chronic fatigue syndrome (CFS)",
#         "Chronic obstructive pulmonary disease (COPD)",
#         "Chronic sinusitis",
#         "Congestive heart failure",
#         "Cystic fibrosis",
#         "Emphysema",
#         "Endometriosis",
#         "Essential tremor",
#         "Fatty liver disease",
#         "Gastroesophageal reflux disease (GERD)",
#         "Graves disease",
#         "Hypertension (high blood pressure)",
#         "Hyperthyroidism",
#         "Hypothyroidism",
#         "Inflammatory bowel disease (IBD)",
#         "Insomnia",
#         "Interstitial cystitis",
#         "Irritable bowel syndrome (IBS)",
#         "Kidney stones",
#         "Ménière's disease",
#         "Multiple system atrophy (MSA)",
#         "Myasthenia gravis",
#         "Narcolepsy",
#         "Obstructive sleep apnea",
#         "Osteoarthritis",
#         "Paget's disease of bone",
#         "Parkinson's disease",
#         "Pelvic inflammatory disease (PID)",
#         "Peripheral neuropathy",
#         "Peyronie's disease",
#         "Pityriasis rosea",
#         "Polycystic ovary syndrome (PCOS)",
#         "Postural orthostatic tachycardia syndrome (POTS)",
#         "Primary biliary cirrhosis (PBC)",
#         "Primary sclerosing cholangitis (PSC)",
#         "Pulmonary fibrosis",
#         "Raynaud's phenomenon",
#         "Restless legs syndrome (RLS)",
#         "Rheumatic fever",
#         "Sarcoidosis",
#         "Sjögren's syndrome",
#         "Sleep apnea",
#         "Spondyloarthritis",
#         "Tinnitus",
#         "Trigeminal neuralgia",
#         "Ulcerative colitis",
#         "Urinary incontinence",
#         "Varicose veins",
#         "Vitiligo",
#         "Achalasia",
#         "Acromegaly",
#         "Adrenoleukodystrophy",
#         "Agoraphobia",
#         "Alopecia areata",
#         "Amyloidosis",
#         "Ankylosing spondylitis",
#         "Aortic aneurysm",
#         "Aplastic anemia",
#         "Arnold-Chiari malformation",
#         "Atrial fibrillation",
#         "Avascular necrosis",
#         "Behçet's disease",
#         "Bile duct cancer",
#         "Bladder cancer",
#         "Blepharitis",
#         "Buerger's disease",
#         "Bullous pemphigoid",
#         "Cachexia",
#         "Cardiac arrhythmia",
#         "Celiac disease",
#         "Chagas disease",
#         "Charcot foot",
#         "Cholangitis",
#         "Cholestasis",
#         "Chondromalacia patellae",
#         "Chronic granulomatous disease",
#         "Chronic lymphocytic leukemia",
#         "Chronic myelogenous leukemia",
#         "Chronic pancreatitis",
#         "Chronic venous insufficiency",
#         "Colitis",
#         "Complex regional pain syndrome (CRPS)",
#         "Cystinuria",
#         "Dercum's disease",
#         "Dermatitis herpetiformis",
#         "Diabetic neuropathy",
#         "Diffuse idiopathic skeletal hyperostosis (DISH)",
#         "Diverticulosis",
#         "Dry eye syndrome",
#         "Dupuytren's contracture",
#         "Dysautonomia",
#         "Eczema",
#         "Ehlers-Danlos syndrome",
#         "Endometrial cancer",
#         "Eosinophilic esophagitis",
#         "Epidermolysis bullosa",
#         "Erythema multiforme",
#         "Essential thrombocythemia",
#         "Familial hypercholesterolemia",
#         "Fanconi anemia",
#         "Felty syndrome",
#         "Focal segmental glomerulosclerosis",
#         "Friedreich's ataxia",
#         "Gaucher disease",
#         "Giant cell arteritis",
#         "Granulomatosis with polyangiitis",
#         "Hemochromatosis",
#         "Hereditary angioedema",
#         "Hereditary hemorrhagic telangiectasia",
#         "Hidradenitis suppurativa",
#         "Horner's syndrome",
#         "Huntington's disease",
#         "Hydrocephalus",
#         "Hydronephrosis",
#         "Hyperparathyroidism",
#         "Hypertrophic cardiomyopathy",
#         "Hypoparathyroidism",
#         "Idiopathic intracranial hypertension",
#         "Idiopathic pulmonary fibrosis",
#         "Inclusion body myositis",
#         "Interstitial cystitis",
#         "Kawasaki disease",
#         "Klinefelter syndrome",
#         "Lichen planus",
#         "Lichen sclerosus",
#         "Lymphedema",
#         "Malignant hyperthermia",
#         "Mastocytosis",
#         "Ménière's disease",
#         "Mitral valve prolapse",
#         "Moyamoya disease",
#         "Multiple endocrine neoplasia",
#         "Myelodysplastic syndromes",
#         "Myelofibrosis",
#         "Myositis",
#         "Nail patella syndrome",
#         "Nephrotic syndrome",
#         "Neurofibromatosis",
#         "Neutropenia",
#         "Non-alcoholic fatty liver disease (NAFLD)",
#         "Osteogenesis imperfecta",
#         "Pemphigus",
#     ]

#     # Extract the PMIDs from the results
#     return results


# def insert_dataframe_into_table(df):
#     # Instantiate a client object using credentials
#     project_name = "airflow-test-371320"
#     dataset_name = "DEVL"
#     table_id = f"{dataset_name}.STUFF_THAT_WORKS_TREATMENTS_DEV"
#     key_path = "/Users/samsavage/NHIB Scraper/airflow-test-371320-dad1bdc01d6f.json"
#     creds = Credentials.from_service_account_file(key_path)
#     client = bigquery.Client(credentials=creds, project=project_name)

#     pandas_gbq.to_gbq(
#         df,
#         table_id,
#         project_id="airflow-test-371320",
#         if_exists="append",
#         credentials=creds,
#         chunksize=None,
#     )


# def push_treatment_data_to_gbq():
#     results = get_conditions()

#     results = list(set(results))

#     print(f"We are scraping for:{len(results)} conditions")

#     for condition in results:
#         try:
#             counter_for_me = 0
#             treatments_frame = get_treatments(condition)
#             counter_for_me += 1
#             if len(treatments_frame) > 0:
#                 print(len(treatments_frame))
#                 insert_dataframe_into_table(treatments_frame)

#                 print(
#                     f"We are ::::::{((counter_for_me/len(results))*100)}:::::completed"
#                 )
#             else:
#                 print(f"frame is empty for {condition}")
#             print(f"finish with {condition}!!!")
#         except Exception as e:
#             print(f"{condition} was {e} not valid moving on")
#             continue
