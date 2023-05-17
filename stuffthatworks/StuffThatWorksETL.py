from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import pandas as pd
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

KEY_PATH = "gbqkeys.json"
PROJECT_NAME = "airflow-test-371320"


def run_jobs():

    def join_dataframes_ranking(symptoms_df, triggers_df, comorbidities_df):
        # Pivot the dataframes
        symptoms_df = symptoms_df.pivot(index='conditions', columns='symptoms', values='rankings').fillna(0)
        triggers_df = triggers_df.pivot(index='conditions', columns='triggers', values='rankings').fillna(0)
        comorbidities_df = comorbidities_df.pivot(index='conditions', columns='comorbidities', values='rankings').fillna(0)
        joined_df = pd.concat([symptoms_df, triggers_df, comorbidities_df], axis=1).fillna(0)
        return joined_df

    def join_dataframes(symptoms_df, triggers_df, comorbidities_df):
        # Pivot the dataframes
        symptoms_df = symptoms_df.pivot(index='conditions', columns='symptoms', values='rankings').fillna(0)
        triggers_df = triggers_df.pivot(index='conditions', columns='triggers', values='rankings').fillna(0)
        comorbidities_df = comorbidities_df.pivot(index='conditions', columns='comorbidities', values='rankings').fillna(0)
        joined_df_normal = pd.concat([symptoms_df, triggers_df, comorbidities_df], axis=1).fillna(0)
        return joined_df_normal

    def run_bigquery_query(query, key_path, project_name):
    # Instantiate a client object using credentials
        creds = Credentials.from_service_account_file(key_path)
        client = bigquery.Client(credentials=creds, project=project_name)

        # Execute the query and return the results as a DataFrame
        query_job = client.query(query)
        results = query_job.result().to_dataframe()

        return results

    queries = {
"symptoms": """
    SELECT *
    FROM (
        SELECT 
            conditions,
            REGEXP_REPLACE(rankings, '#', '') as rankings,
            num_reports,
            TimeScraped,
            DateScraped,
            symptoms,
            RANK() OVER (PARTITION BY conditions ORDER BY DateScraped DESC, TimeScraped DESC) as rank
        FROM
            `airflow-test-371320.DEV.STUFF_THAT_WORKS_SYMPTOMS_DEV`
        WHERE rankings IS NOT NULL
        AND cast(REGEXP_REPLACE(rankings, '#', '') as int) <= 20
    ) ranked_data
    WHERE rank = 1
""",
"triggers": """
    SELECT *
    FROM (
        SELECT 
            conditions,
            REGEXP_REPLACE(rankings, '#', '') as rankings,
            num_reports,
            TimeScraped,
            DateScraped,
            triggers,
            RANK() OVER (PARTITION BY conditions ORDER BY DateScraped DESC, TimeScraped DESC) as rank
        FROM 
            `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_TRIGGERS`
        WHERE rankings IS NOT NULL
        AND cast(REGEXP_REPLACE(rankings, '#', '') as int) <= 20
    ) ranked_data
    WHERE rank = 1
""",
"comorbidities": """
    SELECT *
    FROM (
        SELECT 
            conditions,
            REGEXP_REPLACE(rankings, '#', '') as rankings,
            num_reports,
            TimeScraped,
            DateScraped,
            comorbidities,
            RANK() OVER (PARTITION BY conditions ORDER BY DateScraped DESC, TimeScraped DESC) as rank
        FROM 
            `airflow-test-371320.BACKFILL.STUFF_THAT_WORKS_COMORBIDITIES`
        WHERE rankings IS NOT NULL
        AND cast(REGEXP_REPLACE(rankings, '#', '') as int) <= 20
    ) ranked_data
    WHERE rank = 1
        """
    }

    dfs = []

    for query_name, query_str in queries.items():
        # Execute the query and store the results in a DataFrame
        results = run_bigquery_query(query_str, KEY_PATH, PROJECT_NAME)

        # Add the DataFrame to the list of DataFrames
        dfs.append(results)
        
    symptoms_df = dfs[0].copy()
    triggers_df= dfs[1].copy()
    comorbidities_df = dfs[2].copy()

    joined_df = join_dataframes_ranking(symptoms_df, triggers_df, comorbidities_df)
    
    joined_df_normal = join_dataframes_ranking(symptoms_df, triggers_df, comorbidities_df).astype('int')

    mask = joined_df_normal > 0

    # Apply the mask to the DataFrame to replace positive numbers with 1
    df_binary = joined_df_normal.where(~mask, 1)


    return joined_df,df_binary


joined_df,binary_df = run_jobs()

binary_df.to_csv("bigmatrix.csv")

