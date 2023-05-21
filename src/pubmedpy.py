import pandas as pd
from pymed import PubMed
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
import os
import regex as re


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


def get_results_and_predictions(condition, treatment):
    os.environ["OPENAI_API_KEY"] = "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"

    with open("/Users/samsavage/PythonProjects/PubMedGPT/data/openaikeys.json") as f:
        keys = json.load(f)

    pubmed = PubMed(tool="MyTool", email="samuel.savage@uconn.edu")
    condition = condition
    treatment = treatment

    query = f'({condition}[Title/Abstract] AND {treatment}[Title/Abstract] AND ("Randomized Controlled Trial"[Publication Type] OR "Double-Blind Method"[MeSH Terms] OR "Clinical Trial"[Publication Type]))'

    results = pubmed.query(query=query, max_results=10)

    article_dicts = []
    for article in results:
        # Convert article to dict and append to list
        article_dict = article.toDict()
        article_dicts.append(article_dict)

    df = pd.DataFrame(article_dicts)

    prompt = PromptTemplate(
        input_variables=[
            "title",
            "results",
            "conclusions",
        ],
        template="""
                        CONTEXT:

                        You are a medical PHD student at harvard reviewing pubmed medical journal articles to perform a meta analysis 

                        You are reviwing a paper titled: {title}

                        The paper had these conclusions: {conclusions}
                        
                        The paper had these results : {results} 
                        
                        TASK : Return a 5 labels for each paper

                        1) Treatment efficacy, ONLY CHOOSE FROM THESE 3 OPTIONS BELOW:
                        
                            (Stastically Significant (CONTEXT: if p value mentioned less than .05))
                            (Directionaly Significant (CONTEXT: if p value is not mentioned but their is an effect))
                            (No Effect (CONTEXT:Results were inclonclusive))

                        2) Sample Size of Study (Number of Total Participants)

                        3) Study Type (Meta, Randomized, Clinical, Double Blind,Qualitative)

                        4) Disease Specific Symptoms Addressed by Study (Specific Metrics relative to the disease)

                        5) Trend/Correlation Discovered

                        FORMAT REQUIRMENTS:

                        Return a Python LIST [], here is an EXAMPLE:

                        ["Stastically Significant","1030","Meta Analyis",["Disease Activity, ESR, and CRP"],"Negative Correlation between Vitamin D levels and Disease Activity"]

                        INCLUDE NO OTHER TEXT BUT THE LIST OUPUT!!!
                        """,
    )

    llm = OpenAI(
        model_name="text-davinci-003",  # default model
        temperature=0.2,  # temperature dictates how whacky the output should be
    )

    llmchain = LLMChain(llm=llm, prompt=prompt)

    df["MetaGPT"] = df.apply(
        lambda row: llmchain.run(
            title=row["title"], results=row["results"], conclusions=row["conclusions"]
        ),
        axis=1,
    )

    import ast

    # Function to handle the third element when it's a list
    def split_list(x):
        if isinstance(x, list):
            return pd.Series(x)
        return pd.Series([x])

    # Remove the 'ANSWER: ' prefix and parse strings into python objects
    df["MetaGPT"] = df["MetaGPT"].str.replace("ANSWER: ", "", regex=False).str.strip()
    df["SignificanceMetricsSymptomsAndTrends"] = (
        df["conclusions"] + " " + df["results"]
    ).apply(extract_significance_metrics_and_symptoms)

    df.to_csv(f"pre_cleaned_{treatment}_{condition}.csv")
    try:
        df["MetaGPT"] = df["MetaGPT"].apply(ast.literal_eval)

        # Split the list into multiple columns
        df[
            ["efficacy", "size", "StudyType", "SymptomsTreated", "Trend"]
        ] = pd.DataFrame(df["MetaGPT"].to_list(), index=df.index)

        # Find the maximum number of elements in the lists in the third column
        max_elements = (
            df["SymptomsTreated"]
            .apply(lambda x: len(x) if isinstance(x, list) else 1)
            .max()
        )

        # Create a list of column names based on that
        new_col_names = [f"SymptomsTreated_{i+1}" for i in range(max_elements)]

        # Split the third column into multiple columns
        df[new_col_names] = df["SymptomsTreated"].apply(split_list)

        # Drop the original column
        df = df.drop(columns=["MetaGPT"])

        df.to_csv(f"{condition}_{treatment}.csv")
    except:
        df.to_csv(f"pre_cleaned_{treatment}_{condition}_2.csv")

    return df


get_results_and_predictions("adhd", "methylphenidate")

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
