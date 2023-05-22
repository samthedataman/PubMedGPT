import pandas as pd
from pymed import PubMed
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from collections import OrderedDict
from habanero import counts
import pyarrow as pa
import os
import regex as re
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
import openai
import ast


def stringify_columns(df):
    """
    Convert all columns in a DataFrame to strings, with special handling for dictionaries.

    :param df: pandas DataFrame
    :return: DataFrame with all columns converted to strings
    """
    for column in df.columns:
        df[column] = df[column].apply(
            lambda x: ", ".join(f"{k}:{v}" for k, v in x.items())
            if isinstance(x, dict)
            else str(x)
        )
    return df


def get_condition_treatments_for_pubmed_from_STW():
    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"
    key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
    creds = Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)
    query = f""" SELECT 
    conditions AS Disease,
    REPLACE(
        REPLACE(SPLIT(treatments, ',')[OFFSET(0)], '|', ''), 
        CONCAT(
            CASE WHEN treatments LIKE '%Physical activity%' THEN 'Physical activity' ELSE '' END,
            CASE WHEN treatments LIKE '%Dietary change%' THEN 'Dietary change' ELSE '' END,
            CASE WHEN treatments LIKE '%Lifestyle change%' THEN 'Lifestyle change' ELSE '' END,
            CASE WHEN treatments LIKE '%Alternative therapy%' THEN 'Alternative therapy' ELSE '' END,
            CASE WHEN treatments LIKE '%Non-surgical procedure%' THEN 'Non-surgical procedure' ELSE '' END,
            CASE WHEN treatments LIKE '%Psychological therapy%' THEN 'Psychological therapy' ELSE '' END,
            CASE WHEN treatments LIKE '%Home remedies%' THEN 'Home remedies' ELSE '' END,
            CASE WHEN treatments LIKE '%Herbal drug / herb%' THEN 'Herbal drug / herb' ELSE '' END,
                            CASE WHEN treatments LIKE '%(Unspecified)Surgical procedure %' THEN '(Unspecified)Surgical procedure' ELSE '' END,
                CASE WHEN treatments LIKE '%(Unspecified)Vitamins & minerals %' THEN '(Unspecified)Vitamins & minerals' ELSE '' END,
            CASE WHEN treatments LIKE '%(Unspecified) %' THEN 'Unspecified' ELSE '' END,
            CASE WHEN treatments LIKE '%Massage therapies%' THEN 'Massage therapies' ELSE '' END,
            CASE WHEN treatments LIKE '%Drug%' THEN 'Drug' ELSE '' END,
            CASE WHEN treatments LIKE '%Coping tools and strategies%' THEN 'Coping tools and strategies' ELSE '' END
            
        ),
        ''
    ) AS Treatment,
    CONCAT(
        conditions, "|",
        REPLACE(
            REPLACE(SPLIT(treatments, ',')[OFFSET(0)], '|', ''), 
            CONCAT(
                CASE WHEN treatments LIKE '%Physical activity%' THEN 'Physical activity' ELSE '' END,
                CASE WHEN treatments LIKE '%Dietary change%' THEN 'Dietary change' ELSE '' END,
                CASE WHEN treatments LIKE '%Lifestyle change%' THEN 'Lifestyle change' ELSE '' END,
                CASE WHEN treatments LIKE '%Alternative therapy%' THEN 'Alternative therapy' ELSE '' END,
                CASE WHEN treatments LIKE '%Non-surgical procedure%' THEN 'Non-surgical procedure' ELSE '' END,
                CASE WHEN treatments LIKE '%Psychological therapy%' THEN 'Psychological therapy' ELSE '' END,
                CASE WHEN treatments LIKE '%Home remedies%' THEN 'Home remedies' ELSE '' END,
                CASE WHEN treatments LIKE '%Herbal drug / herb%' THEN 'Herbal drug / herb' ELSE '' END,
                CASE WHEN treatments LIKE '%(Unspecified)Surgical procedure %' THEN '(Unspecified)Surgical procedure' ELSE '' END,
                CASE WHEN treatments LIKE '%(Unspecified)Vitamins & minerals %' THEN '(Unspecified)Vitamins & minerals' ELSE '' END,
                CASE WHEN treatments LIKE '%(Unspecified) %' THEN 'Unspecified' ELSE '' END,
                CASE WHEN treatments LIKE '% (Unspecified) %' THEN 'Unspecified' ELSE '' END,
                        case WHEN treatments LIKE '%( Unspecified)%' THEN 'Unspecified' ELSE '' END,
                     case WHEN treatments LIKE '%(Unspecified )%' THEN 'Unspecified' ELSE '' END,
                    case WHEN treatments LIKE '%( Unspecified )%' THEN 'Unspecified' ELSE '' END,
                case WHEN treatments LIKE '%(Unspecified)%' THEN 'Unspecified' ELSE '' END,
                CASE WHEN treatments LIKE '%Massage therapies%' THEN 'Massage therapies' ELSE '' END,
                CASE WHEN treatments LIKE '%Drug%' THEN 'Drug' ELSE '' END,
                CASE WHEN treatments LIKE '%Coping tools and strategies%' THEN 'Coping tools and strategies' ELSE '' END
            ),
            ''
        )
    ) AS DiseaseTreatmentKey,
        CASE 
        WHEN treatments LIKE '%Physical activity%' THEN 'Physical activity'
        WHEN treatments LIKE '%Dietary change%' THEN 'Dietary change'
        WHEN treatments LIKE '%Lifestyle change%' THEN 'Lifestyle change'
        WHEN treatments LIKE '%Alternative therapy%' THEN 'Alternative therapy'
        WHEN treatments LIKE '%Non-surgical procedure%' THEN 'Non-surgical procedure'
        WHEN treatments LIKE '%Psychological therapy%' THEN 'Psychological therapy'
        WHEN treatments LIKE '%Home remedies%' THEN 'Home remedies'
        WHEN treatments LIKE '%Herbal drug / herb%' THEN 'Herbal drug / herb'
        WHEN treatments LIKE '%Massage therapies%' THEN 'Massage therapies'
        WHEN treatments LIKE '%Drug%' THEN 'Drug'
        WHEN treatments LIKE '%Coping tools and strategies%' THEN 'Coping tools and strategies'
        WHEN treatments LIKE '%(Unspecified)Surgical procedure %' THEN '(Unspecified)Surgical procedure'
        WHEN treatments LIKE '%(Unspecified)Vitamins & minerals %' THEN '(Unspecified)Vitamins & minerals'
        WHEN treatments LIKE '%Unspecified%' THEN 'Unspecified'
        WHEN treatments LIKE '%( Unspecified)%' THEN 'Unspecified'
        WHEN treatments LIKE '%(Unspecified )%' THEN 'Unspecified'
        WHEN treatments LIKE '%( Unspecified )%' THEN 'Unspecified'
                WHEN treatments LIKE '%(Unspecified)%' THEN 'Unspecified'
        ELSE 'Other'
    END AS TreatmentCategory,
    rankings AS DiseaseTreatmentRank,
    num_reports AS DiseaseTreatmentNumReports
FROM 
    airflow-test-371320.DEVL.STUFF_THAT_WORKS_TREATMENTS_DEV
WHERE 
    conditions IS NOT NULL;

                """

    query_job = client.query(query)
    results = query_job.result().to_dataframe()
    DiseaseTreatments = [d for d in results["DiseaseTreatmentKey"].unique()]
    return DiseaseTreatments


