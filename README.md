# Hybrid Resume Parsing System

A production-ready FastAPI application that parses resumes from PDF and DOCX files using a hybrid approach:

- Regex for deterministic fields such as email, phone, LinkedIn, and GitHub
- Google Gemini for contextual extraction such as summary, skills, education, and experience
- A merge layer that prioritizes regex values for contact fields

## Installation

```bash
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file in the project root with your Gemini API key:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

## How to Obtain a Gemini API Key

1. Visit Google AI Studio.
2. Create a new API key.
3. Paste it into the `.env` file above.

## Running the Server

```bash
uvicorn app:app --reload
```

The app will be available at `http://127.0.0.1:8000`.

## API Endpoints

### POST /auth/register

Register a new user.

### POST /auth/login

Authenticate and receive a JWT token.

### POST /auth/logout

Logout endpoint.

### POST /auth/forgot-password

Request a password reset.

### POST /auth/reset-password

Reset a password.

### GET /users/profile

Get the authenticated user profile.

### PUT /users/profile

Update the authenticated user profile.

### PUT /users/change-password

Change the authenticated user's password.

### DELETE /users/profile

Delete the authenticated user account.

### POST /resume/upload

Upload a resume, parse it with the existing hybrid parser, and save parsed data to the database.

### POST /parse-resume

Legacy parser endpoint for PDF/DOCX resume parsing without database persistence.

### Sample Request

```bash
curl -X POST "http://127.0.0.1:8000/parse-resume" \
  -F "file=@sample_resume.pdf"
```

### Sample Response

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-123-4567",
  "linkedin": "https://www.linkedin.com/in/johndoe",
  "github": "https://github.com/johndoe",
  "address": "",
  "professional_summary": "Experienced software engineer.",
  "education": [],
  "skills": ["Python", "FastAPI"],
  "technical_skills": ["Python", "FastAPI"],
  "soft_skills": ["Communication"],
  "experience": [],
  "projects": [],
  "certifications": [],
  "internships": [],
  "languages": [],
  "achievements": [],
  "publications": []
}
```

## Project Structure

- `app.py`: FastAPI entrypoint
- `routes/upload.py`: Resume upload and parsing endpoint
- `services/file_parser.py`: PDF/DOCX text extraction
- `services/regex_parser.py`: Regex-based extraction
- `services/llm_parser.py`: Gemini-based extraction
- `services/merge.py`: Merging strategy
- `models/schema.py`: Pydantic response models

## RAG-Based Internship Matching

The application now includes an internship retrieval pipeline:

1. Parse the candidate resume with the existing Regex + Gemini hybrid parser.
2. Convert the structured candidate data into an embedding document.
3. Embed the internship dataset with Gemini Embeddings (`gemini-embedding-001`).
4. Store normalized internship vectors in FAISS using cosine similarity via inner product.
5. Retrieve the top relevant internships with similarity scores.
6. Optionally pass only the candidate data and retrieved internships to Gemini for a grounded RAG explanation.

### Internship endpoints

- `GET /internships` — view the internship dataset.
- `POST /internships/index` — generate/rebuild the FAISS internship index.
- `POST /internships/match` — match an already extracted candidate JSON object.
- `POST /internships/match-resume` — demo endpoint used by the simple frontend; upload PDF/DOCX and receive parsed candidate data plus matches.

### Frontend

Open `http://127.0.0.1:8000/` after starting the server. The page provides resume upload, extracted candidate information, top internship matches, similarity scores, and the grounded RAG explanation.

### Building the vector database

The first matching request requires a FAISS index. Run:

```bash
curl -X POST http://127.0.0.1:8000/internships/index
```

or use the `/internships/index` endpoint from Swagger at `http://127.0.0.1:8000/docs`.
