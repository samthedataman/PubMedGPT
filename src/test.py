import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Instantiate model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")
base_model = AutoModelForCausalLM.from_pretrained("mosaicml/mpt-7b-instruct",
                                                        offload_folder="model/",
                                                        trust_remote_code=True,
                                                        device_map=None)
# Ask a question
question = "What is a quoll?"

# Encode the question and generate a response
input_ids = tokenizer.encode(question, return_tensors='pt')

generated_ids = base_model.generate(input_ids)

# Decode the response
answer = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

print(answer)



#   'mosaicml/mpt-7b-instruct',
#   trust_remote_code=True
# )

# gptj = GPT4All("ggml-gpt4all-j-v1.3-groovy")
# condition = "alzhiemers"
# truncated_text = "Cognitive impairment impacts the quality of life and increases morbidity and mortality rates. The prevalence of and factors associated with cognitive impairment have become important issues as the age of people living with HIV(PLWH) increases. In 2020, We conducted a cross-sectional study to survey the cognitive impairment among PLWH in three hospitals in Taiwan with Alzheimer Disease-8 (AD8) questionnaire. The average age of 1,111 individuals was 37.54 ± 10.46 years old, and their average duration to live with HIV was 7.12 ± 4.85 years. The rate of impaired cognitive function was 2.25% (N = 25) when AD8 score ≥ 2 was a positive finding for cognitive impairment. Aging (p = .012), being less educated (p = 0.010), and having a longer duration to live with HIV (p = .025) were significantly associated with cognitive impairment. Multivariate logistic regression analysis revealed that only the duration of living with HIV was a significant factor related to the tendency of cognitive impairment (p = .032). The risk of cognitive impairment increased by 1.098 times for every additional year to live with HIV. In conclusion, the prevalence of cognitive impairment among PLWH in Taiwan was 2.25%. Healthcare personnel should be sensitive to the changes in PLWH's cognitive function as they age."
# prompt = f"""Tell me the conclusion from this PubMed Paper on this {condition}: \n{truncated_text}\n\n"""
# messages = [{"role": "user", "content": prompt}]
# answer = gptj.chat_completion(messages)
# for i,x in gptj.chat_completion(messages).items():
#     print(i,"====",x)