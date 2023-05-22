# from dotenv import load_dotenv
import matplotlib.pyplot as plt
import plotly.express as px
from fuzzywuzzy import fuzz

import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
from langchain.document_loaders import DataFrameLoader
import streamlit as st
from datetime import date
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import pandas as pd
import os
import pandas_gbq
import openai
from langchain.document_loaders import CSVLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import os
from difflib import SequenceMatcher
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from stuffthatworks.StuffThatWorksETL import run_jobs
from streamlitfunctions import *
import pandas as pd
import plotly.express as px

def visualize_data(df, nlargest=100):
    # Convert 'DateScraped' column to datetime format
    df["DateScraped"] = pd.to_datetime(df["DateScraped"])
    df["num_reports"] = df["num_reports"].astype("int")

    # Filter top conditions by num_reports
    top_conditions = df.groupby("conditions")["num_reports"].sum().nlargest(nlargest)
    top_condition_names = top_conditions.index.tolist()

    # Sort the plot_df by descending order of the total number of reports
    plot_df = df[df["conditions"].isin(top_condition_names)]
    plot_df = plot_df.sort_values(by="num_reports", ascending=False)

    # Create the stacked bar chart
    fig = px.bar(
        plot_df,
        x="symptoms",
        y="num_reports",
        color="symptoms",
        labels={
            "conditions": "Conditions",
            "num_reports": "Number of Reports",
            "symptoms": "Symptoms",
        },
        category_orders={"symptoms": top_condition_names},
    )
    fig.update_layout(
        xaxis=dict(
            tickfont=dict(size=14),  # make labels bold
            tickangle=-45,  # slant labels at -45 degrees
        )
    )

    # Display the chart using Streamlit
    st.plotly_chart(fig,height=400,use_container_width=True)


def create_chart1(timeline_df, options):
    fig = px.line(
        timeline_df,
        x="Year_Month",
        y="AggregatedPapers",
        color="ChronicCondition",
        hover_data=["ChronicCondition"],
        labels={"AggregatedPapers": "Number of Papers"},
        text=timeline_df["AggregatedPapers"]    )
    
    fig.update_traces(textposition='top center')

    fig.update_xaxes(type="category", tickformat="%Y-%m")

    # Update y-axis ticks
    fig.update_yaxes(
        tickmode="linear",  # Set the tick mode to linear
        dtick=10,
          tickfont=dict(color="white")   # Set the tick size to 10
    )

    # Update x-axis and y-axis labels
    fig.update_layout(
        xaxis=dict(
            tickfont=dict(size=14),  # make labels bold
            tickangle=-45,  # slant labels at -45 degrees
        ),
        yaxis=dict(
            title="Number of Papers",  # Set y-axis title
            tickfont=dict(size=14),  # make labels bold
        )
    )

    # Display the chart using Streamlit with desired height
    st.plotly_chart(fig,height=400,use_container_width=True)



# Function to create the second chart
def create_chart2(df, nlargest=100):
    # Convert 'DateScraped' column to datetime format
    df["DateScraped"] = pd.to_datetime(df["DateScraped"])
    df["num_reports"] = df["num_reports"].astype("int")

    # Filter top conditions by num_reports
    top_conditions = df.groupby("conditions")["num_reports"].sum().nlargest(nlargest)
    top_condition_names = top_conditions.index.tolist()

    # Sort the plot_df by descending order of the total number of reports
    plot_df = df[df["conditions"].isin(top_condition_names)]
    plot_df = plot_df.sort_values(by="num_reports", ascending=False)

    # Create the stacked bar chart
    fig = px.bar(
        plot_df,
        x="symptoms",
        y="num_reports",
        color="symptoms",
        labels={
            "conditions": "Conditions",
            "num_reports": "Number of Reports",
            "symptoms": "Symptoms",
        },
        category_orders={"symptoms": top_condition_names},
    )
    fig.update_layout(
        xaxis=dict(
            tickfont=dict(size=14),  # make labels bold
            tickangle=-45,  # slant labels at -45 degrees
        )
    )

    # Display the chart using Streamlit with desired height
    st.plotly_chart(fig, height=400)


