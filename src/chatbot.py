import streamlit as st
from streamlit_chat import message
import streamlit_nested_layout
import pandas as pd
from langchain.llms import OpenAI
import os
from google.cloud import bigquery
from google.oauth2 import service_account
import langchain
from langchain.chains import ConversationalRetrievalChain
import openai
import langchain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import DataFrameLoader
from langchain.memory import ConversationBufferMemory
import math
import pandas as pd
from PubMetaAppBackEndFunctions import *

os.environ["OPENAI_API_KEY"] = "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"


# get unique diseases
@st.cache_data
def get_unique_diseases():
    project_name = "airflow-test-371320"
    key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
    creds = service_account.Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)
    query = f"""SELECT disease
    FROM `airflow-test-371320.PubMeta.ArticlesM1CHIP`"""
    query_job = client.query(query)
    results = query_job.result().to_dataframe()
    diseases = [d for d in results["disease"].unique()]
    return diseases


@st.cache_data
def get_treatments_for_diseases(diseases):
    project_name = "airflow-test-371320"
    key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
    creds = service_account.Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)
    # if diseases has been selected by user split them up and inject back into query to get disease specific treatments for users
    if diseases:
        placeholders = ", ".join(f'"{d}"' for d in diseases)
        query = f"""SELECT treatment
        FROM `airflow-test-371320.PubMeta.ArticlesM1CHIP`
          where disease in ({placeholders}) """
        query_job = client.query(query)
        results = query_job.result().to_dataframe()
        DiseaseTreatments = [d for d in results["treatment"].unique()]
        return DiseaseTreatments


@st.cache_data
def get_disease_by_treatment_data(diseases, treatments):
    if not diseases and not treatments:
        diseases = ""
        treatments = ""
    else:
        diseases = diseases
        treatments = treatments
    project_name = "airflow-test-371320"
    key_path = "/Users/samsavage/PythonProjects/PubMedGPT/data/gcp_creds.json"
    creds = service_account.Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_name)

    if diseases and treatments:
        # get unique diseases
        udiseases = ", ".join(f'"{d}"' for d in diseases)
        utreatments = ", ".join(f'"{t}"' for t in treatments)

        query = f"""SELECT *
        FROM `airflow-test-371320.PubMeta.ArticlesM1CHIP` 
        where disease in ({udiseases})
          and treatment in ({utreatments})"""

        query_job = client.query(query)
        results = query_job.result().to_dataframe()
        results["full_text"] = (
            results["title"]
            + results["abstract"]
            + results["results"]
            + results["conclusions"]
        )
    if diseases:
        udiseases = ", ".join(f'"{d}"' for d in diseases)

        query = f"""SELECT *
        FROM `airflow-test-371320.PubMeta.ArticlesM1CHIP`  where disease in ({udiseases})"""

        query_job = client.query(query)
        results = query_job.result().to_dataframe()
        results["full_text"] = (
            results["title"]
            + results["abstract"]
            + results["results"]
            + results["conclusions"]
        )
    if treatments:
        utreatments = ", ".join(f'"{t}"' for t in treatments)

        query = f"""SELECT *
        FROM `airflow-test-371320.PubMeta.ArticlesM1CHIP`  where treatment in ({utreatments})"""

        query_job = client.query(query)
        results = query_job.result().to_dataframe()
        results["full_text"] = (
            results["title"]
            + results["abstract"]
            + results["results"]
            + results["conclusions"]
        )
    else:
        query = f"""SELECT *
        FROM `airflow-test-371320.PubMeta.ArticlesM1CHIP`"""
        query_job = client.query(query)
        results = query_job.result().to_dataframe()
        results["full_text"] = (
            results["title"]
            + results["abstract"]
            + results["results"]
            + results["conclusions"]
        )

    return results