def handle_list_objects(series):
    # Convert list objects to bytes
    series = series.apply(
        lambda x: json.dumps(x).encode() if isinstance(x, list) else x
    )
    return series


def upload_to_bq(df):
    project_name = "airflow-test-371320"
    dataset_name = "PubMeta"
    table_id = f"{dataset_name}.PubMedWrapperDuck"
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


def update_dicts(article_dicts):
    for article_dict in article_dicts:
        # Extract PMID and add 'ArticlePmid' and 'ArticleLink' keys to the dict
        pmid_search = re.search(r"\d+", article_dict.get("pubmed_id", ""))
        if pmid_search:
            pmid = pmid_search.group()
            article_dict["ArticlePmid"] = pmid
            article_dict["ArticleLink"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}"

        # Add 'CitationCounts' key to the dict
        citation_count = 0  # Default to 0 if we can't get a count
        doi = article_dict.get("doi", "")
        if doi:
            doi = doi.split(" ")[0]  # get the first DOI
            try:
                citation_count = counts.citation_count(doi=doi)
            except Exception:
                # If there's an error getting the citation count, we'll just ignore it.
                pass
        article_dict["CitationCounts"] = citation_count
    return article_dicts

    return article_dicts


def get_ai_generated_data(df):
    prompt = PromptTemplate(
        input_variables=["title", "results", "conclusions", "abstract"],
        template="""Context:
                    You are a medical PhD student at Harvard reviewing PubMed medical journal articles to perform a meta analysis.
                    You are reviewing a paper titled: {title}
                    The paper had these conclusions: {conclusions}
                    The paper had these results: {results}
                    The paper has this abstract: {abstract}

                    Task: Return 6 labels for each paper

                    1) Study Objective OR Hypothesis
                    2) Treatment efficacy for each indicator tested, only choose from these 3 options below:
                    (Statistically significant high (context: if p value mentioned less than .05))
                    (Statistically significant middle (context: if p value mentioned less than .1))
                    (Statistically significant low (context: if p value mentioned less than .2))
                    (Directionally significant (context: if p value is not mentioned but there is an effect))
                    (No effect (context: results were inconclusive))
                    3) Sample size of study (number of total participants)
                    4) Study type (meta, randomized, clinical, double blind, qualitative)
                    5) Stat sig + / 1 with disease specific symptoms addressed by study (specific metrics relative to the disease) example = (.05+, medical acronym/indicator)
                    6) Trend/correlation discovered

                    Format requirements:
                    Return a Python list []. Here is an example:
                    ["Telephone cognitive behavior therapy (CBT) with two face-to-face appointments is an effective treatment for chronic fatigue syndrome (CFS) and is comparable to face-to-face CBT in terms of improving physical functioning and reducing fatigue.", "Statistically significant", "30", "Randomized clinical trial", [[".01+, time elapsed before recovery of 25% of neuromuscular function"], [".001+, time elapsed before recovery of 90% of function"]], "Rocuronium block had a better profile than vecuronium block for patients with myasthenia gravis."]
                    Include no other text but the list output!!!""",
    )

    llm = OpenAI(
        model_name="text-davinci-003",  # default model
        temperature=0.2,  # temperature dictates how whacky the output should be
    )

    llmchain = LLMChain(llm=llm, prompt=prompt)
    print(llmchain)

    df["MetaGPT"] = df.apply(
        lambda row: llmchain.run(
            title=row["title"],
            results=row["results"],
            conclusions=row["conclusions"],
            abstract=row["abstract"],
        ),
        axis=1,
    )

    # df["MetaGPT"] = df["MetaGPT"].apply(ast.literal_eval)

    return df


