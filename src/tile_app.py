
# Generate grid of metrics
import streamlit as st
import random
import streamlit_nested_layout

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

    treatments = treatments_df[
        (treatments_df["TreatmentType"] == "Beneficial")
        & (treatments_df["PubMedConditions"] == options)
    ]["treatments"]

    drug_list = [
        drug.strip() for treatment in treatments for drug in treatment.split(",")
    ]
    drug_list = sorted(drug_list, key=len)

    if not drug_list:
        st.error('No treatments found.')
        return

    # List of potential medical emojis
    emoji_list = ["💊", "🩺", "💉", "🌡️", "🧪", "🦠", "🔬", "🧬"]

    # Pad the drug_list
    max_len = max(len(drug) for drug in drug_list)
    drug_list = [f"{random.choice(emoji_list)} {drug.ljust(max_len)}" for drug in drug_list]

    # Define the number of rows and columns based on the drug_list
    num_drugs = len(drug_list)
    metrics_per_row = min(4, num_drugs)  # Set the maximum columns per row
    num_containers = (num_drugs // metrics_per_row) + (num_drugs % metrics_per_row > 0)  # Round up

    drug_index = 0
    for container_index in range(num_containers):
        with st.container():
            cols = st.columns(metrics_per_row)
            for metric_index in range(metrics_per_row):
                if drug_index < num_drugs:  # Check if there are still drugs left to display
                    with cols[metric_index]:
                        with st.expander(drug_list[drug_index], expanded=True):
                            st.write()
                            st.metric(label="", value="1000 RCT", delta="40% pvalue<.05")
                            with st.expander("What does this treat?", expanded=False):
                                st.write("Hello world")
                        drug_index += 1

main()


