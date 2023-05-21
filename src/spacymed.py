import spacy
import pandas as pd
import re
from pymed import PubMed

nlp = spacy.load("en_core_web_sm")


def extract_trend(text):
    if "increase" in text or "positive" in text or "improved" in text:
        return "Positive"
    elif "decrease" in text or "negative" in text or "worsened" in text:
        return "Negative"
    else:
        return "No clear trend"


def extract_sample_size(text):
    match = re.search(
        r"(\d+)\s*(patients|participants|subjects|individuals)", text, re.IGNORECASE
    )
    return int(match.group(1)) if match else None


def extract_symptoms(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "DISEASE"]


def extract_study_type(text):
    doc = nlp(text)
    return [
        token.text
        for token in doc
        if token.text.lower()
        in ["meta", "randomized", "clinical", "double blind", "qualitative"]
    ]


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
    pubmed = PubMed(tool="MyTool", email="samuel.savage@uconn.edu")

    query = f'({condition}[Title/Abstract] AND {treatment}[Title/Abstract] AND ("Randomized Controlled Trial"[Publication Type] OR "Double-Blind Method"[MeSH Terms] OR "Clinical Trial"[Publication Type]))'
    results = pubmed.query(query=query, max_results=1000)

    article_dicts = []
    for article in results:
        # Convert article to dict and append to list
        article_dict = article.toDict()
        article_dicts.append(article_dict)

    df = pd.DataFrame(article_dicts)

    df["Trend"] = (df["conclusions"] + " " + df["results"]).apply(extract_trend)
    df["SampleSize"] = (df["conclusions"] + " " + df["results"]).apply(
        extract_sample_size
    )
    df["Symptoms"] = (df["conclusions"] + " " + df["results"]).apply(extract_symptoms)
    df["StudyType"] = (df["conclusions"] + " " + df["results"]).apply(
        extract_study_type
    )
    df["SignificanceMetricsSymptomsAndTrends"] = (
        df["conclusions"] + " " + df["results"]
    ).apply(extract_significance_metrics_and_symptoms)

    return df


def main():
    condition = "cancer"  # Replace with your desired condition
    treatment = "vitamin d"  # Replace with your desired treatment

    df = get_results_and_predictions(condition, treatment)
    print(df)  # Replace with your desired output or further processing
    df.to_csv(f"{condition}_{treatment}_spacy.csv")


if __name__ == "__main__":
    main()
