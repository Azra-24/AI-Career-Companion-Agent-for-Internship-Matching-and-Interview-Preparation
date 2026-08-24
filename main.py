from resume_parser.app import app

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hybrid Resume Parsing System API is running"}
