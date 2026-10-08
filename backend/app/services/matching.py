import math
import re
from typing import List, Dict, Any, Optional
from collections import Counter
from pydantic import BaseModel
from app.services.job_sources import JobListing
from app.services.resume_parser import CandidateProfile

class RankedJob(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    required_skills: List[str]
    experience_level: str
    salary_range: Optional[str]
    posted_date: str
    source: str
    original_url: str
    match_score: int  # 0 to 100
    match_level: str  # "High Match" | "Medium Match" | "Low Match"
    matched_skills: List[str]
    missing_skills: List[str]

class SkillGapItem(BaseModel):
    skill: str
    frequency_in_jobs: int
    demand_percentage: int
    importance: str  # "Critical" | "High" | "Moderate"
    recommended_action: str

class TrendingTechItem(BaseModel):
    name: str
    category: str
    market_demand: str
    growth_rate: str
    learning_difficulty: str
    est_learning_time: str
    strategic_reason: str

class RoadmapPhase(BaseModel):
    phase_number: int
    title: str
    duration: str
    focus_skills: List[str]
    learning_objectives: List[str]
    practical_activities: List[str]
    milestone_project: str

class CareerRoadmap(BaseModel):
    target_role: str
    current_match_score: int
    projected_match_score: int
    score_boost: int
    summary: str
    phases: List[RoadmapPhase]
    recommended_portfolio_project: Dict[str, Any]
    interview_preparation_tips: List[str]

# Industry curated trending technologies database
TRENDING_TECH_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "name": "Docker & Containers",
        "category": "Cloud & DevOps",
        "market_demand": "Frequently requested in backend and cloud roles",
        "growth_rate": "Strong industry trend",
        "learning_difficulty": "Intermediate",
        "est_learning_time": "1-2 weeks",
        "strategic_reason": "Standard requirement for reproducible microservices, local development, and cloud deployments."
    },
    {
        "name": "Kubernetes (K8s)",
        "category": "Cloud & DevOps",
        "market_demand": "Frequently requested in enterprise engineering",
        "growth_rate": "Strong industry trend",
        "learning_difficulty": "Advanced",
        "est_learning_time": "3-4 weeks",
        "strategic_reason": "Essential for container orchestration, scaling, and cloud-native infrastructure."
    },
    {
        "name": "Next.js & React Server Components",
        "category": "Frontend & Full Stack",
        "market_demand": "Frequently requested in modern React roles",
        "growth_rate": "Strong industry trend",
        "learning_difficulty": "Intermediate",
        "est_learning_time": "2 weeks",
        "strategic_reason": "Industry standard for SEO-optimized, ultra-fast server-rendered React web applications."
    },
    {
        "name": "TypeScript",
        "category": "Programming Languages",
        "market_demand": "Frequently requested in JavaScript and full-stack roles",
        "growth_rate": "Strong industry trend",
        "learning_difficulty": "Beginner to Intermediate",
        "est_learning_time": "1-2 weeks",
        "strategic_reason": "Provides static type safety, reducing production bugs and enabling large-scale enterprise refactoring."
    },
    {
        "name": "LangChain & LLM RAG Pipelines",
        "category": "AI / Machine Learning",
        "market_demand": "Frequently requested in AI/ML and product roles",
        "growth_rate": "Rapidly growing area",
        "learning_difficulty": "Intermediate",
        "est_learning_time": "2-3 weeks",
        "strategic_reason": "High-value skill in enterprise AI adoption for building custom chatbots, search engines, and agentic workflows."
    },
    {
        "name": "FastAPI & Async Python",
        "category": "Backend Engineering",
        "market_demand": "Frequently requested in Python API roles",
        "growth_rate": "Strong industry trend",
        "learning_difficulty": "Intermediate",
        "est_learning_time": "1-2 weeks",
        "strategic_reason": "Replaces legacy frameworks for high-concurrency microservices, AI endpoints, and OpenAPI auto-documentation."
    },
    {
        "name": "Terraform / Infrastructure as Code",
        "category": "Cloud & DevOps",
        "market_demand": "Frequently requested in senior engineering roles",
        "growth_rate": "Strong industry trend",
        "learning_difficulty": "Intermediate",
        "est_learning_time": "2 weeks",
        "strategic_reason": "Automates multi-cloud provisioning (AWS, Azure, GCP) with declarative configuration."
    },
    {
        "name": "PostgreSQL & Vector Extensions (pgvector)",
        "category": "Databases & AI Storage",
        "market_demand": "Frequently used in relational and AI-enabled data systems",
        "growth_rate": "Growing industry trend",
        "learning_difficulty": "Intermediate",
        "est_learning_time": "1-2 weeks",
        "strategic_reason": "Combines ACID compliance, JSON flexibility, and native AI vector embeddings search."
    }
]

