# note - the  latest, app.py uses deprecated selenium

import requests
from xml.etree import ElementTree
import pandas as pd
import json
import os
import regex as re
from google.cloud import bigquery
from airflow.contrib.hooks import *

# initialize the client with the service account key file
from google.cloud import bigquery
import pandas as pd
import numpy as np
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
import urllib3

urllib3.disable_warnings()


import requests


def parse_xml_data(response):
    try:
        xml_data = response.text
        root = ElementTree.fromstring(xml_data)
        # process the XML data
        # ...
    except ElementTree.ParseError as error:
        print(f"Failed to parse XML data: {error}")
        # handle the error as appropriate


def extract_text(regexer):
    if regexer:
        text_between = regexer.group(1)
    else:
        text_between = ""
    return text_between


def extract_date(regexer):

    if regexer:
        year_text = str(regexer.group(1))
        month_text = str(regexer.group(2))
        day_text = str(regexer.group(3))
        full_date = str(year_text + "/" + month_text + "/" + day_text)
        # full_date = datetime.datetime.strptime(full_date, '%Y/%b/%d').strftime("%Y-%m-%d")
    else:
        full_date = ""
    return full_date


def search_pmids(condition):
    """
    Search the PubMed database for articles related to a specific condition and return a list of PMIDs.
    """
    # Send the search request to the Entrez API
    import requests

    # Specify the condition and the number of results to retrieve
    condition = condition
    global num_results
    num_results = 200

    # Build the Entrez API query
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
    # query = f"db=pubmed&term={condition}&retmax={num_results}&sort=pubdate&sortdir=desc"
    query = f"db=pubmed&term={condition}+Meta-Analysis[pt]&retmax={num_results}&sort=pubdate&sortdir=desc&api_key=1f93c5a0c91e90f6c0d0fae4178c2e9ae309"
    # Send the API request and retrieve the XML response
    response = requests.get(base_url + query, verify=False)

    try:
        xml_data = response.text
    except ElementTree.ParseError as error:
        print(f"Failed to parse XML data: {error}")
        xml_data = None

    # Parse the XML data to retrieve the PMIDs
    # root = parse_xml_data(xml_data)

    if xml_data:
        try:
            root = ElementTree.fromstring(xml_data)
            pmids = [elem.text for elem in root.findall("./IdList/Id")]
            pmids = list(set(pmids))

        except ElementTree.ParseError as error:
            print("Error parsing XML data:", error)
            root = None
            pmids = []
            return

    return pmids


def fetch_abstract(pmid):
    # Join the PMIDs into a single stringf
    pmid_string = pmid

    # Build the Entrez API query
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
    query = f"db=pubmed&id={pmid_string}&retmode=xml&api_key=1f93c5a0c91e90f6c0d0fae4178c2e9ae309"

    # Send the API request and retrieve the XML response
    response = requests.get(base_url + query)
    xml_data = response.text

    # print(xml_data)
    # with open('xml_data.txt','w') as file:
    #     file.write(xml_data)
    # Parse the XML data to retrieve the abstracts
    root = ElementTree.fromstring(xml_data)

    # print(len(abstractclassmethod))
    # Parse other main important components of doc
    abstract_texts = [elem.text for elem in root.findall(".//AbstractText")]
    abstract_texts = ",".join(abstract_texts)

    # # Print the extracted text content
    # for text in abstract_texts:
    #     print(text)

    CONCLUSION = re.search(r'CONCLUSIONS">(.*?)</AbstractText>', xml_data)
    RESULTS = re.search(r'RESULTS">([^<]+)', xml_data)
    METHODS = re.search(r'METHODS">([^<]+).', xml_data)
    BACKROUND = re.search(r'BACKGROUND">(.*?)</AbstractText>', xml_data)
    TITLE = re.search(r"<ArticleTitle>(.*?)<", xml_data)
    AUTHOR_LAST_NAME = re.search(r"<LastName>(.*?)<\/LastName>", xml_data)
    AUTHOR_FIRST_NAME = re.search(r"<ForeName>(.*?)<\/ForeName>", xml_data)
    DATE_PUBLISHED = re.search(
        r"<PubDate><Year>(.+?)<\/Year><Month>(.+?)<\/Month><Day>(.+?)<\/Day><\/PubDate>",
        xml_data,
    )

    # ABSTRACT = extract_text(abstracts)
    # print(f"I am an abstract {ABSTRACT}")
    CONCLUSION = extract_text(CONCLUSION)
    RESULTS = extract_text(RESULTS)
    METHODS = extract_text(METHODS)
    BACKROUND = extract_text(BACKROUND)
    TITLE = extract_text(TITLE)
    AUTHOR_LAST_NAME = extract_text(AUTHOR_LAST_NAME)
    AUTHOR_FIRST_NAME = extract_text(AUTHOR_FIRST_NAME)
    DATE_PUBLISHED = extract_date(DATE_PUBLISHED)

    return (
        abstract_texts,
        xml_data,
        CONCLUSION,
        RESULTS,
        METHODS,
        BACKROUND,
        TITLE,
        AUTHOR_FIRST_NAME,
        AUTHOR_LAST_NAME,
        DATE_PUBLISHED,
    )


