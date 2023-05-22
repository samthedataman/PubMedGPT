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


def main():
    symptoms_df, triggers_df, comorbidities_df, treatments_df = run_jobs()

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

    # Create an empty list to store the fuzzy matched words
    matched_words = []
    matched_words_treatments = []

    # Iterate over words in df1 and find the closest match in df2
    for word1 in df["ChronicCondition"].unique():
        best_match = None
        highest_similarity = 0

        for word2 in symptoms_df["conditions"].unique():
            similarity = fuzz.ratio(word1, word2)

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = word2

        if highest_similarity >= 70:  # Set the similarity threshold as desired
            matched_words.append((word1, best_match))

    # Create a DataFrame from the matched words
    matched_df = pd.DataFrame(
        matched_words, columns=["PubMedConditions", "StuffThatWorksConditions"]
    )

    # Iterate over words in df1 and find the closest match in df2
    for word1 in df["ChronicCondition"].unique():
        best_match = None
        highest_similarity = 0

        for word2 in treatments_df["conditions"].unique():
            similarity = fuzz.ratio(word1, word2)

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = word2

        if highest_similarity >= 70:  # Set the similarity threshold as desired
            matched_words_treatments.append((word1, best_match))

    # Create a DataFrame from the matched words
    matched_df_treatment = pd.DataFrame(
        matched_words_treatments,
        columns=["PubMedConditions", "StuffThatWorksConditions"],
    )

    # Display the matched DataFrame
    df = df.merge(matched_df, left_on="ChronicCondition", right_on="PubMedConditions")

    symptoms_df = symptoms_df.merge(
        matched_df, left_on="conditions", right_on="StuffThatWorksConditions"
    )

    treatments_df = treatments_df.merge(
        matched_df_treatment, left_on="conditions", right_on="StuffThatWorksConditions"
    )

    options = st.selectbox(
        "What condition(s) do you want to understand?",
        df.PubMedConditions.unique(),
        index=11,
    )

    # filter conditions on chronic condition
    filtered_df = df[
        (df["ChronicCondition"].isin([options]))
        & (df["Year_Month"] >= date1)
        & (df["Year_Month"] <= date2)
    ]

    chart_df = filtered_df.copy()

    chart_df["Year_Month_Names"] = pd.to_datetime(chart_df["Year_Month"]).dt.strftime(
        "%B"
    )

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
    st.markdown(
        f"""### Symptoms and Studies over Time for </span><span class='condition_title'>{options}</span></div>""",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        create_chart2(symptoms_df[(symptoms_df["PubMedConditions"] == options)])

    with col2:
        create_chart1(timeline_df, options)

    treatments = treatments_df[
        (treatments_df["TreatmentType"] == "Beneficial")
        & (treatments_df["PubMedConditions"] == options)
    ]["treatments"]
    # (treatments_df['rankings'] == '1'))]['treatments']

    drug_list = [
        drug.strip() for treatment in treatments for drug in treatment.split(",")
    ]

    st.markdown(
        f"""### PubMed Articles in descending order by publishing date for {options}"""
    )
    # st.markdown(f"""### Summurized Discoveres for {options} include:""")

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
        st.write(
            f"No studies exist at this time. Please try a different filtering option."
        )
    # <div class='item'><span class='date'>
    # Generate GPT-3 bot response


main()