def search_documents(df: pd.DataFrame, full_user_question: str):
    os.environ["OPENAI_API_KEY"] = "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"

    df_loader = DataFrameLoader(df, page_content_column="full_text")
    df_docs = df_loader.load()

    embeddings = OpenAIEmbeddings()

    faiss_db = FAISS.from_documents(df_docs, embeddings)

    docs = faiss_db.similarity_search(full_user_question)
    # search_type="similarity_score_threshold",
    # search_kwargs={"score_threshold": 0.7})
    return docs[0].page_content


def retreive_best_answer(df: pd.DataFrame, full_user_question: str):
    os.environ["OPENAI_API_KEY"] = "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"

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    df_loader = DataFrameLoader(df, page_content_column="full_text")
    df_docs = df_loader.load()

    embeddings = OpenAIEmbeddings()

    faiss_db = FAISS.from_documents(df_docs, embeddings)

    qa = ConversationalRetrievalChain.from_llm(
        OpenAI(temperature=0.1),
        faiss_db.as_retriever(),
        memory=memory,
        chain_type="stuff",
    )

    results = qa({"question": full_user_question})

    return results["answer"]


def display_treatments_metrics(df, disease_list=None):
    if not disease_list:
        treatment_list = df["treatment"].unique().tolist()
        num_treatments = len(treatment_list)
        metrics_per_row = min(3, num_treatments)  # Set the maximum columns per row
        num_containers = math.ceil(num_treatments / metrics_per_row)

        treatment_index = 0
        for _ in range(num_containers):
            with st.container():
                cols = st.columns(metrics_per_row)
                for metric_index in range(metrics_per_row):
                    if treatment_index < num_treatments:
                        # Filter the DataFrame for records associated with this treatment
                        treatment = treatment_list[treatment_index]
                        treatment_data = df[df["treatment"] == treatment]

                        # Calculate some example metrics from the treatment data
                        num_studies = treatment_data[
                            "ArticlePmid"
                        ].nunique()  # Number of unique studies
                        avg_citations = treatment_data[
                            "CitationCounts"
                        ].mean()  # Average citation counts
                        # Please replace these with your actual metrics

                        with cols[metric_index]:
                            with st.expander(f"Treatment: {treatment}", expanded=True):
                                st.markdown(
                                    f"<h3 style='text-align: center;'>{treatment}</h3>",
                                    unsafe_allow_html=True,
                                )
                                with st.expander("Studies"):
                                    # Display the number of studies
                                    st.metric(
                                        label="Number of Studies", value=num_studies
                                    )
                                    # Add more metrics as needed, using data from treatment_data

                                with st.expander("Metrics"):
                                    # Display the average citation count
                                    st.metric(
                                        label="Average Citation Count",
                                        value=(avg_citations),
                                    )
                                    # Add more metrics as needed, using data from treatment_data

                                with st.expander("Full Studies:", expanded=False):
                                    # Show a list of studies for this treatment
                                    for _, row in treatment_data.iterrows():
                                        st.markdown(
                                            f"[{row['title']}]({row['ArticleLink']})",
                                            unsafe_allow_html=True,
                                        )

                        treatment_index += 1
    else:
        df = df[df["disease"].isin(disease_list)]
        treatment_list = df["treatment"].unique().tolist()
        num_treatments = len(treatment_list)
        metrics_per_row = min(3, num_treatments)  # Set the maximum columns per row
        num_containers = math.ceil(num_treatments / metrics_per_row)

        treatment_index = 0
        for _ in range(num_containers):
            with st.container():
                cols = st.columns(metrics_per_row)
                for metric_index in range(metrics_per_row):
                    if treatment_index < num_treatments:
                        # Filter the DataFrame for records associated with this treatment
                        treatment = treatment_list[treatment_index]
                        treatment_data = df[df["treatment"] == treatment]

                        # Calculate some example metrics from the treatment data
                        num_studies = treatment_data[
                            "ArticlePmid"
                        ].nunique()  # Number of unique studies
                        avg_citations = treatment_data[
                            "CitationCounts"
                        ].mean()  # Average citation counts
                        # Please replace these with your actual metrics

                        with cols[metric_index]:
                            with st.expander(f"Treatment: {treatment}", expanded=True):
                                st.markdown(
                                    f"<h3 style='text-align: center;'>{treatment}</h3>",
                                    unsafe_allow_html=True,
                                )
                                with st.expander("Studies"):
                                    # Display the number of studies
                                    st.metric(
                                        label="Number of Studies", value=num_studies
                                    )
                                    # Add more metrics as needed, using data from treatment_data

                                with st.expander("Metrics"):
                                    # Display the average citation count
                                    st.metric(
                                        label="Average Citation Count",
                                        value=(avg_citations),
                                    )
                                    # Add more metrics as needed, using data from treatment_data

                                with st.expander("Full Studies:", expanded=False):
                                    # Show a list of studies for this treatment
                                    for _, row in treatment_data.iterrows():
                                        st.markdown(
                                            f"[{row['title']}]({row['ArticleLink']})",
                                            unsafe_allow_html=True,
                                        )

                        treatment_index += 1