def get_results_and_predictions(DiseaseTreatments):
    # Iterate over the list
    print(f"length of Dtreatment list is {len(DiseaseTreatments)}, scraping away..")
    dt_count = 0
    for item in DiseaseTreatments:
        # Split the element into disease and treatment
        disease, treatment = item.split("|")

        print(f"Scraping {disease} with {treatment}")

        # Clean up the strings (remove leading/trailing spaces)
        disease = disease.strip()
        treatment = treatment.strip()

        # Build the query
        query = f'({disease}[Title/Abstract] AND {treatment}[Title/Abstract] AND ("Randomized Controlled Trial"[Publication Type] OR "Double-Blind Method"[MeSH Terms] OR "Clinical Trial"[Publication Type]))'
        #
        pubmed = PubMed(tool="MyTool", email="samuel.savage@uconn.edu")
        my_api_key = "1f93c5a0c91e90f6c0d0fae4178c2e9ae309"
        pubmed.parameters.update({"api_key": my_api_key})
        pubmed._rateLimit = 50
        # Execute the query
        try:
            results = pubmed.query(query=query, max_results=10000)
            article_dicts = []
            for article in results:
                # Convert article to dict and append to list
                article_dict = article.toDict()
                # article_dict.pop("authors", None)
                # Combine disease and treatment as 'DiseaseTreatments'
                DiseaseTreatments = disease + "|" + treatment
                # Create an ordered dictionary with 'DiseaseTreatments' as the first key
                ordered_dict = OrderedDict(
                    [("DiseaseTreatments", DiseaseTreatments)]
                    + list(article_dict.items())
                )
                ordered_dict["disease"] = disease
                ordered_dict["treatment"] = treatment
                article_dicts.append(ordered_dict)
                article_dicts = update_dicts(article_dicts)
        except:
            print(f"{item} does not have any RCT's at the moment")

        df = pd.DataFrame(article_dicts)
        df = stringify_columns(df)
        df.to_csv("tablethatowontowkr.csv")
        print(f"uploading {disease} {treatment} pubmed results")
        dt_count += 1
        print(df.head(10).T)

        if len(df) > 0:
            # funtion to get_gen
            # df = get_ai_generated_data(df)
            upload_to_bq(df)
            print(
                f"done with {round(dt_count/len(DiseaseTreatments),3)}% of  pubmed results"
            )
        else:
            print("no date to scrape")

    return df


