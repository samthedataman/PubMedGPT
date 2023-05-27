Apologies for the oversight. Here's the corrected version with the data pipeline changes highlighted:

# Plan Organizer

## Launch Steps
- **Data Pipeline Changes**:

  - Rescrape for a full list of conditions for treatments, symptoms, side effects, comorbidities, and triggers.
  
  - Rescrape PubMeta for all papers.
  - Use Chat GPT to parse statistical significance.
  - Add drug costs to the pipeline (maybe scrape from PatientsLikeMe?).

## Model Changes
- Make the model faster (consider not using faiss and test with chromadb).
- Make the model encompass more meta data or concatenate data better.
- Use if columns to indicate the most cited paper.
- Add in Patient Data* around symptoms.
- Test different chunking sizes.

## UI/UX Changes
- Show Chatbot immediately.
- Provide options for users.
- Implement BERT to recognize drugs or diseases matching the query and filter the dataframe accordingly.
- Consider the customer journey of the user, making it simple but easy to handle complexity.
- Add filters for Stat Sig Score.
- Add filters for Journal, Journal Type, and Study Type.
- Add Rank to Drug Card.
- Add User Experiences.
- Add User Reports to Drug Card.
- Add a visually appealing chart to the tile Card.
- Add studies published in the last 6 months.
- Highlight the most cited study.
- Highlight the newest study with the most citations.

## PayWall Changes
- Add functions for direct query to PubMed.
- Determine which features to make paid and when the freemium version stops.
- Add research note pad and allow text input from the chatbot.

Please use this updated version, and once again, I apologize for the oversight.