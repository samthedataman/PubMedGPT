import streamlit as st
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from stuffthatworks.StuffThatWorksETL import run_jobs
import pandas as pd
import plotly.express as px
import streamlit as st

symptoms_df, triggers_df, comorbidities_df, treatments_df = run_jobs()


def visualize_data(df, nlargest=10):
    # Convert 'DateScraped' column to datetime format
    df["DateScraped"] = pd.to_datetime(df["DateScraped"])
    df["num_reports"] = df["num_reports"].astype("int")

    # Filter top 100 conditions by num_reports
    top_100_conditions = (
        df.groupby("conditions")["num_reports"].sum().nlargest(nlargest).index
    )
    df = df[df["conditions"].isin(top_100_conditions)]

    # Create a pivot table
    for i in df.columns.unique():
        if i == "symptoms":
            pivot_df = df.pivot_table(
                index="conditions",
                columns="symptoms",
                values="num_reports",
                aggfunc="sum",
                fill_value=0,
            )

            # Convert pivot table back to DataFrame for the plot
            plot_df = pivot_df.reset_index().melt(
                id_vars="conditions", value_name="num_reports"
            )

            # Create the stacked bar chart
            fig = px.bar(
                plot_df,
                x="conditions",
                y="num_reports",
                color="symptoms",
                title="Top Conditions by Number of Reports split by Symptoms",
                labels={
                    "conditions": "Conditions",
                    "num_reports": "Number of Reports",
                    "symptoms": "Symptoms",
                },
                category_orders={"conditions": top_100_conditions.tolist()},
                height=500,
            )

            # Display the chart using Streamlit
            st.plotly_chart(fig)

    for i in df.columns.unique():
        if i == "treatments":
            pivot_df = df.pivot_table(
                index="conditions",
                columns="treatments",
                values="num_reports",
                aggfunc="sum",
                fill_value=0,
            )

            # Convert pivot table back to DataFrame for the plot
            plot_df = pivot_df.reset_index().melt(
                id_vars="conditions", value_name="num_reports"
            )

            # Create the stacked bar chart
            fig = px.bar(
                plot_df,
                x="conditions",
                y="num_reports",
                color="treatments",
                title="Top Conditions by Number of Reports split by treatments",
                labels={
                    "conditions": "Conditions",
                    "num_reports": "Number of Reports",
                    "treatments": "Treatments",
                },
                category_orders={"conditions": top_100_conditions.tolist()},
                height=500,
            )

            # Display the chart using Streamlit
            st.plotly_chart(fig)

    for i in df.columns.unique():
        if i == "triggers":
            pivot_df = df.pivot_table(
                index="conditions",
                columns="triggers",
                values="num_reports",
                aggfunc="sum",
                fill_value=0,
            )

            # Convert pivot table back to DataFrame for the plot
            plot_df = pivot_df.reset_index().melt(
                id_vars="conditions", value_name="num_reports"
            )

            # Create the stacked bar chart
            fig = px.bar(
                plot_df,
                x="conditions",
                y="num_reports",
                color="triggers",
                title="Top Conditions by Number of Reports split by triggers",
                labels={
                    "conditions": "Conditions",
                    "num_reports": "Number of Reports",
                    "triggers": "Triggers",
                },
                category_orders={"conditions": top_100_conditions.tolist()},
                height=500,
            )
            st.plotly_chart(fig)

    for i in df.columns.unique():
        if i == "comorbidities":
            pivot_df = df.pivot_table(
                index="conditions",
                columns="comorbidities",
                values="num_reports",
                aggfunc="sum",
                fill_value=0,
            )

            # Convert pivot table back to DataFrame for the plot
            plot_df = pivot_df.reset_index().melt(
                id_vars="conditions", value_name="num_reports"
            )

            # Create the stacked bar chart
            fig = px.bar(
                plot_df,
                x="conditions",
                y="num_reports",
                color="comorbidities",
                title="Top Conditions by Number of Reports split by comorbidities",
                labels={
                    "conditions": "Conditions",
                    "num_reports": "Number of Reports",
                    "comorbidities": "Comorbidities",
                },
                category_orders={"conditions": top_100_conditions.tolist()},
                height=500,
            )

            # Display the chart using Streamlit
            st.plotly_chart(fig)


# Existing symptoms selector
symptoms_selector = st.multiselect(
    "Select the Symptoms of Interest", [i for i in symptoms_df.symptoms.unique()]
)
visualize_data(symptoms_df[(symptoms_df["symptoms"].isin(symptoms_selector))])

# New treatment selector
treatments_selector = st.multiselect(
    "Select the Treatments of Interest", [i for i in treatments_df.treatments.unique()]
)
visualize_data(treatments_df[(treatments_df["treatments"].isin(treatments_selector))])

# New triggers selector
triggers_selector = st.multiselect(
    "Select the Triggers of Interest", [i for i in triggers_df.triggers.unique()]
)
visualize_data(triggers_df[(triggers_df["triggers"].isin(triggers_selector))])

# New comorbidities selector
comorbidities_selector = st.multiselect(
    "Select the Comorbidities of Interest",
    [i for i in comorbidities_df.comorbidities.unique()],
)
visualize_data(
    comorbidities_df[(comorbidities_df["comorbidities"].isin(comorbidities_selector))]
)

# Existing conditions selector
condtions_selector = st.multiselect(
    "Select the Condition of Interest", [i for i in symptoms_df.conditions.unique()]
)
visualize_data(symptoms_df[(symptoms_df["conditions"].isin(condtions_selector))])
# visualize_data(triggers_df)
# visualize_data(comorbidities_df)

# Assuming you have a DataFrame called 'df'
