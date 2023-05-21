from dotenv import load_dotenv
from gpt4all import GPT4All
import json
from datetime import datetime
load_dotenv()
import pandas as pd 
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import openai
import pandas_gbq
import scholarly


with open('/Users/samsavage/PythonProjects/PubMedGPT/data/openaikeys.json') as f:
    keys = json.load(f)

openai_api_key = keys["OPENAI_API_KEY"]

def get_total_citation_count(doi_str):
    # Split the DOIs using the delimiter
    
   if doi_str is not None:
    doi_list = doi_str.split("++")
    print(doi_list)

    # Get the citation count for each DOI and add them up
    total_citation_count = 0
    for doi in doi_list:
        try:
            pub = next(scholarly.search_pubs_query(doi))
            total_citation_count += pub.citedby
        except:
            pass
    
    return total_citation_count

max_tokens = 2153


# def get_free_conclusion(condition, truncated_text):
#     gptj = GPT4All("ggml-gpt4all-j-v1.3-groovy")
#     prompt = f"""Tell me the conclusion from this PubMed Paper on this {condition}: \n{truncated_text}\n\n"""
#     messages = [{"role": "user", "content": prompt}]
#     message = [0:2048]
#     answer = gptj.chat_completion(messages)['choices'][0]['message']['content']
#     return str(answer),prompt


def insert_dataframe_into_table(df):
    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"
    dataset_name = "BACKFILL"
    table_id = f"{dataset_name}.BACKFILL_2023_GPT3"
    key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
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

def get_clean_data():

    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"
    key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
    creds = Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)
    query = f"""WITH ranked_table AS (
    SELECT 
        a.*,
        ROW_NUMBER() OVER(PARTITION BY a.pmid_2 ORDER BY a.DatePublished DESC) as rankdaddy
    FROM (
Select
        concat(Year,"-",Month,"-",Day) as Date_,
        concat(Year,"-",(case Month
            WHEN 'jan' THEN '01'
            WHEN 'Feb' THEN '02'
            WHEN 'Mar' THEN '03'
            WHEN 'Apr' THEN '04'
            WHEN 'May' THEN '05'
            WHEN 'Jun' THEN '06'
            WHEN 'Jul' THEN '07'
            WHEN 'Aug' THEN '08'
            WHEN 'Sep' THEN '09'
            WHEN 'Oct' THEN '10'
            WHEN 'Nov' THEN '11'
            WHEN 'Dec' THEN '12' end)) PubDate,
        Year,
        Month,
        Day,
        * from (
            SELECT 
                *,
                REGEXP_EXTRACT(REGEXP_EXTRACT(xml_list, r'<PubDate>(.*?)<\/PubDate>'), r'\d{4}') as Year,
                REGEXP_EXTRACT(REGEXP_EXTRACT(xml_list, r'<PubDate>(.*?)<\/PubDate>'), r'<Month>([a-zA-Z]+)</Month>') as Month,
                REGEXP_EXTRACT(REGEXP_EXTRACT(xml_list, r'<PubDate>(.*?)<\/PubDate>'), r'<Day>(\d{1,2})</Day>') as Day,
                REGEXP_EXTRACT(xml_list, r'<ArticleId IdType="doi">([^<]+)</ArticleId>') AS DOI
            FROM `airflow-test-371320.BACKFILL.BACKFILL_2023_Clinical_Trials_vm`
        )
    ) a 
)
Select z.*
from (
SELECT 
    SAFE_CAST(concat(PubDate,"-01") as date) as date_,
    ChronicCondition,
    concat(STRING_AGG(Conclusion,'++'),STRING_AGG(Abstract,'++')) AS raw_text,
    STRING_AGG(PMID_2,'++') AS PMID,
    STRING_AGG(DOI,'++') AS DOI
FROM ranked_table
where PubDate is not null 
and rankdaddy =1 
GROUP BY 1,2
ORDER BY date_ desc) z
where z.raw_text not in (Select raw_text FROM `airflow-test-371320.BACKFILL.BACKFILL_2023_GPT3`)"""

    query_job = client.query(query)
    results = query_job.result().to_dataframe()
    # Extract the PMIDs from the results
    return results


def summarize_text(text, condition):
    """
    Summarize the given text using the DaVinci API.
    """
    openai.api_key = openai_api_key

    prompt_and_response_max_tokens = 4096

    prompt_limit = 2000

    truncated_text = text[:prompt_limit]

    conditon = condition
    
    prompt = f"""Tell me the conclusion from this PubMed Paper on this {condition}: \n{truncated_text}\n\n"""
    # print(prompt[:200])
    max_tokens = prompt_and_response_max_tokens - len(truncated_text)

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=max_tokens,
        n=1,
        stop=None,
        temperature=0.1,
    )

    summary = response.choices[0].text.strip()
    return summary, prompt


def go():

    df = get_clean_data()

    # df["f0_"] = df["DOI"].apply(get_total_citation_count)
    # print(df["f0_"])

    prompt_list = []
    text_list = []

    length_of_df = len(df)
    counter = 0

    for i in range(0, length_of_df, 20):

        chunk = df.loc[i : i + 20, :]

        uniques_pmids = [pmid for pmid in chunk]

        for text, condition in zip(
            chunk["raw_text"].astype("str"), chunk["ChronicCondition"].astype("str")
        ):
            counter += 1
            try:
                sum, prompt = summarize_text(text, condition=condition)
                # sum,prompt = get_free_conclusion(text,condition)
                prompt_list.append(prompt)
                text_list.append(sum)
                print(f"done with row {counter}")
            except ValueError as e:
                print(f"Error was {e}")
                print("writing blank")
                filler = " "
                prompt_list.append(filler)
                text_list.append(filler)
                print(f"done with row {counter}")

        chunk["GPT3_SUMMARY"] = text_list
        chunk["GPT3_PROMPT"] = prompt_list
        chunk["date_"] = chunk["date_"].astype("string")
        chunk["date_uploaded"] = pd.to_datetime(datetime.now().strftime('%Y-%m-%d'))
        chunk["date_uploaded_new"] = pd.to_datetime(datetime.now().strftime('%Y-%m-%d'))

        chunk =  chunk[["date_",				
                        "ChronicCondition",			
                        "raw_text",			
                        "PMID",		
                        "GPT3_SUMMARY",			
                        "GPT3_PROMPT",
                        "date_uploaded",
                        "date_uploaded_new"]]
        insert_dataframe_into_table(chunk)
        print("chunk inserted")

        prompt_list.clear()
        text_list.clear()

        print(counter)


go()
