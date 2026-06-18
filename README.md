# Grounded MCQ Generator

A simple Python app that uploads a PDF or Word `.docx` file, extracts text with Google Cloud Document AI, and uses Vertex AI Gemini Flash to generate cited multiple-choice questions.

## Architecture

```text
Streamlit UI on Cloud Run
  -> Document AI Enterprise Document OCR processor
  -> Vertex AI Gemini Flash
  -> JSON validation
  -> questions plus answer key/citations
```

The app validates that every generated answer includes a citation quote found on the cited extracted page. If Gemini returns uncited or malformed output, the app shows an error instead of displaying unsupported questions.

## Required Google Cloud setup

Create or choose a Google Cloud project with billing enabled, then:

1. Enable the Document AI API and Vertex AI API.
2. Create a Document AI OCR processor, such as an Enterprise Document OCR processor.
3. Give the Cloud Run service account permission to call Document AI and Vertex AI.
4. Set these environment variables when running the app:

```text
GOOGLE_CLOUD_PROJECT=your-project-id
DOCUMENT_AI_LOCATION=us
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
VERTEX_AI_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
```

Optional cost-control settings:

```text
MAX_UPLOAD_MB=5
MAX_PAGES=30
MAX_QUESTIONS=20
MAX_SOURCE_CHARS=80000
```

## Run locally

Authenticate with Google Cloud Application Default Credentials first:

```bash
gcloud auth application-default login
```

Then install and run:

```bash
python3 -m pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Cloud Run

Build and deploy the container:

```bash
gcloud run deploy grounded-mcq-generator \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id,DOCUMENT_AI_LOCATION=us,DOCUMENT_AI_PROCESSOR_ID=your-processor-id,VERTEX_AI_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash
```

For a private app, omit `--allow-unauthenticated` and configure access with IAM.

## Test

The unit tests avoid live Google Cloud calls and focus on validation, prompt construction, formatting, and Document AI response parsing helpers.

```bash
python3 -m unittest discover -s tests -v
```