def chat_bot_streamlit_openai():
    if "generated" not in st.session_state:

        st.session_state["generated"] = []

    if "past" not in st.session_state:
        st.session_state["past"] = []

    # We will get the user's input by calling the get_text function
    st.title("⚕️*PubMeta*⚕️ A Rapid Meta-Analysis Chatbot ")

    st.subheader(
        """The only research tool on the Internet that combines the latest medical research with aggregated crowd sourced medical data in a single chat-bot"""
    )

    col1, col2 = st.columns(2)

    with st.expander("What Conditions are you Interested in?", expanded=True):
        with col1:
            input_disease = st.sidebar.multiselect(
                "If you have a disease in mind pick one",
                get_unique_diseases(),
                key="input",
            )
            if not input_disease:
                input_disease = ""

            if "input_disease" not in st.session_state:
                st.session_state.input_disease = False

            if input_disease or st.session_state.input_disease:
                st.session_state.input_disease = True

        with col2:
            if st.session_state.input_disease:
                input_treatment = st.sidebar.multiselect(
                    f"Pick a Treatment relative to {' '.join(input_disease)}",
                    get_treatments_for_diseases(input_disease),
                    key="treatment",
                )
                if not input_treatment:
                    input_treatment = ""

                if "input_treatment" not in st.session_state:
                    st.session_state.input_treatment = False

                if input_treatment or st.session_state.input_disease:
                    st.session_state.input_treatment = True
            else:
                input_treatment = ""

        # from disease list generate the question format string
        # full_user_question = st.text_input(
        #     "User:",
        #     f"Hello, can you tell me about {' '.join(input_disease)} and any new treatment advances such as : {' '.join(input_treatment)}",
        #     key="new_input",
        # )
        
        full_user_question = st.text_input(
            "Chat with me!",
            f"Hello, can you tell me about {' '.join(input_disease)} and any new treatment advances such as : {' '.join(input_treatment)}",
            key="new_input",
        )
        bert_list = classify_medical_text(full_user_question)
        predicted_labels = classify_medical_text_insight(full_user_question)

        st.write(bert_list)

        if "full_user_question" not in st.session_state:
            st.session_state.full_user_question = False

        if full_user_question or st.session_state.input_disease:
            st.session_state.full_user_question = True

        enter_button = st.button("Chat with PubMeta")
        # with vector store ask question
        if full_user_question and enter_button:
            # get query based on user input
            df = get_disease_by_treatment_data(input_disease, input_treatment)
            # get similar results from db
            search_response = retreive_best_answer(df, full_user_question)

            # store the output
            st.session_state.past.append(full_user_question)
            st.session_state.generated.append(search_response)
            
        if "first_run" not in st.session_state:
            st.session_state["first_run"] = True
            message("Hello! I'm your chatbot. How can I assist you today?")

        if st.session_state["generated"]:
            for i in range(len(st.session_state["generated"]) - 1, -1, -1):
                message(st.session_state["generated"][i], key=str(i))
                message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")

        panel_df = get_disease_by_treatment_data(input_disease, input_treatment)
        display_treatments_metrics(panel_df, input_disease)


chat_bot_streamlit_openai()
