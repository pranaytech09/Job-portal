import re
import datetime
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import httpx
from pydantic import BaseModel
from app.core.config import settings

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    required_skills: List[str]
    experience_level: str = "Mid-Level"
    salary_range: Optional[str] = "Competitive"
    posted_date: str
    source: str  # "Remote OK" | "Adzuna" | "The Muse"
    original_url: str
    is_expired: bool = False
    is_valid_url: bool = True
    is_demo: bool = False

SAMPLE_BASE_JOBS: List[Dict[str, Any]] = [
    {
        "id": "muse-101",
        "title": "Senior Full Stack Engineer",
        "company": "Vercel",
        "location": "Remote, US",
        "description": "Build high-performance web infrastructure and developer tooling. Required stack: React, Next.js, TypeScript, Node.js, Tailwind CSS, GraphQL, and AWS cloud services.",
        "required_skills": ["React", "Next.js", "TypeScript", "Node.js", "Tailwind CSS", "GraphQL", "AWS"],
        "experience_level": "Senior",
        "salary_range": "$150,000 - $185,000",
        "posted_date": "2026-09-25",
        "source": "The Muse",
        "original_url": "https://www.themuse.com/jobs/vercel/senior-full-stack-engineer",
        "is_expired": False,
    },
    {
        "id": "muse-102",
        "title": "Frontend React Developer",
        "company": "Shopify",
        "location": "Remote",
        "description": "Develop accessible and fast storefront applications using React, TypeScript, Redux, REST APIs, and Jest for unit testing. Experience with modern CSS and Webpack is a plus.",
        "required_skills": ["React", "TypeScript", "JavaScript", "HTML", "CSS", "Redux", "REST APIs", "Jest"],
        "experience_level": "Mid-Level",
        "salary_range": "$115,000 - $140,000",
        "posted_date": "2026-09-28",
        "source": "The Muse",
        "original_url": "https://www.themuse.com/jobs/shopify/frontend-react-developer",
        "is_expired": False,
    },
    {
        "id": "muse-103",
        "title": "DevOps & Cloud Infrastructure Engineer",
        "company": "Datadog",
        "location": "New York, NY (Hybrid)",
        "description": "Architect robust cloud infrastructure utilizing Docker, Kubernetes, Terraform, AWS, CI/CD pipelines, and Linux automation.",
        "required_skills": ["Docker", "Kubernetes", "Terraform", "AWS", "CI/CD", "Linux", "Python", "Bash"],
        "experience_level": "Senior",
        "salary_range": "$160,000 - $200,000",
        "posted_date": "2026-09-22",
        "source": "The Muse",
        "original_url": "https://www.themuse.com/jobs/datadog/devops-cloud-engineer",
        "is_expired": False,
    },
    {
        "id": "muse-104",
        "title": "Junior Python Developer",
        "company": "Squarespace",
        "location": "New York, NY",
        "description": "Assist our core platform team in building backend microservices with Python, FastAPI, PostgreSQL, and Git version control.",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Git", "REST APIs", "SQL"],
        "experience_level": "Junior",
        "salary_range": "$85,000 - $105,000",
        "posted_date": "2026-09-30",
        "source": "The Muse",
        "original_url": "https://www.themuse.com/jobs/squarespace/junior-python-developer",
        "is_expired": False,
    },
    {
        "id": "adzuna-201",
        "title": "Senior Python Backend Engineer",
        "company": "Stripe",
        "location": "San Francisco, CA (Remote)",
        "description": "Design mission-critical payment APIs using Python, Django, FastAPI, PostgreSQL, Redis, Docker, and distributed systems architecture.",
        "required_skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "REST APIs", "Microservices"],
        "experience_level": "Senior",
        "salary_range": "$175,000 - $210,000",
        "posted_date": "2026-09-20",
        "source": "Adzuna",
        "original_url": "https://www.adzuna.com/land/ad/stripe-backend-engineer",
        "is_expired": False,
    },
    {
        "id": "adzuna-202",
        "title": "Full Stack Software Engineer",
        "company": "Airbnb",
        "location": "San Francisco, CA",
        "description": "Join our guest experience team. Build scalable web applications with React, Node.js, TypeScript, GraphQL, MySQL, and Docker.",
        "required_skills": ["React", "Node.js", "TypeScript", "GraphQL", "MySQL", "Docker", "Git", "REST APIs"],
        "experience_level": "Mid-Level",
        "salary_range": "$140,000 - $170,000",
        "posted_date": "2026-09-26",
        "source": "Adzuna",
        "original_url": "https://www.adzuna.com/land/ad/airbnb-full-stack-engineer",
        "is_expired": False,
    },
    {
        "id": "adzuna-203",
        "title": "Machine Learning / AI Engineer",
        "company": "Scale AI",
        "location": "San Francisco, CA (Remote)",
        "description": "Develop and deploy enterprise RAG pipelines and LLM systems. Stack includes Python, PyTorch, LangChain, OpenAI API, HuggingFace, Docker, and PostgreSQL.",
        "required_skills": ["Python", "PyTorch", "LangChain", "Machine Learning", "Docker", "PostgreSQL", "FastAPI", "Git"],
        "experience_level": "Mid-Level",
        "salary_range": "$155,000 - $190,000",
        "posted_date": "2026-09-29",
        "source": "Adzuna",
        "original_url": "https://www.adzuna.com/land/ad/scale-ai-engineer",
        "is_expired": False,
    },
    {
        "id": "adzuna-204",
        "title": "Frontend Engineer (React / TypeScript)",
        "company": "Dropbox",
        "location": "Austin, TX (Remote)",
        "description": "Build responsive and fast user interfaces using React, TypeScript, Next.js, CSS, and modern web standards.",
        "required_skills": ["React", "TypeScript", "Next.js", "JavaScript", "HTML", "CSS", "Git"],
        "experience_level": "Mid-Level",
        "salary_range": "$125,000 - $150,000",
        "posted_date": "2026-09-18",
        "source": "Adzuna",
        "original_url": "https://www.adzuna.com/land/ad/dropbox-frontend-engineer",
        "is_expired": False,
    },
    {
        "id": "remoteok-301",
        "title": "Senior Cloud & Platform Engineer",
        "company": "Cloudflare",
        "location": "Austin, TX (Remote)",
        "description": "Manage global edge infrastructure with Kubernetes, Go, Docker, Terraform, CI/CD, and Linux kernel networking.",
        "required_skills": ["Kubernetes", "Docker", "Terraform", "Go", "CI/CD", "Linux", "AWS", "Nginx"],
        "experience_level": "Senior",
        "salary_range": "$165,000 - $205,000",
        "posted_date": "2026-09-27",
        "source": "Remote OK",
        "original_url": "https://remoteok.com/remote-jobs/remote-cloud-engineer-cloudflare",
        "is_expired": False,
    },
    {
        "id": "remoteok-302",
        "title": "Full Stack Web Developer",
        "company": "HubSpot",
        "location": "Cambridge, MA (Remote)",
        "description": "Develop full-lifecycle features across our marketing hub. Requirements: JavaScript, React, Node.js, Express, MongoDB, and AWS.",
        "required_skills": ["JavaScript", "React", "Node.js", "Express", "MongoDB", "AWS", "Git", "REST APIs"],
        "experience_level": "Mid-Level",
        "salary_range": "$120,000 - $145,000",
        "posted_date": "2026-09-24",
        "source": "Remote OK",
        "original_url": "https://remoteok.com/remote-jobs/remote-full-stack-web-developer-hubspot",
        "is_expired": False,
    },
    {
        "id": "remoteok-303",
        "title": "Data Scientist / Python Specialist",
        "company": "Spotify",
        "location": "New York, NY",
        "description": "Analyze user behavior metrics and build predictive analytics models using Python, Pandas, Scikit-Learn, SQL, and data pipelines.",
        "required_skills": ["Python", "SQL", "Pandas", "Scikit-Learn", "Machine Learning", "Data Analysis", "Git"],
        "experience_level": "Mid-Level",
        "salary_range": "$135,000 - $165,000",
        "posted_date": "2026-09-21",
        "source": "Remote OK",
        "original_url": "https://remoteok.com/remote-jobs/remote-data-scientist-python-specialist-spotify",
        "is_expired": False,
    },
    {
        "id": "remoteok-304",
        "title": "Backend Software Engineer (Node & Go)",
        "company": "Twilio",
        "location": "Denver, CO (Remote)",
        "description": "Scale real-time messaging APIs. Required: Node.js, TypeScript, Go, Docker, PostgreSQL, Redis, and Microservices.",
        "required_skills": ["Node.js", "TypeScript", "Go", "Docker", "PostgreSQL", "Redis", "Microservices", "REST APIs"],
        "experience_level": "Senior",
        "salary_range": "$150,000 - $180,000",
        "posted_date": "2026-09-29",
        "source": "Remote OK",
        "original_url": "https://remoteok.com/remote-jobs/remote-backend-engineer-node-go-twilio",
        "is_expired": False,
    },
    {
        "id": "remoteok-dup-999",
        "title": "Senior Full Stack Engineer",
        "company": "Vercel",
        "location": "Remote, US",
        "description": "Build high-performance web infrastructure and developer tooling. Required stack: React, Next.js, TypeScript, Node.js, Tailwind CSS, GraphQL, and AWS cloud services.",
        "required_skills": ["React", "Next.js", "TypeScript", "Node.js", "Tailwind CSS", "GraphQL", "AWS"],
        "experience_level": "Senior",
        "salary_range": "$150,000 - $185,000",
        "posted_date": "2026-09-25",
        "source": "Remote OK",
        "original_url": "https://remoteok.com/remote-jobs/remote-senior-full-stack-engineer-vercel",
        "is_expired": False,
    },
    {
        "id": "adzuna-exp-888",
        "title": "Legacy PHP & MySQL Developer (CLOSED)",
        "company": "OldTech Inc",
        "location": "Chicago, IL",
        "description": "This job listing is closed and no longer accepting applications. Maintained legacy systems with PHP and MySQL.",
        "required_skills": ["PHP", "MySQL", "HTML", "CSS"],
        "experience_level": "Junior",
        "salary_range": "$60,000 - $75,000",
        "posted_date": "2026-01-10",
        "source": "Adzuna",
        "original_url": "https://www.adzuna.com/land/ad/expired-legacy-php-role",
        "is_expired": True,
    },
    {
        "id": "muse-broken-777",
        "title": "Software Engineer (Dead Link Sample)",
        "company": "Defunct Co",
        "location": "Remote",
        "description": "Requires JavaScript and HTML. Note: link target is invalid or dead.",
        "required_skills": ["JavaScript", "HTML"],
        "experience_level": "Junior",
        "salary_range": "$70,000",
        "posted_date": "2026-09-15",
        "source": "The Muse",
        "original_url": "https://this-domain-does-not-exist-404-invalid.xyz/careers/job",
        "is_expired": False,
    },
]

