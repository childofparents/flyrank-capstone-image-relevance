# AI Image Understanding & Content Matching Engine

## Overview
This system analyzes Pexels, an image library, understands the contents using a vision model, and automatically matches the right image to the right blog post based on semantic meaning. It includes a mismatch guard designed to recommend images when confident and safely reject them when not.

## Architecture
(Placeholder for architecture diagram or image link)
* **Images:** Processed via a background batch job -> Gemini Flash Vision Model -> Validated JSON Metadata -> Gemini Embeddings.
* **Posts:** Text -> Gemini Embeddings.
* **Matching:** Semantic Similarity Search -> Mismatch Guard (confidence + tags) -> Recommendation or Rejection.

## Setup and Run Instructions

### Prerequisites
* Docker and Docker Compose
* Python 3.10+
* Google Gemini API Key

### Running the Application
1. Clone the repository.
2. Copy `.env.example` to `.env` and add your API keys.
3. Start the application and database:
   ```bash
   docker compose up --build
   ```
### Seed the database with the initial image dataset:
```bash
# Add exact seed command here (e.g., python scripts/seed.py)]
```

## Testing and Evaluation
To run the automated test suite and check the mismatch guard:
```bash
# Add exact test command here (e.g., pytest)
```
### Evaluation Metric:
* Top-1 Precision: [Insert % here before demo]

## Limitations
* Currently processes a small corpus of ~50 images. 
* Relies on Gemini's free tier, so processing large batches is subject to rate limits. 
* The semantic similarity threshold is tuned specifically for the provided categories (e.g., animals/wildlife) and may require adjustment for fundamentally different datasets.