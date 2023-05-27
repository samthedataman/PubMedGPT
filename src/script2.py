from PubMetaAppBackEndFunctions import (
    get_condition_treatments_for_pubmed_from_STW,
    get_results_and_predictions,
)


def main():
    DiseaseTreatments = get_condition_treatments_for_pubmed_from_STW(
        query="""SELECT * 
    FROM `airflow-test-371320.PubMeta.CleanedUpStuffThatWorksTreatments` 
    WHERE TreatmentCategory IN ('Alternative therapy', 'Other', 'Dietary change');
    """
    )
    get_results_and_predictions(DiseaseTreatments)
    print("Data upload process completed.")


if __name__ == "__main__":
    main()
