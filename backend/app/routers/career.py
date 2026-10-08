from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from app.services.job_sources import job_sources_service
from app.services.validation import validation_service
from app.services.resume_parser import resume_parser_service, CandidateProfile
from app.services.matching import matching_service

router = APIRouter(prefix="/career", tags=["Career Development"])

class SkillGapRequest(BaseModel):
    skills: List[str]
    target_role: Optional[str] = ""

class RoadmapRequest(BaseModel):
    skills: List[str]
    target_role: str = "Full Stack Software Engineer"
    years_of_experience: Optional[int] = 2

@router.get("/trending-tech")
def get_trending_tech(role: Optional[str] = ""):
    """Returns trending technology recommendations based on aggregated market requirements."""
    trending = matching_service.get_trending_technologies(role)
    return {"trending_technologies": trending}

@router.post("/skill-gap")
async def analyze_skill_gap(payload: SkillGapRequest):
    """Performs skill gap analysis for given skills against target role."""
    jobs = await job_sources_service.aggregate_jobs(query=payload.target_role or "software engineer")
    cleaned_jobs, _ = await validation_service.clean_and_deduplicate(jobs)
    gap_result = matching_service.perform_skill_gap_analysis(payload.skills, cleaned_jobs)
    return gap_result

@router.post("/roadmap")
async def create_roadmap(payload: RoadmapRequest):
    """Generates a personalized 4-phase Career Improvement Roadmap."""
    jobs = await job_sources_service.aggregate_jobs(query=payload.target_role)
    cleaned_jobs, _ = await validation_service.clean_and_deduplicate(jobs)
    gap_result = matching_service.perform_skill_gap_analysis(payload.skills, cleaned_jobs)

    dummy_profile = CandidateProfile(
        name="Candidate",
        years_of_experience=payload.years_of_experience or 2,
        skills=payload.skills
    )

    roadmap = matching_service.generate_career_roadmap(
        profile=dummy_profile,
        target_role=payload.target_role,
        gap_analysis=gap_result
    )

    return roadmap

@router.post("/pipeline")
async def run_full_pipeline(
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    target_role: Optional[str] = Form(""),
    location: Optional[str] = Form(""),
    sources: Optional[str] = Form("Remote OK,Adzuna,The Muse")
):
    """
    Executes the Complete CareerMatch AI Proposed Flow in sub-second time:
    Resume → Job Search → URL Validation → Remove Invalid/Expired Jobs →
    Deduplication → Resume Skill Extraction → Resume–Job Matching → Match Score →
    Job Ranking → Original Job URL → Skill Gap Analysis →
    Trending Technology Recommendations → Career Improvement Roadmap
    """
    profile = CandidateProfile()
    if resume_file and hasattr(resume_file, "filename") and resume_file.filename:
        content = await resume_file.read()
        profile = resume_parser_service.parse_file(resume_file.filename, content)
    elif resume_text and isinstance(resume_text, str) and resume_text.strip():
        profile = resume_parser_service.parse_text(resume_text)
    else:
        raise HTTPException(status_code=400, detail="Please upload a resume file or paste resume text.")

    query_str = target_role or (" ".join(profile.skills[:2]) if profile.skills else "Software Engineer")
    source_list = [s.strip() for s in sources.split(",") if s.strip()] if sources else ["Remote OK", "Adzuna", "The Muse"]

    # 1. Multi-source fetch (cached & parallel)
    raw_jobs = await job_sources_service.aggregate_jobs(
        query=query_str,
        location=location or "",
        sources=source_list
    )

    # 2. Fast concurrent validation, expiration removal, and deduplication
    cleaned_jobs, audit = await validation_service.clean_and_deduplicate(raw_jobs)

    # 3. Resume-Job Matching, Match Score, Ranking & Original URLs
    ranked_jobs = matching_service.match_and_rank_jobs(profile, cleaned_jobs)

    # 4. Skill Gap Analysis
    skill_gap = matching_service.perform_skill_gap_analysis(profile.skills, cleaned_jobs)

    # 5. Trending Technology Recommendations
    trending_tech = matching_service.get_trending_technologies(query_str)

    # 6. Personalized Career Improvement Roadmap
    roadmap = matching_service.generate_career_roadmap(
        profile=profile,
        target_role=query_str,
        gap_analysis=skill_gap
    )

    return {
        "pipeline_status": "Success",
        "flow": [
            "Resume Upload & Ingestion",
            "Job Search across Remote OK, Adzuna & The Muse",
            "URL Validation & Reachability",
            "Invalid & Expired Listing Removal",
            "Cross-Platform Deduplication",
            "Resume Skill Extraction",
            "Resume-Job Matching & Composite Scoring",
            "Relevance Ranking & Original URL Delivery",
            "Market Skill Gap Analysis",
            "Trending Technology Recommendations",
            "Personalized Career Improvement Roadmap"
        ],
        "candidate_profile": profile,
        "validation_audit": audit,
        "ranked_jobs": ranked_jobs,
        "skill_gap_analysis": skill_gap,
        "trending_technologies": trending_tech,
        "career_roadmap": roadmap
    }
