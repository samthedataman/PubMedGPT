from habanero import Crossref
from habanero import counts
from google.cloud import bigquery
import pandas as pd
import numpy as np
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
import urllib3
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import pandas_gbq
import pandas as pd
import numpy as np
from habanero import counts
import urllib3
import pandas as pd
import pandas_gbq
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

def get_data():
    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"
    dataset_name = "BACKFILL"
    table_id = f"{dataset_name}.BACKFILL_2023_Clinical_Trials_vm"
    key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
    creds = Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)
    query = f"SELECT REGEXP_EXTRACT(xml_list, r'<ArticleId IdType=\"doi\">([^<]+)</ArticleId>') AS DOI,* from  `{project_name}.{table_id}` "
    query_job = client.query(query)
    results = query_job.result().to_dataframe()

    return results

def insert_dataframe_into_table(df):
    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"
    dataset_name = "BACKFILL"
    table_id = f"{dataset_name}.BACKFILL_2023_Clinical_Trials_vm_Citation_Count2"
    key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
    creds = Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)

    pandas_gbq.to_gbq(
        df,
        table_id,
        project_id=project_name,
        if_exists="replace",
        credentials=creds,
        chunksize=None,
    )

def add_citation_count_and_upload():
    # Get data from the BigQuery table
    df = get_data()

    def fetch_citation_count(doi, index):
        cr = Works()
        try:
            results = cr.doi(doi)
            citation_count = results['reference-count']
            print(f"Processed {index+1} rows")
            return citation_count
        except Exception as e:
            print(f"Error occurred: {e}")
            return None

    # Add a new column for Citation Count initialized with NaN
    df['citation_count'] = df['DOI'].apply(fetch_citation_count)

    insert_dataframe_into_table(df)

add_citation_count_and_upload()



# for i in get_data()['DOI']:
#     doi_list.append(i)

# for doi in doi_list:
#     if doi:
#         count = counts.citation_count(doi = doi)
#         print(count)