class MatchingService:
    """Service for resume-job matching, skill gap analysis, trending tech, and roadmap generation."""

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        stopwords = {
            "the", "and", "in", "to", "of", "a", "with", "for", "is", "on", "that", "by",
            "this", "an", "you", "we", "our", "are", "from", "at", "as", "your", "all", "have"
        }
        return [w for w in words if w not in stopwords]

    def _compute_tfidf_cosine_similarity(self, text1: str, text2: str) -> float:
        """Compute true TF-IDF cosine similarity for two documents.

        IDF is calculated over the candidate resume and the individual job
        document. This keeps the matcher dependency-free while using the
        actual TF-IDF weighting rather than raw word-count cosine similarity.
        """
        docs = [self._tokenize(text1), self._tokenize(text2)]
        if not docs[0] or not docs[1]:
            return 0.0

        vocabulary = set(docs[0]) | set(docs[1])
        document_frequency = {
            token: sum(1 for doc in docs if token in doc)
            for token in vocabulary
        }

        def vectorize(tokens: List[str]) -> Dict[str, float]:
            counts = Counter(tokens)
            total = len(tokens)
            return {
                token: (count / total) * math.log((1 + len(docs)) / (1 + document_frequency[token])) + 1.0
                for token, count in counts.items()
            }

        vec1 = vectorize(docs[0])
        vec2 = vectorize(docs[1])
        intersection = set(vec1) & set(vec2)
        numerator = sum(vec1[token] * vec2[token] for token in intersection)
        norm1 = math.sqrt(sum(value * value for value in vec1.values()))
        norm2 = math.sqrt(sum(value * value for value in vec2.values()))
        return numerator / (norm1 * norm2) if norm1 and norm2 else 0.0

    def calculate_match_score(
        self,
        candidate_skills: List[str],
        candidate_text: str,
        job: JobListing
    ) -> Dict[str, Any]:
        """Calculates personalized match score and skill breakdown for a single job."""
        candidate_skills_lower = {s.lower(): s for s in candidate_skills}
        job_skills_lower = {s.lower(): s for s in job.required_skills}

        matched = []
        missing = []

        for req_lower, req_original in job_skills_lower.items():
            if req_lower in candidate_skills_lower:
                matched.append(req_original)
            else:
                missing.append(req_original)

        # 1. Skill recall ratio (Weight: 65%)
        skill_ratio = (len(matched) / max(len(job.required_skills), 1)) if job.required_skills else 0.5
        
        # 2. TF-IDF text similarity (Weight: 25%)
        job_full_text = f"{job.title} {job.description} {' '.join(job.required_skills)}"
        text_sim = self._compute_tfidf_cosine_similarity(candidate_text, job_full_text)
        # Scale text similarity (since raw cosine between resume and brief job is typically 0.15 - 0.6)
        text_sim_scaled = min(1.0, text_sim * 2.2)

        # 3. Domain alignment bonus (Weight: 10%)
        domain_bonus = 0.1 if len(matched) >= 2 else 0.0

        raw_score = (skill_ratio * 0.65) + (text_sim_scaled * 0.25) + domain_bonus
        # Keep the score in the documented 0-100 range. Do not add an
        # artificial 5% floor: a candidate with no overlap should score 0.
        score = int(round(min(1.0, max(0.0, raw_score)) * 100))

        if score >= 75:
            level = "High Match"
        elif score >= 50:
            level = "Medium Match"
        else:
            level = "Low Match"

        return {
            "match_score": score,
            "match_level": level,
            "matched_skills": sorted(matched),
            "missing_skills": sorted(missing)
        }

    def match_and_rank_jobs(
        self,
        profile: CandidateProfile,
        jobs: List[JobListing]
    ) -> List[RankedJob]:
        """Ranks jobs according to their relevance and match score."""
        ranked_jobs: List[RankedJob] = []

        for job in jobs:
            match_data = self.calculate_match_score(
                candidate_skills=profile.skills,
                candidate_text=profile.raw_text,
                job=job
            )
            ranked_jobs.append(RankedJob(
                id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                required_skills=job.required_skills,
                experience_level=job.experience_level,
                salary_range=job.salary_range,
                posted_date=job.posted_date,
                source=job.source,
                original_url=job.original_url,
                match_score=match_data["match_score"],
                match_level=match_data["match_level"],
                matched_skills=match_data["matched_skills"],
                missing_skills=match_data["missing_skills"]
            ))

        # Sort descending by match score, then by number of matched skills
        ranked_jobs.sort(key=lambda j: (j.match_score, len(j.matched_skills)), reverse=True)
        return ranked_jobs

    def perform_skill_gap_analysis(
        self,
        candidate_skills: List[str],
        jobs: List[JobListing]
    ) -> Dict[str, Any]:
        """Analyzes missing skills across retrieved jobs to calculate candidate gaps and market readiness."""
        candidate_skills_lower = {s.lower() for s in candidate_skills}
        total_jobs = max(len(jobs), 1)

        skill_demands: Dict[str, int] = {}
        for job in jobs:
            for skill in job.required_skills:
                skill_demands[skill] = skill_demands.get(skill, 0) + 1

        missing_skills_analysis: List[SkillGapItem] = []
        candidate_strengths: List[Dict[str, Any]] = []

        for skill, count in sorted(skill_demands.items(), key=lambda x: x[1], reverse=True):
            pct = int(round((count / total_jobs) * 100))
            if skill.lower() not in candidate_skills_lower:
                if pct >= 45:
                    importance = "Critical"
                    action = f"Top prerequisite in {pct}% of openings. Priority #1 to master."
                elif pct >= 25:
                    importance = "High"
                    action = f"Requested in {pct}% of postings. Highly recommended to learn."
                else:
                    importance = "Moderate"
                    action = f"Secondary qualification ({pct}%). Good for competitive edge."

                missing_skills_analysis.append(SkillGapItem(
                    skill=skill,
                    frequency_in_jobs=count,
                    demand_percentage=pct,
                    importance=importance,
                    recommended_action=action
                ))
            else:
                candidate_strengths.append({
                    "skill": skill,
                    "market_presence": f"Required in {pct}% of jobs",
                    "status": "Possessed & Verified"
                })

        # Calculate market readiness index
        matched_demand_weight = sum(count for skill, count in skill_demands.items() if skill.lower() in candidate_skills_lower)
        total_demand_weight = sum(skill_demands.values()) or 1
        market_readiness_pct = int(round((matched_demand_weight / total_demand_weight) * 100))

        return {
            "market_readiness_index": max(15, min(98, market_readiness_pct)),
            "total_analyzed_jobs": len(jobs),
            "missing_skills": missing_skills_analysis,
            "candidate_strengths": candidate_strengths,
            "critical_gaps_count": sum(1 for item in missing_skills_analysis if item.importance == "Critical"),
            "high_gaps_count": sum(1 for item in missing_skills_analysis if item.importance == "High")
        }

    def get_trending_technologies(self, target_role: str = "") -> List[TrendingTechItem]:
        """Provides trending technology recommendations aligned with market requirements."""
        recommendations: List[TrendingTechItem] = []
        for item in TRENDING_TECH_KNOWLEDGE:
            recommendations.append(TrendingTechItem(**item))
        return recommendations

    def generate_career_roadmap(
        self,
        profile: CandidateProfile,
        target_role: str,
        gap_analysis: Dict[str, Any]
    ) -> CareerRoadmap:
        """Generates a structured, actionable 4-phase career improvement roadmap."""
        critical_missing = [item.skill for item in gap_analysis.get("missing_skills", []) if item.importance == "Critical"]
        high_missing = [item.skill for item in gap_analysis.get("missing_skills", []) if item.importance == "High"]
        all_missing = critical_missing + high_missing

        # Fallback if candidate already possesses most skills
        if not critical_missing:
            critical_missing = ["Docker", "Kubernetes", "Next.js"][:2]
        if not high_missing:
            high_missing = ["LangChain", "GraphQL", "Redis"][:2]

        current_score = gap_analysis.get("market_readiness_index", 55)
        projected_score = min(96, current_score + 35)
        score_boost = projected_score - current_score

        phase_1_skills = critical_missing[:3]
        phase_2_skills = high_missing[:3] or ["TypeScript", "CI/CD", "AWS"]

        phases = [
            RoadmapPhase(
                phase_number=1,
                title="Phase 1: Remediation of Critical Core Skill Gaps",
                duration="Weeks 1 – 2",
                focus_skills=phase_1_skills,
                learning_objectives=[
                    f"Master fundamentals and core APIs of {', '.join(phase_1_skills)}.",
                    "Build small runnable proofs-of-concept demonstrating practical usage.",
                    "Integrate these technologies with your existing codebase or projects."
                ],
                practical_activities=[
                    f"Set up a sandbox repository utilizing {phase_1_skills[0] if phase_1_skills else 'Docker'}.",
                    "Implement end-to-end unit tests and configure automated local workflows.",
                    "Document code decisions in a comprehensive README."
                ],
                milestone_project=f"Mini-Project: Production-grade module using {', '.join(phase_1_skills[:2])}"
            ),
            RoadmapPhase(
                phase_number=2,
                title="Phase 2: Trending & Cloud-Native Stack Expansion",
                duration="Weeks 3 – 5",
                focus_skills=phase_2_skills,
                learning_objectives=[
                    f"Adopt modern industry paradigms with {', '.join(phase_2_skills)}.",
                    "Implement caching, async execution, or container orchestration.",
                    "Optimize system throughput and security best practices."
                ],
                practical_activities=[
                    "Containerize application using Docker Compose with multiple services.",
                    "Set up GitHub Actions CI/CD pipeline for automated testing and linting.",
                    "Implement API caching or state persistence using Redis / PostgreSQL."
                ],
                milestone_project=f"Multi-Service Architecture integrating {', '.join(phase_2_skills[:2])}"
            ),
            RoadmapPhase(
                phase_number=3,
                title="Phase 3: Flagship Portfolio Engineering Project",
                duration="Weeks 6 – 8",
                focus_skills=phase_1_skills + phase_2_skills[:2],
                learning_objectives=[
                    "Synthesize all newly acquired skills into an enterprise-grade showcase repository.",
                    "Deploy a live, interactive web application with custom domain and monitoring.",
                    "Demonstrate clean architectural patterns, documentation, and automated deployment."
                ],
                practical_activities=[
                    "Implement responsive frontend, resilient backend APIs, and database migrations.",
                    "Deploy to cloud infrastructure (Vercel / Render / AWS) with automated CI/CD.",
                    "Record a 2-minute Loom walkthrough and write a technical case study."
                ],
                milestone_project="Full-Stack Cloud-Native Application with Live URL & Public GitHub Repo"
            ),
            RoadmapPhase(
                phase_number=4,
                title="Phase 4: Resume Optimization & Interview Mastery",
                duration="Weeks 9 – 10",
                focus_skills=["System Design", "Technical Storytelling", "Behavioral Alignment"],
                learning_objectives=[
                    "Update resume bullet points using the Google XYZ formula: 'Accomplished [X], measured by [Y], by doing [Z]'.",
                    "Highlight newly mastered skills directly in top-line technical summary.",
                    "Practice targeted technical interview questions for the target role."
                ],
                practical_activities=[
                    "Refactor resume using ATS-friendly keywords extracted by CareerMatch AI.",
                    "Complete 5 mock interviews focusing on system architecture and code problem-solving.",
                    "Apply directly to validated listings identified in CareerMatch AI."
                ],
                milestone_project="Targeted Application Campaign & 100% Interview-Ready Portfolio"
            )
        ]

        portfolio_project = {
            "title": f"Production-Grade Cloud Application for {target_role or 'Full Stack Software Engineer'}",
            "description": "A high-performance full-stack web application designed to demonstrate mastery over the identified skill gaps.",
            "tech_stack": phase_1_skills + phase_2_skills,
            "key_features": [
                "Authentication & secure session management",
                "High-performance REST / GraphQL API endpoints",
                "Containerized with Docker & orchestrated for local and cloud environments",
                "Continuous integration & deployment via GitHub Actions",
                "Automated test coverage with unit & integration tests"
            ]
        }

        interview_tips = [
            f"Be ready to articulate design trade-offs regarding {phase_1_skills[0] if phase_1_skills else 'architecture'} in your recent projects.",
            "Explain how containerization or automated CI/CD improved your delivery turnaround time.",
            "Describe a time you diagnosed a performance bottleneck and your methodology for resolving it.",
            "Prepare STAR-method stories emphasizing cross-functional collaboration and rapid technology adoption."
        ]

        summary = (
            f"Based on your profile and target market requirements for {target_role or 'Software Engineer'}, "
            f"your market readiness score is currently {current_score}%. By completing this structured 4-phase "
            f"roadmap and closing the critical gaps ({', '.join(phase_1_skills)}), your projected match score "
            f"will increase to {projected_score}% (+{score_boost}% boost)."
        )

        return CareerRoadmap(
            target_role=target_role or "Full Stack Software Engineer",
            current_match_score=current_score,
            projected_match_score=projected_score,
            score_boost=score_boost,
            summary=summary,
            phases=phases,
            recommended_portfolio_project=portfolio_project,
            interview_preparation_tips=interview_tips
        )

matching_service = MatchingService()
