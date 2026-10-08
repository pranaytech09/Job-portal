from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from app.services.job_sources import job_sources_service, JobListing
from app.services.validation import validation_service
from app.services.resume_parser import resume_parser_service, CandidateProfile
from app.services.matching import matching_service, RankedJob
from app.core.config import settings

router = APIRouter(prefix="/jobs", tags=["Jobs & Matching"])

class SearchRequest(BaseModel):
    query: str = ""
    location: str = ""
    sources: List[str] = Field(default_factory=lambda: ["Remote OK", "Adzuna", "The Muse"])

SAMPLE_RESUMES = {
    "frontend": """Alex Morgan
alex.morgan@example.dev | (555) 234-5678 | github.com/alexmorgan-dev
Summary:
Results-driven Frontend Developer with 3 years of experience building responsive, high-performance web applications using modern JavaScript and React. Passionate about UI/UX design systems and accessible frontend code.

Technical Skills:
- Programming Languages: JavaScript, TypeScript, HTML5, CSS3, SQL
- Frontend: React, Redux, Tailwind CSS, Next.js, Vite, Webpack
- Tools: Git, GitHub, Jest, Postman, Figma, REST APIs

Work Experience:
Frontend Developer | TechWave Labs (2023 - Present)
- Developed responsive client portals using React, TypeScript, and Tailwind CSS.
- Optimized page load times by 35% through code-splitting and asset compression.
- Wrote unit tests using Jest, achieving 85% test coverage.

Junior Web Developer | PixelCraft Studio (2021 - 2023)
- Built interactive marketing websites with JavaScript and modern CSS.
- Integrated REST APIs with backend services and handled state management with Redux.
""",
    "backend": """Jordan Lee
jordan.lee@example.dev | (555) 876-5432 | github.com/jordanlee-code
Summary:
Backend Software Engineer with 4 years of experience architecting resilient APIs and data pipelines using Python, FastAPI, and PostgreSQL. Experienced in Docker containerization and database optimization.

Technical Skills:
- Languages: Python, SQL, Bash
- Frameworks & Backend: FastAPI, Django, Flask, REST APIs, Microservices
- Databases: PostgreSQL, Redis, MySQL
- Cloud & DevOps: Docker, Docker Compose, Git, Linux, CI/CD, AWS

Experience:
Backend Engineer | Apex Cloud Systems (2022 - Present)
- Engineered scalable RESTful microservices using Python and FastAPI handling 10k requests/minute.
- Implemented Redis caching layers, cutting database read latency by 45%.
- Containerized development and staging environments using Docker and Docker Compose.
""",
    "ai_ml": """Priya Sharma
priya.sharma@example.ai | (555) 901-2345 | github.com/priyasharma-ai
Summary:
Machine Learning Engineer specializing in NLP, Retrieval-Augmented Generation (RAG), and deep learning applications. Proficient in Python, PyTorch, LangChain, and modern data processing stacks.

Technical Skills:
- Languages: Python, SQL, C++
- AI / ML: Machine Learning, Deep Learning, PyTorch, TensorFlow, Scikit-Learn, Pandas, NumPy, LangChain, RAG, HuggingFace
- Backend & Cloud: FastAPI, Docker, PostgreSQL, Git, Linux

Experience:
Machine Learning Engineer | Nova AI Technologies (2023 - Present)
- Designed and deployed end-to-end RAG question-answering systems with LangChain and vector databases.
- Fine-tuned transformer models using HuggingFace and PyTorch for domain-specific text classification.
- Served ML inference endpoints via FastAPI containerized with Docker.
"""
}

@router.get("/sources")
def get_sources_status():
    """Return available job sources and connection metadata."""
    return {
        "sources": [
            {
                "name": "Remote OK",
                "status": "Curated Demo Feed",
                "specialty": "Curated remote Tech & Software Engineering Opportunities",
                "features": ["URL syntax validation", "Detailed tech stacks", "Salary transparency"]
            },
            {
                "name": "Adzuna",
                "status": "API Configured" if settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY else "Demo Fallback",
                "specialty": "Multi-region Global Job Aggregation",
                "features": ["Broad marketplace reach", "Category filtering", "Live API when configured"]
            },
            {
                "name": "The Muse",
                "status": "API Configured" if settings.THE_MUSE_API_KEY else "Demo Fallback",
                "specialty": "Company Profiles & Open Roles",
                "features": ["Company context", "Job posting metadata", "Level tagging"]
            }
        ]
    }

@router.get("/sample-resumes")
def get_sample_resumes():
    """Returns sample resumes for instant testing."""
    return SAMPLE_RESUMES

@router.post("/search")
async def search_jobs(payload: SearchRequest):
    """
    Search jobs from Remote OK, Adzuna, and The Muse,
    validates URLs, removes expired/invalid entries, and eliminates duplicates.
    """
    raw_jobs = await job_sources_service.aggregate_jobs(
        query=payload.query,
        location=payload.location,
        sources=payload.sources
    )

    cleaned_jobs, audit = await validation_service.clean_and_deduplicate(raw_jobs)

    return {
        "jobs": cleaned_jobs,
        "audit": audit
    }

@router.post("/match")
async def match_resume_to_jobs(
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    query: str = Form(""),
    location: str = Form(""),
    sources: Optional[str] = Form("Remote OK,Adzuna,The Muse")
):
    """
    Full pipeline execution:
    1. Parse Resume (PDF/DOCX/Text) & Extract Skills
    2. Search Jobs across Remote OK, Adzuna, and The Muse
    3. URL Validation & Reachability Check
    4. Remove Invalid/Expired Jobs
    5. Cross-platform Deduplication
    6. Calculate personalized Match Scores
    7. Rank jobs by relevance with original apply URLs
    """
    profile = CandidateProfile()
    if resume_file and hasattr(resume_file, "filename") and resume_file.filename:
        content = await resume_file.read()
        profile = resume_parser_service.parse_file(resume_file.filename, content)
    elif resume_text and isinstance(resume_text, str) and resume_text.strip():
        profile = resume_parser_service.parse_text(resume_text)
    else:
        raise HTTPException(status_code=400, detail="Please provide either a resume file or resume text.")

    source_list = [s.strip() for s in sources.split(",") if s.strip()] if sources else ["Remote OK", "Adzuna", "The Muse"]

    raw_jobs = await job_sources_service.aggregate_jobs(
        query=query or (" ".join(profile.skills[:2]) if profile.skills else ""),
        location=location,
        sources=source_list
    )

    cleaned_jobs, audit = await validation_service.clean_and_deduplicate(raw_jobs)
    ranked_jobs = matching_service.match_and_rank_jobs(profile, cleaned_jobs)

    return {
        "candidate_profile": profile,
        "ranked_jobs": ranked_jobs,
        "validation_audit": audit
    }