# load_dotenv()


def get_current_month_start():
    today = datetime.date.today()
    current_month_start = datetime.date(today.year, today.month, 1)
    return current_month_start


current_month = get_current_month_start()


def get_month_start(months_ago):
    today = datetime.date.today()
    past_date = today - relativedelta(months=months_ago)
    month_start = datetime.date(past_date.year, past_date.month, 1)
    month_start = month_start.strftime("%Y-%m-%d")
    # date_object = datetime.datetime.strptime(month_start, "%Y-%m-%d").date()
    return month_start


month_starts = [get_month_start(i) for i in range(1, 7)]


def make_clickable(val):
    # target _blank to open new window
    return '<a target="_blank" href="{}">{}</a>'.format(val, val)


def get_data():
    # Instantiate a client object using credentials
    project_name = "airflow-test-371320"
    dataset_name = "BACKFILL"
    table_name = "BACKFILL_2023_GPT3"
    table_id = f"{dataset_name}.{table_name}"
    key_path = "/Users/samsavage/NHIB Scraper/airflow-test-371320-dad1bdc01d6f.json"
    creds = Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)
    query = f"""WITH ranked_data AS (
    SELECT 
        CAST(date_ AS DATE) AS Year_Month,
        date_uploaded_new,
        ChronicCondition,
        PMID,
        CONCAT(UPPER(SUBSTR(GPT3_SUMMARY, 1, 1)), SUBSTR(GPT3_SUMMARY, 2)) AS GPT3_SUMMARY,
        ROW_NUMBER() OVER (PARTITION BY ChronicCondition,CAST(date_ AS DATE) ORDER BY date_uploaded_new DESC) as row_num
    FROM `airflow-test-371320.BACKFILL.BACKFILL_2023_GPT3`
    WHERE CAST(date_ AS DATE) IS NOT NULL
)

SELECT 
    Year_Month,
    date_uploaded_new,
    ChronicCondition,
    PMID,
    GPT3_SUMMARY
FROM ranked_data
WHERE row_num = 1
 """
    query_job = client.query(query)
    results = query_job.result().to_dataframe()

    results["AggregatedPapers"] = results["PMID"].apply(
        lambda x: len(set(x.split(",")))
    )

    results[
        [
            "PMID1",
            "PMID2",
            "PMID3",
            "PMID4",
            "PMID5",
            "PMID6",
            "PMID7",
            "PMID8",
            "PMID9",
            "PMID10",
            "PMID11",
            "PMID12",
            "PMID13",
            "PMID14",
            "PMID15",
            "PMID16",
            "PMID17",
            "PMID18",
            "PMID19",
            "PMID20",
            "PMID21",
            "PMID22",
            "PMID23",
            "PMID24",
            "PMID25",
            "PMID26",
            "PMID27",
            "PMID28",
            "PMID29",
            "PMID30",
        ]
    ] = results["PMID"].str.split(",", expand=True, n=29)
    for i in range(1, 31):
        results[f"URL{i}"] = "https://pubmed.ncbi.nlm.nih.gov/" + results[f"PMID{i}"]
        results.style.format({f"URL{i}": make_clickable})
    results["URL_combined"] = results[
        [
            "URL1",
            "URL2",
            "URL3",
            "URL4",
            "URL5",
            "URL6",
            "URL7",
            "URL8",
            "URL9",
            "URL10",
            "URL11",
            "URL12",
            "URL13",
            "URL14",
            "URL15",
            "URL16",
            "URL17",
            "URL18",
            "URL19",
            "URL20",
            "URL21",
            "URL22",
            "URL23",
            "URL24",
            "URL25",
            "URL26",
            "URL27",
            "URL28",
            "URL29",
            "URL30",
        ]
    ].apply(lambda x: " , ".join(x.dropna().astype(str)), axis=1)
    results.style.format({"URL_combined": make_clickable})
    return results
