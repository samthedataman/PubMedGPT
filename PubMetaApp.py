# Generate grid of metrics
import streamlit as st
import random
import streamlit_nested_layout
import streamlit as st
import pandas as pd
import os
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from stuffthatworks.StuffThatWorksETL import run_jobs
from streamlitfunctions import *
import pandas as pd
import plotly.express as px
from PubMetaFrontEndFunctions import (
    fuzzy_match,
    set_custom_page_config,
    display_drugs_metrics,
    get_filtered_drug_list,
)


class SessionState:
    def __init__(self):
        self.selected_symptoms = []
        self.selected_diseases = []
        self.selected_drugs = []


button_style = """
    <style>
    .my-button {
        width: 100%;
        height: 60px;
        font-size: 18px;
    }
    </style>
    """
centered_content = """
    <style>
    .centered-content {
        text-align: center;
    }
    </style>
    """


def main():
    state = SessionState()
    set_custom_page_config()
    symptoms_df, triggers_df, comorbidities_df, treatments_df = run_jobs()
    df = get_data()
    df, symptoms_df, treatments_df = fuzzy_match(df, symptoms_df, treatments_df)

    drug_list = ["Drug A", "Drug B", "Drug C", "Drug D", "Drug E", "Drug F"]

    drug_data = {
        "Drug A": {
            "studies_count": 1000,
            "people_rank": 3,
            "proportion_of_significant_results": "40% pvalue<.05",
            "average_size": 200,
            "general_trend": "Positive",
            "pathologies": ["Pathology 1", "Pathology 2", "Pathology 3"],
            "average_citation_count": 50,
            "study_counts_over_time": [
                ("2020-01-01", 100),
                ("2020-02-01", 200),
                # more data points...
            ],
            "studies": [
                {
                    "link": "http://example.com/study1",
                    "citation_count": 100,
                    "date": "2020-01-01",
                },
                {
                    "link": "http://example.com/study2",
                    "citation_count": 200,
                    "date": "2020-02-01",
                },
                # more studies...
            ],
            "side_effects": [
                {"name": "Headache", "frequency": "Common"},
                {"name": "Nausea", "frequency": "Occasional"},
                {"name": "Dizziness", "frequency": "Rare"},
            ],
        },
        "Drug B": {
            "studies_count": 1500,
            "people_rank": 2,
            "proportion_of_significant_results": "50% pvalue<.05",
            "average_size": 180,
            "general_trend": "Negative",
            "pathologies": ["Pathology 4", "Pathology 5"],
            "average_citation_count": 60,
            "study_counts_over_time": [
                ("2020-01-01", 150),
                ("2020-02-01", 180),
                # more data points...
            ],
            "studies": [
                {
                    "link": "http://example.com/study3",
                    "citation_count": 80,
                    "date": "2020-01-01",
                },
                {
                    "link": "http://example.com/study4",
                    "citation_count": 120,
                    "date": "2020-02-01",
                },
                # more studies...
            ],
            "side_effects": [
                {"name": "Nausea", "frequency": "Common"},
                {"name": "Fatigue", "frequency": "Occasional"},
                {"name": "Rash", "frequency": "Rare"},
            ],
        },
        "Drug C": {
            "studies_count": 1200,
            "people_rank": 1,
            "proportion_of_significant_results": "20% pvalue<.05",
            "average_size": 190,
            "general_trend": "Neutral",
            "pathologies": ["Pathology 2", "Pathology 6"],
            "average_citation_count": 70,
            "study_counts_over_time": [
                ("2020-01-01", 110),
                ("2020-02-01", 160),
                # more data points...
            ],
            "studies": [
                {
                    "link": "http://example.com/study5",
                    "citation_count": 60,
                    "date": "2020-01-01",
                },
                {"link": "2020-02-01"},
                # more studies...
            ],
            "side_effects": [
                {"name": "Drowsiness", "frequency": "Common"},
                {"name": "Dry mouth", "frequency": "Occasional"},
                {"name": "Constipation", "frequency": "Rare"},
            ],
        },
        "Drug D": {
            "studies_count": 1000,
            "people_rank": 3,
            "proportion_of_significant_results": "40% pvalue<.05",
            "average_size": 200,
            "general_trend": "Positive",
            "pathologies": ["Pathology 1", "Pathology 2", "Pathology 3"],
            "average_citation_count": 50,
            "study_counts_over_time": [
                ("2020-01-01", 100),
                ("2020-02-01", 200),
                # more data points...
            ],
            "studies": [
                {
                    "link": "http://example.com/study1",
                    "citation_count": 100,
                    "date": "2020-01-01",
                },
                {
                    "link": "http://example.com/study2",
                    "citation_count": 200,
                    "date": "2020-02-01",
                },
                # more studies...
            ],
            "side_effects": [
                {"name": "Headache", "frequency": "Common"},
                {"name": "Nausea", "frequency": "Occasional"},
                {"name": "Dizziness", "frequency": "Rare"},
            ],
        },
        "Drug E": {
            "studies_count": 1000,
            "people_rank": 3,
            "proportion_of_significant_results": "40% pvalue<.05",
            "average_size": 200,
            "general_trend": "Positive",
            "pathologies": ["Pathology 1", "Pathology 2", "Pathology 3"],
            "average_citation_count": 50,
            "study_counts_over_time": [
                ("2020-01-01", 100),
                ("2020-02-01", 200),
                # more data points...
            ],
            "studies": [
                {
                    "link": "http://example.com/study1",
                    "citation_count": 100,
                    "date": "2020-01-01",
                },
                {
                    "link": "http://example.com/study2",
                    "citation_count": 200,
                    "date": "2020-02-01",
                },
                # more studies...
            ],
            "side_effects": [
                {"name": "Headache", "frequency": "Common"},
                {"name": "Nausea", "frequency": "Occasional"},
                {"name": "Dizziness", "frequency": "Rare"},
            ],
        },
        "Drug F": {
            "studies_count": 1000,
            "people_rank": 3,
            "proportion_of_significant_results": "40% pvalue<.05",
            "average_size": 200,
            "general_trend": "Positive",
            "pathologies": ["Pathology 1", "Pathology 2", "Pathology 3"],
            "average_citation_count": 50,
            "study_counts_over_time": [
                ("2020-01-01", 100),
                ("2020-02-01", 200),
                # more data points...
            ],
            "studies": [
                {
                    "link": "http://example.com/study1",
                    "citation_count": 100,
                    "date": "2020-01-01",
                },
                {
                    "link": "http://example.com/study2",
                    "citation_count": 200,
                    "date": "2020-02-01",
                },
                # more studies...
            ],
            "side_effects": [
                {"name": "Headache", "frequency": "Common"},
                {"name": "Nausea", "frequency": "Occasional"},
                {"name": "Dizziness", "frequency": "Rare"},
            ],
        },
    }

    # User Interface
    # User Interface
    with st.container():
        st.markdown(centered_content, unsafe_allow_html=True)  # Apply the custom CSS
        st.header("⚕️*PubMeta*⚕️")
        st.subheader("**A Rapid Meta-Analysis Generation Tool for Patients**")
        st.markdown(
            """Assisting patients around the world uncover and compare proven treatment options in a single webpage"""
        )

        with st.form("search_form"):
            col1, col2, col3 = st.columns(
                [4, 0.5, 1.5]
            )  # Custom widths for the columns

            with col1:
                keyword = st.text_area(
                    "Tell us what symptoms, diseases, or drugs you are interested in learning about",
                    height=200,
                    max_chars=250,
                )

            with col2:
                st.markdown(
                    "<div style='display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;'>"
                    "<h3 style='text-align: center;'>OR</h3>"
                    "</div>",
                    unsafe_allow_html=True,
                )

            with col3:
                state.selected_symptoms = st.multiselect(
                    "Select symptoms",
                    options=symptoms_df["symptoms"],
                    default=state.selected_symptoms,
                )
                state.selected_diseases = st.multiselect(
                    "Select diseases",
                    options=symptoms_df["symptoms"],
                    default=state.selected_diseases,
                )  # Replace all_diseases with a list of all diseases
                state.selected_drugs = st.multiselect(
                    "Select drugs", options=drug_list, default=state.selected_drugs
                )

            search_button = st.form_submit_button(
                label="Generate Meta Analysis",
                help="Click to generate results",
                use_container_width=True,
            )

            # Display a loading state while the search is in progress
            if search_button:
                with st.spinner("Searching..."):
                    filtered_drug_list = get_filtered_drug_list(
                        drug_list,
                        drug_data,
                        keyword,
                        state.selected_symptoms,
                        state.selected_diseases,
                        state.selected_drugs,
                    )
            display_drugs_metrics(drug_list, drug_data)


# Call your main function
if __name__ == "__main__":
    main()
