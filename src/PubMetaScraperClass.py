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


class PubMedScraper:
    def __init__(self, table_name, num_results):
        self.table_name = table_name
        self.num_results = num_results

    def stringify_columns(self, df):
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

    def get_condition_treatments_for_pubmed_from_STW(self):
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
                    conditions IS NOT NULL"""
        query_job = client.query(query)
        results = query_job.result().to_dataframe()
        DiseaseTreatments = [d for d in results["DiseaseTreatmentKey"].unique()]
        return DiseaseTreatments

    def handle_list_objects(self, series):
        # Convert list objects to bytes
        series = series.apply(
            lambda x: json.dumps(x).encode() if isinstance(x, list) else x
        )
        return series

    def upload_to_bq(self, df):
        project_name = "airflow-test-371320"
        dataset_name = "PubMeta"
        table_id = f"{dataset_name}.{self.table_name}"  # use the table name passed in to __init__()
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
        print("Data loaded to BigQuery")

    def update_dicts(self, article_dicts):
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

    def get_ai_generated_data(self, df):
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
                        2) Treatment efficacy for each indicator tested, only choose from

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

        df["MetaGPT"] = df.apply(
            lambda row: llmchain.run(
                title=row["title"],
                results=row["results"],
                conclusions=row["conclusions"],
                abstract=row["abstract"],
            ),
            axis=1,
        )

        return df

    def get_results_and_predictions(self, DiseaseTreatments):
        # Instantiate a client object using credentials
        project_name = "airflow-test-371320"
        key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
        creds = Credentials.from_service_account_file(key_path)
        client = bigquery.Client(credentials=creds, project=project_name)

        # Iterate over the DiseaseTreatments list
        for item in DiseaseTreatments:
            # Split the element into disease and treatment
            disease, treatment = item.split("|")

            print(f"Scraping {disease} with {treatment}")

            # Clean up the strings (remove leading/trailing spaces)
            disease = disease.strip()
            treatment = treatment.strip()

            # Build the query
            query = f'({disease}[Title/Abstract] AND {treatment}[Title/Abstract] AND ("Randomized Controlled Trial"[Publication Type] OR "Double-Blind Method"[MeSH Terms] OR "Clinical Trial"[Publication Type]))'

            query_job = client.query(query)
            results = query_job.result().to_dataframe()

            if len(results) > 0:
                article_dicts = []
                for _, row in results.iterrows():
                    article_dict = row.to_dict()

                    # Combine disease and treatment as 'DiseaseTreatments'
                    DiseaseTreatments = disease + "|" + treatment

                    # Create an ordered dictionary with 'DiseaseTreatments' as the first key
                    ordered_dict = OrderedDict(
                        [
                            ("DiseaseTreatments", DiseaseTreatments),
                            *article_dict.items(),
                        ]
                    )

                    ordered_dict["disease"] = disease
                    ordered_dict["treatment"] = treatment
                    article_dicts.append(ordered_dict)

                article_dicts = self.update_dicts(article_dicts)

                df = pd.DataFrame(article_dicts)
                df = self.stringify_columns(df)

                if len(df) > 0:
                    df = self.get_ai_generated_data(df)
                    self.upload_to_bq(df)
                    print(f"Scraping {disease} with {treatment}: Success")
                else:
                    print(f"Scraping {disease} with {treatment}: No data to scrape")
            else:
                print(f"Scraping {disease} with {treatment}: No results found")

    def run_scraper(self):
        DiseaseTreatments = self.get_condition_treatments_for_pubmed_from_STW()
        self.get_results_and_predictions(DiseaseTreatments)


if __name__ == "__main__":
    scraper = PubMedScraper(table_name="PublicMedicalMay21", num_results=1000)
    scraper.run_scraper()
