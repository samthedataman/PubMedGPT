# from dotenv import load_dotenv
import matplotlib.pyplot as plt
import plotly.express as px
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
import streamlit as st
import openai
from langchain.document_loaders import CSVLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "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"


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
    query = f""" SELECT 
                CAST(date_ as date) as Year_Month,
                ChronicCondition,
                PMID,
                REGEXP_REPLACE(GPT3_SUMMARY, r'The conclusion (from|of) this .* is that', '') as GPT3_SUMMARY FROM `airflow-test-371320.BACKFILL.BACKFILL_2023_GPT3`
                order by 1 desc """
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


df = get_data()

df = df[pd.to_datetime(df["Year_Month"]) >= pd.to_datetime("2020-01-01")]

# Load the dataset
# link to download data I used: https://www.kaggle.com/datasets/ashishraut64/indian-startups-top-300?resource=download


st.set_page_config(
    page_title="Learn About New Chronic Condition Research with AI",
    page_icon=":bar_chart:",
    layout="wide",
)


st.markdown(
    """<link href="https://fonts.googleapis.com/css2?family=Major+Mono+Display&family=Xanh+Mono:ital@1&display=swap&family=Roboto:wght@100&display=swap&family=Roboto+Mono:wght@300&display=swap&family=Comfortaa:wght@400;500&family=Roboto+Mono:wght@300&display=swap" rel="stylesheet">""",
    unsafe_allow_html=True,
)
st.markdown(
    """<style>
                h1 { color: white; font-family: 'Comfortaa',monospace;} 
                h2 { color: white; font-family: 'Comfortaa', monospace;} 
                h3 { color: white; font-family: 'Comfortaa',monospace;} 
                .month { color: purple; margin-right:  }
                .blurb { color: white; font-family: 'Roboto Mono', sans-serif; line-height: 1.2 } 
                .item { display: flex; align-items: flex-start; } 
                .condition_title { color: gold; font-family: 'Comfortaa',sans-serif }
                .condition_links { color: gold; font-family: 'Comfortaa',sans-serif; line-height: 1.2 }
                </style>""",
    unsafe_allow_html=True,
)
st.markdown("""<style></style>""", unsafe_allow_html=True)


st.title("Learn About New Chronic Condition Research with AI")


# Create slider widget
min_date = df["Year_Month"].min()
max_date = df["Year_Month"].max()

selected_date = st.slider(
    "Select a date:",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY/MM",
)

date1, date2 = selected_date


options = st.selectbox(
    "What condition(s) do you want to understand?", df.ChronicCondition.unique()
)

# Filter the dataframe using masks
text_search = st.text_input("Search by keyword", value="")



m1 = df["GPT3_SUMMARY"].str.contains(text_search)
df = df[m1]

# filter conditions on chronic condition
filtered_df = df[
    (df["ChronicCondition"].isin([options]))
    & (df["Year_Month"] >= date1)
    & (df["Year_Month"] <= date2)
]


chart_df = filtered_df.copy()

chart_df["Year_Month_Names"] = pd.to_datetime(chart_df["Year_Month"]).dt.strftime("%B")

timeline_df = (
    chart_df.groupby(
        ["Year_Month", "Year_Month_Names", "ChronicCondition", "GPT3_SUMMARY"]
    )
    .agg({"AggregatedPapers": "sum"})
    .reset_index()
    .sort_values(by="Year_Month", ascending=True)
)

# Extract year and month from the date column
# create stacked bar chart
fig = px.line(
    timeline_df,
    x="Year_Month",
    y="AggregatedPapers",
    color="ChronicCondition",
    hover_data=["ChronicCondition"],
    labels="AggregatedPapers",
)

fig.update_xaxes(type="category", tickformat="%Y-%m")
# update x-axis labels
fig.update_layout(
    xaxis=dict(
        tickfont=dict(size=14),  # make labels bold
        tickangle=-45,  # slant labels at -45 degrees
    ),
    width=800,  # adjust the width of the plot
    height=400,  # adjust the height of the plot
)


st.markdown(
    f"""### Plot of # of Studies overtime for </span><span class='condition_title'>{options}</span></div>""",
    unsafe_allow_html=True,
)

st.plotly_chart(fig)


st.markdown(f"""## Summurized Discoveres for {options} include:""")


if len(filtered_df) > 0:

    for summary, month, url in zip(
        filtered_df["GPT3_SUMMARY"],
        filtered_df["Year_Month"],
        filtered_df["URL_combined"],
    ):
        # Split the combined URLs and make them clickable
        urls = url.split(", ")
        n_urls = len(urls)
        clickable_urls = ", ".join(
            [
                f"<a href='{u}' target='_blank'>source {i+1}</a>"
                for i, u in enumerate(urls)
            ]
        )

        col1, col2 = st.columns([7, 1])

        with col1:
            st.markdown(
                f"""<div><b>{month}</b></div><div class='blurb'>{summary}</div>""",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""</span><span class='condition_title'>Links: {clickable_urls}</span></div>""",
                unsafe_allow_html=True,
            )
else:
    st.write(f"No studies exist at this time. Please try a different filtering option.")
# <div class='item'><span class='date'>
# Generate GPT-3 bot response