def main():
    # os.environ["OPENAI_API_KEY"] = "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"

    # Step 1: Get condition treatments from STW
    DiseaseTreatments = get_condition_treatments_for_pubmed_from_STW()
    # Step 2: Get results and predictions
    get_results_and_predictions(DiseaseTreatments)
    print("Data upload process completed.")


if __name__ == "__main__":
    main()


# from google.cloud import bigquery
# from google.oauth2 import service_account

# def upload_to_bq_new(df):
#     project_name = "airflow-test-371320"
#     dataset_name = "PubMeta"
#     table_id = f"{project_name}.{dataset_name}.PubMetaArticles"
#     credentials = service_account.Credentials.from_service_account_file(
#         "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
#     )

#     # Convert list objects to bytes
#     df = df.apply(handle_list_objects)

#     # Create BigQuery client
#     client = bigquery.Client(project=project_name, credentials=credentials)

#     # Check if table exists
#     table = bigquery.Table(table_id)
#     if not client.get_table(table):
#         schema = bigquery.Schema.from_dataframe(df)
#         table = bigquery.Table(table_id, schema=schema)
#         table = client.create_table(table, project=project_name)
#         print(f"Table {table_id} created.")

#     # Load data to BigQuery
#     job_config = bigquery.LoadJobConfig()
#     job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
#     job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
#     job.result()

#     print("Data loaded to BigQuery")


def extract_significance_metrics_and_symptoms(text):
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    significance_metrics_and_symptoms = []
    for sentence in sentences:
        if re.search(r"p\s*(<|<=)\s*0.05", sentence):
            metric = re.search(
                r"\b(\w+)\b(?=\s*(had|showed|exhibited|revealed|demonstrated|indicated|suggested))",
                sentence,
            )
            symptom = re.search(r"\b(\w+)\b(?=\s*(symptoms|symptom))", sentence)
            trend = re.search(r"\b(increased|decreased|improved)\b", sentence)
            if metric and symptom:
                significance_metrics_and_symptoms.append(
                    (
                        symptom.group(0),
                        metric.group(0),
                        "Positive",
                        "Statistically Significant",
                        trend.group(0) if trend else None,
                    )
                )
            else:
                significance_metrics_and_symptoms.append(
                    (
                        None,
                        metric.group(0),
                        "Positive",
                        "Statistically Significant" if metric else None,
                        trend.group(0) if trend else None,
                    )
                )
        elif re.search(r"p\s*(>|>=)\s*0.05", sentence):
            metric = re.search(
                r"\b(\w+)\b(?=\s*(had|showed|exhibited|revealed|demonstrated|indicated|suggested))",
                sentence,
            )
            symptom = re.search(r"\b(\w+)\b(?=\s*(symptoms|symptom))", sentence)
            trend = re.search(r"\b(increased|decreased|improved)\b", sentence)
            if metric and symptom:
                significance_metrics_and_symptoms.append(
                    (
                        symptom.group(0),
                        metric.group(0),
                        "Negative",
                        "Not Statistically Significant",
                        trend.group(0) if trend else None,
                    )
                )
            else:
                significance_metrics_and_symptoms.append(
                    (
                        None,
                        metric.group(0),
                        "Negative",
                        "Not Statistically Significant" if metric else None,
                        trend.group(0) if trend else None,
                    )
                )
    return significance_metrics_and_symptoms


#     pubmed = PubMed(tool="MyTool", email="samuel.savage@uconn.edu")
#     condition = condition
#     treatment = treatment