# Fast in-memory cache: (cache_key -> (timestamp, List[JobListing]))
_JOB_CACHE: Dict[str, Tuple[float, List[JobListing]]] = {}
CACHE_TTL = 300  # 5 minutes

class JobSourcesService:
    """High-speed aggregator for Remote OK, Adzuna, and The Muse."""

    async def fetch_adzuna_jobs(self, query: str = "", location: str = "") -> List[JobListing]:
        """Fetch jobs from Adzuna API with fast timeout or instant fallback."""
        jobs: List[JobListing] = []
        if settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY:
            try:
                url = f"https://api.adzuna.com/v1/api/jobs/{settings.ADZUNA_COUNTRY}/search/1"
                params = {
                    "app_id": settings.ADZUNA_APP_ID,
                    "app_key": settings.ADZUNA_APP_KEY,
                    "what": query or "software engineer",
                    "where": location or "remote",
                    "results_per_page": settings.MAX_JOBS_PER_SOURCE,
                    "content-type": "application/json"
                }
                async with httpx.AsyncClient(timeout=1.2) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("results", []):
                            desc = item.get("description", "")
                            skills = self._extract_skills_from_text(f"{item.get('title', '')} {desc}")
                            jobs.append(JobListing(
                                id=f"adzuna-{item.get('id')}",
                                title=item.get("title", "Software Engineer"),
                                company=item.get("company", {}).get("display_name", "Tech Company"),
                                location=item.get("location", {}).get("display_name", "Remote"),
                                description=desc,
                                required_skills=skills,
                                experience_level="Mid-Level",
                                salary_range=f"${int(item.get('salary_min', 90000)):,} - ${int(item.get('salary_max', 140000)):,}" if item.get("salary_min") else "Competitive",
                                posted_date=item.get("created", datetime.date.today().isoformat())[:10],
                                source="Adzuna",
                                original_url=item.get("redirect_url", "https://www.adzuna.com"),
                                is_expired=False,
                            ))
            except Exception:
                pass

        if not jobs:
            adzuna_samples = [j for j in SAMPLE_BASE_JOBS if j["source"] == "Adzuna"]
            for sample in adzuna_samples:
                if self._matches_filter(sample, query, location):
                    jobs.append(JobListing(**sample, is_demo=True))

        return jobs

    async def fetch_themuse_jobs(self, query: str = "", location: str = "") -> List[JobListing]:
        """Fetch jobs from The Muse with micro-timeout or instant fallback."""
        jobs: List[JobListing] = []
        if settings.THE_MUSE_API_KEY:
            try:
                url = "https://www.themuse.com/api/public/jobs"
                params = {"category": "Software Engineering", "page": 1, "api_key": settings.THE_MUSE_API_KEY}
                async with httpx.AsyncClient(timeout=1.2) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("results", [])[:10]:
                            desc = re.sub(r'<[^>]+>', ' ', item.get("contents", ""))
                            skills = self._extract_skills_from_text(f"{item.get('name', '')} {desc}")
                            locations = [loc.get("name") for loc in item.get("locations", [])]
                            jobs.append(JobListing(
                                id=f"muse-{item.get('id')}",
                                title=item.get("name", "Software Engineer"),
                                company=item.get("company", {}).get("name", "Innovative Co"),
                                location=", ".join(locations) if locations else "Remote",
                                description=desc[:600],
                                required_skills=skills,
                                experience_level=item.get("levels", [{}])[0].get("name", "Mid-Level") if item.get("levels") else "Mid-Level",
                                salary_range="Competitive",
                                posted_date=item.get("publication_date", datetime.date.today().isoformat())[:10],
                                source="The Muse",
                                original_url=item.get("refs", {}).get("landing_page", "https://www.themuse.com"),
                                is_expired=False,
                            ))
            except Exception:
                pass

        if not jobs:
            muse_samples = [j for j in SAMPLE_BASE_JOBS if j["source"] == "The Muse"]
            for sample in muse_samples:
                if self._matches_filter(sample, query, location):
                    jobs.append(JobListing(**sample, is_demo=True))

        return jobs

    async def fetch_remoteok_jobs(self, query: str = "", location: str = "") -> List[JobListing]:
        """Instant fetch from the Remote OK tech repository demo feed."""
        jobs: List[JobListing] = []
        remoteok_samples = [j for j in SAMPLE_BASE_JOBS if j["source"] == "Remote OK"]
        for sample in remoteok_samples:
            if self._matches_filter(sample, query, location):
                jobs.append(JobListing(**sample, is_demo=True))
        return jobs

    async def aggregate_jobs(
        self,
        query: str = "",
        location: str = "",
        sources: Optional[List[str]] = None
    ) -> List[JobListing]:
        """Collects jobs concurrently with instant memory cache (<1ms response)."""
        requested_sources = sources or ["Remote OK", "Adzuna", "The Muse"]
        source_names = {"remote ok": "Remote OK", "remoteok": "Remote OK", "remote-ok": "Remote OK", "adzuna": "Adzuna", "the muse": "The Muse", "themuse": "The Muse"}
        active_sources = []
        for source in requested_sources:
            canonical = source_names.get(source.strip().lower())
            if canonical and canonical not in active_sources:
                active_sources.append(canonical)
        if not active_sources:
            active_sources = ["Remote OK", "Adzuna", "The Muse"]
        cache_key = f"{query.lower()}::{location.lower()}::{','.join(sorted(active_sources))}"

        now = time.time()
        if cache_key in _JOB_CACHE:
            cached_time, cached_jobs = _JOB_CACHE[cache_key]
            if now - cached_time < CACHE_TTL:
                return [j.model_copy() for j in cached_jobs]

        # Fetch in parallel
        tasks = []
        if "Adzuna" in active_sources:
            tasks.append(self.fetch_adzuna_jobs(query, location))
        if "The Muse" in active_sources:
            tasks.append(self.fetch_themuse_jobs(query, location))
        if "Remote OK" in active_sources:
            tasks.append(self.fetch_remoteok_jobs(query, location))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_jobs: List[JobListing] = []
        for res in results:
            if isinstance(res, list):
                all_jobs.extend(res)
            elif isinstance(res, Exception):
                pass

        if not all_jobs:
            for sample in SAMPLE_BASE_JOBS:
                if sample["source"] in active_sources:
                    all_jobs.append(JobListing(**sample, is_demo=True))

        _JOB_CACHE[cache_key] = (now, all_jobs)
        return all_jobs

    def _matches_filter(self, job: Dict[str, Any], query: str, location: str) -> bool:
        if not query and not location:
            return True
        text = f"{job['title']} {job['description']} {' '.join(job.get('required_skills', []))}".lower()
        query_words = query.lower().split()
        matches_query = any(word in text for word in query_words) if query_words else True
        matches_location = location.lower() in job['location'].lower() if location else True
        return matches_query and matches_location

    def _extract_skills_from_text(self, text: str) -> List[str]:
        common_tech = [
            "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js",
            "Express", "FastAPI", "Django", "PostgreSQL", "MySQL", "MongoDB",
            "Redis", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
            "CI/CD", "Git", "GraphQL", "REST APIs", "Tailwind CSS", "Linux",
            "PyTorch", "Machine Learning", "Microservices", "Java", "Go"
        ]
        found = []
        lower_text = text.lower()
        for tech in common_tech:
            pattern = rf"\b{re.escape(tech.lower())}\b"
            if re.search(pattern, lower_text):
                found.append(tech)
        return found or ["Software Engineering", "Problem Solving", "Git"]

job_sources_service = JobSourcesService()
