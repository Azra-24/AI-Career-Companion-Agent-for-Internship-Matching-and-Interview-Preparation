# AI Career Companion Agent for Internship Matching and Interview Preparation

An AI-powered career assistance platform that helps students and job seekers analyze resumes, find suitable internships, identify skill gaps, generate cover letters, track applications, and prepare for interviews.


## Project Overview

The AI Career Companion Agent provides an end-to-end career assistance experience. It analyzes uploaded resumes using document extraction, regular expressions, and AI-based analysis. The extracted candidate profile is used for semantic internship matching through embeddings and FAISS.

The platform also provides ATS analysis, skill-gap analysis, personalized cover letter generation, interview preparation, application tracking, and AI-powered career assistance.

## Key Features

* User registration, login, and session management
* PDF and DOCX resume upload and parsing
* Hybrid resume analysis using Regex and Groq AI
* AI-based candidate profile extraction
* Semantic internship matching using FAISS
* 12-role internship catalog with INR (₹) stipend information
* RAG-based internship explanations
* ATS resume analysis
* Skill gap analysis
* Personalized cover letter generation
* 5-stage application tracker:

  * Applied
  * Skill Screening
  * Technical Assessment
  * Interview
  * Offer
* AI interview preparation
* Interview Prep Agent with Document Q&A
* Career Copilot with defined AI safety guardrails
* Interactive dashboard with responsive UI
* Collapsible sidebar and theme switching

## System Workflow

<img width="785" height="1024" alt="image" src="https://github.com/user-attachments/assets/afc62188-f214-4c7a-b43c-71f4c7aa7431" />


## AI Safety and Platform Guardrails

The platform includes defined AI safety and usage boundaries based on the project's policy document:

`data/policy.pdf`

### Career Copilot Guardrails

Career Copilot is designed to provide career-related assistance while following the defined platform boundaries. The guardrails are based on `data/policy.pdf` and help keep responses relevant to career guidance and appropriate platform use.

### Interview Preparation Guardrails

The Interview Prep Agent follows defined anti-cheating guidelines. It is intended for preparation and learning rather than assisting with dishonest behavior during assessments or interviews.

The Interview Prep Agent also supports the **STAR method**:

* Situation
* Task
* Action
* Result

This helps users structure and improve behavioral interview responses.

## Technology Stack

| Category          | Technology                      |
| ----------------- | ------------------------------- |
| Languages         | Python, JavaScript, HTML5, CSS3 |
| Backend           | FastAPI                         |
| Frontend          | Vanilla JavaScript, HTML5, CSS3 |
| AI / LLM          | Groq API                        |
| Resume Processing | PyMuPDF, python-docx, Regex     |
| Vector Search     | FAISS                           |
| RAG               | Vector RAG                      |
| Database          | SQLite                          |
| Client Storage    | localStorage                    |
| Testing           | Pytest                          |
| Version Control   | Git, GitHub                     |

## Project Structure

```text
AI-Career-Companion-Agent/
├── data/
│   ├── faiss_policy_index/
│   │   ├── chunks.json
│   │   └── index.faiss
│   ├── internships.json
│   └── policy.pdf
│
├── database/
│   ├── applications.json
│   ├── connection.py
│   └── models.py
│
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── style.css
│
├── resume_parser/
│   ├── models/
│   │   └── schema.py
│   ├── routes/
│   │   └── upload.py
│   ├── services/
│   │   ├── candidate_profile.py
│   │   ├── embedding_service.py
│   │   ├── file_parser.py
│   │   ├── internship_matcher.py
│   │   ├── llm_parser.py
│   │   ├── merge.py
│   │   ├── policy_rag.py
│   │   ├── regex_parser.py
│   │   └── vector_store.py
│   ├── app.py
│   └── config.py
│
├── routers/
│   ├── auth.py
│   ├── internships.py
│   ├── resume.py
│   └── users.py
│
├── schemas/
│   ├── resume_schema.py
│   └── user_schema.py
│
├── services/
│   ├── file_parser.py
│   ├── llm_parser.py
│   ├── merge.py
│   └── regex_parser.py
│
├── tests/
│   ├── test_applications.py
│   ├── test_ats.py
│   ├── test_auth.py
│   ├── test_chat.py
│   ├── test_cover_letter.py
│   ├── test_internship_matching.py
│   ├── test_interview_prep.py
│   └── test_resume_parsing.py
│
├── utils/
│   └── security.py
│
├── vector_db/
│   ├── internships.faiss
│   └── internships_metadata.json
│
├── .env.example
├── .gitignore
├── LICENSE
├── app.py
├── main.py
├── psql.sql
├── pytest.ini
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Azra-24/AI-Career-Companion-Agent-for-Internship-Matching-and-Interview-Preparation.git
cd AI-Career-Companion-Agent-for-Internship-Matching-and-Interview-Preparation
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

For Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file and add the required API key:

```env
GROQ_API_KEY=your_groq_api_key
```

Do not commit API keys or the `.env` file to GitHub.

## Running the Application

Start the FastAPI server:

```bash
uvicorn app:app --reload
```

Application:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

## User Workflow

1. Register or log in.
2. Upload a resume.
3. Review the extracted candidate profile.
4. View suitable internship recommendations.
5. Analyze ATS score and skill gaps.
6. Generate a personalized cover letter.
7. Track applications through the application tracker.
8. Practice interviews using the Interview Prep Agent.
9. Use Document Q&A for preparation-related document queries.
10. Use Career Copilot for career guidance.

## Testing

The project uses **Pytest** for testing major application components, including:

* Authentication
* Resume processing
* PDF/DOCX parsing
* API functionality
* Internship matching
* AI-powered features
* User workflows

## Challenges and Solutions

| Challenge | Solution |
|---|---|
| Slow AI responses | Switched from Gemini API to Groq API |
| Inaccurate resume parsing during initial development | Refined the AI prompt with clearer instructions and structured extraction requirements |
| Different resume formats | Added PDF/DOCX-specific extraction |
| Inconsistent resume data | Combined Regex with AI-based parsing |
| Keyword-based matching limitations | Implemented embeddings and FAISS |
| Need for relevant AI responses | Implemented RAG-based retrieval |
| Chatbot unable to retain conversation context | Implemented session/chat ID-based conversation memory to retain context within the current chat |
| Maintaining application state | Used browser localStorage |

## Future Enhancements

* Real-time internship and job listing integration
* Advanced application analytics
* Advanced interview evaluation
* Voice-based interview preparation
* Cloud deployment
* Expanded career analytics

## License

This project is licensed under the MIT License.