#     query = f'({condition}[Title/Abstract] AND {treatment}[Title/Abstract] AND ("Randomized Controlled Trial"[Publication Type] OR "Double-Blind Method"[MeSH Terms] OR "Clinical Trial"[Publication Type]))'

#     results = pubmed.query(query=query, max_results=10)

# article_dicts = []
# for article in results:
#     # Convert article to dict and append to list
#     article_dict = article.toDict()
#     article_dicts.append(article_dict)

# df = pd.DataFrame(article_dicts)
# return df


# import ast

# # Function to handle the third element when it's a list
# def split_list(x):
#     if isinstance(x, list):
#         return pd.Series(x)
#     return pd.Series([x])

# # Remove the 'ANSWER: ' prefix and parse strings into python objects
# df["MetaGPT"] = df["MetaGPT"].str.replace("ANSWER: ", "", regex=False).str.strip()
# df['SignificanceMetricsSymptomsAndTrends'] = (df['conclusions'] + ' ' + df['results']).apply(extract_significance_metrics_and_symptoms)

# df.to_csv(f"pre_cleaned_{treatment}_{condition}.csv")
# try:
#     df["MetaGPT"] = df["MetaGPT"].apply(ast.literal_eval)

#     # Split the list into multiple columns
#     df[
#         ["efficacy", "size", "StudyType", "SymptomsTreated", "Trend"]
#     ] = pd.DataFrame(df["MetaGPT"].to_list(), index=df.index)

#     # Find the maximum number of elements in the lists in the third column
#     max_elements = (
#         df["SymptomsTreated"]
#         .apply(lambda x: len(x) if isinstance(x, list) else 1)
#         .max()
#     )

#     # Create a list of column names based on that
#     new_col_names = [f"SymptomsTreated_{i+1}" for i in range(max_elements)]

#     # Split the third column into multiple columns
#     df[new_col_names] = df["SymptomsTreated"].apply(split_list)

#     # Drop the original column
#     df = df.drop(columns=["MetaGPT"])

#     df.to_csv(f"{condition}_{treatment}.csv")
# except:
#     df.to_csv(f"pre_cleaned_{treatment}_{condition}_2.csv")

# return df


# def generate_score_cards(df):

# return dictionary with # of studies, aver

# def main():
#      df = query_pubmed("arthritus","vitamin d")
#     # #  df = df[~df['conclusions'].isna()]
#     #  df = analyze_study_conclusion(df)
#     #  df = df[["title","conclusions","results"]]
#     #  df.to_csv("analyzed_df.csv")
#     print(df.head().T)
# main()


# def analyze_study_conclusion(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Analyze a study conclusion and return the AI's interpretation.

#     Args:
#         df (pd.DataFrame): DataFrame with 'title' and 'conclusion' columns.

#     Returns:
#         pd.DataFrame: DataFrame with new 'interpretation' column for AI's interpretation of the study conclusion.
#     """

#     # Initialize OpenAI language model
#     llm = OpenAI(temperature=0.1, openai_api_key=openai_api_key)

#     from langchain import PromptTemplate, OpenAI, LLMChain

#     prompt_template="""The study titled "{title}" had these "{results}" and concluded that "{conclusions}".
#                     Based on this conclusion, would you say the study found the treatment to be statistically effective,
#                     unaffected, inconclusive, or detrimental?

#                     RETURN 1 of 4 of these choices

#                     statistically effective
#                     unaffected
#                     inconclusive
#                     detrimental                    """,

#     llm = OpenAI(temperature=0)
#     llm_chain = LLMChain(
#         llm=llm,
#         prompt=PromptTemplate.from_template(prompt_template)
#     )
#     llm_chain("colorful socks")

#     # Create prompt template
#     prompt = PromptTemplate(
#         input_variables=["title", "conclusions", "results"],


#     )
#     # Create chain with language model and prompt
#     chain = LLMChain(llm=llm, prompt=prompt)

# )
#     # Define a function to process each row
#     def process_row(row):
#         if pd.notna(row['title']) and pd.notna(row['conclusions']) and pd.notna(row['results']):
#             return chain.run({"title": row['title'], "conclusions": row['conclusions'], "results": row['results']})
#         else:
#             return None

#     # Apply the function to each row in the DataFrame and store results in 'interpretation' column
#     df['interpretation'] = df.apply(process_row, axis=1)

#     return df