def get_unique_pmids():
    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"
    dataset_name = "BACKFILL"
    table_id = f"{dataset_name}.BACKFILL_2023_Clinical_Trials_vm"
    key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
    creds = Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)
    query = f"SELECT distinct(PMID_2) AS IDS FROM `{project_name}.{table_id}`"
    query_job = client.query(query)
    results = query_job.result().to_dataframe()
    # Extract the PMIDs from the results
    pmids_bq_unique = results["IDS"].unique()
    return pmids_bq_unique


def upload_to_bq(df):

    project_name = "airflow-test-371320"
    dataset_name = "BACKFILL"
    table_id = f"{dataset_name}.BACKFILL_2023_Clinical_Trials_vm"
    GCP_CONNECTION_ID = "happy_go_time"
    credentials = service_account.Credentials.from_service_account_file(
        "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
    )
    # GoogleCloudBaseHook
    df.to_gbq(
        table_id,
        if_exists="append",
        project_id=project_name,
        credentials=credentials,
    )
    print("data loaded to db")


if __name__ == "__main__":

    with open("/Users/samsavage/PythonProjects/PubMedGPT/data/chronic_conditions.json", "r") as f:
        chronic_conditions = json.load(f)

    import datetime

    today = datetime.datetime.today()
    date_string = today.strftime("%Y-%m-%d")
    dfs_big = []
    dfs = []
    condition_count = len(chronic_conditions)
    counter_master = 10000

    pmid_list = []
    pmid_list_NEW = []
    xml_list = []
    abstracts_list_full = []
    CONCLUSION_list = []
    RESULTS_list = []
    METHODS_list = []
    BACKROUND_list = []
    TITLE_list = []
    AUTHOR_list = []
    TITLE_list = []
    AUTHOR_list = []
    DATE_PUBLISHED_list = []

    # for category in chronic conditions dict
    # for for pmid in condtions
    # get dataframe

    # append dataframe
    key_length = len(chronic_conditions.keys())
    # for category in chronic conditions dict

    unies = get_unique_pmids()

    for category in chronic_conditions:
        # for category in chronic conditions dict

        for i in chronic_conditions[category]:

            print(category, "__", i)

            category = category

            search_term = i

            try:
                pmids = search_pmids(search_term)
                print("got pmids")
                pmids = [i for i in pmids if i not in unies]
                pmids = pmids
                print(pmids)
                print("subsetted pmids")
                print(len(pmids))
                if len(pmids) == 0:
                    print(
                        f"all current data about {search_term} is loaded moving on to next condition "
                    )
                else:
                    print(f"scraping {search_term}")
            except:
                print("Somethings IS WRONG")
                continue

            print(f"the numnber of pmid for condition {i} in {category}")

            if pmids is not None:

                print(i, " is not null \n")
                condition_count = len(np.unique(pmids))
                condtion_counter = 0

                for pmid in np.unique(pmids):

                    # for for pmid in condtions

                    print(pmid, "__", i)

                    if pmids is not None:

                        # print(f"getting information for {i}, for {category}")

                        try:

                            (
                                abstract_texts,
                                xml_data,
                                CONCLUSION,
                                RESULTS,
                                METHODS,
                                BACKROUND,
                                TITLE,
                                AUTHOR_FIRST_NAME,
                                AUTHOR_LAST_NAME,
                                DATE_PUBLISHED,
                            ) = fetch_abstract(pmid)

                            if xml_data:
                                if len(xml_data) > 0:
                                    try:
                                        if re.findall(
                                            (r">\d{1,20}<\/PMID>"), "".join(xml_data)
                                        ):
                                            pmid_NEW = (
                                                re.findall(
                                                    (r">\d{1,20}<\/PMID>"),
                                                    "".join(xml_data),
                                                )[0]
                                                .replace("</PMID>", "")
                                                .replace(">", "")
                                            )
                                            pmid_list_NEW.append(pmid_NEW)
                                            print("this pmid worked!")
                                        else:
                                            pmid = None
                                    except:
                                        continue

                            xml_list.append(xml_data)

                            abstracts_list_full.append(str(abstract_texts))
                            CONCLUSION_list.append(CONCLUSION)
                            RESULTS_list.append(RESULTS)
                            METHODS_list.append(METHODS)
                            BACKROUND_list.append(BACKROUND)
                            TITLE_list.append(TITLE)
                            AUTHOR_FULL_NAME = (
                                AUTHOR_FIRST_NAME + "," + AUTHOR_LAST_NAME
                            )
                            AUTHOR_list.append(AUTHOR_FULL_NAME)
                            DATE_PUBLISHED_list.append(DATE_PUBLISHED)
                        except (ElementTree.ParseError, TypeError) as error:

                            continue

                        # print("lists have been zipped")
                        condtion_counter += 1
                        print(f"{(condtion_counter/condition_count)*100} %")

            zipped = list(
                zip(
                    pmid_list_NEW,
                    TITLE_list,
                    AUTHOR_list,
                    DATE_PUBLISHED_list,
                    abstracts_list_full,
                    CONCLUSION_list,
                    RESULTS_list,
                    METHODS_list,
                    BACKROUND_list,
                    xml_list,
                )
            )
            df = pd.DataFrame(
                zipped,
                columns=[
                    "PMID",
                    "Title",
                    "AuthorName",
                    "DatePublished",
                    "Abstract",
                    "Conclusion",
                    "Results",
                    "Methods",
                    "Backround",
                    "xml_list",
                ],
            )
            df["DatePublished"] = df["DatePublished"].astype("object")
            df["MedicalCategory"] = category
            df["ChronicCondition"] = i
            df["LoadDateFormatted"] = date_string
            df["LoadDateTime"] = today
            df["xml_list"] = df["xml_list"].astype("object")

            if not len(df["xml_list"]) < 1:
                try:
                    df["PMID_2"] = df["xml_list"].apply(
                        lambda x: re.findall(r">\d{1,20}<\/PMID>", "".join(x))[0]
                        .replace("</PMID>", "")
                        .replace(">", "")
                    )
                except:
                    continue
            else:
                df["PMID_2"] = None

            df = df.drop("PMID", axis=1)

            print(df.head().T)

            df = df.drop_duplicates(keep=False)
            upload_to_bq(df.drop_duplicates(keep=False))
            print(df.head())

            # dfs.append(df)

            pmid_list.clear()
            TITLE_list.clear()
            AUTHOR_list.clear()
            DATE_PUBLISHED_list.clear()
            CONCLUSION_list.clear()
            RESULTS_list.clear()
            METHODS_list.clear()
            BACKROUND_list.clear()
            xml_list.clear()
            abstracts_list_full.clear()
