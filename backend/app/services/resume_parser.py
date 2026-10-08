import re
import io
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from pypdf import PdfReader
import docx

class CandidateProfile(BaseModel):
    name: str = "Candidate"
    email: Optional[str] = None
    phone: Optional[str] = None
    links: List[str] = Field(default_factory=list)
    years_of_experience: int = 1
    raw_text: str = ""
    skills: List[str] = Field(default_factory=list)
    categorized_skills: Dict[str, List[str]] = Field(default_factory=dict)

# Comprehensive Tech Taxonomy
SKILLS_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Go", "Java", "C++", "C#",
        "Rust", "Ruby", "PHP", "Swift", "Kotlin", "SQL", "HTML", "CSS", "Bash"
    ],
    "Frontend Frameworks & UI": [
        "React", "Next.js", "Vue.js", "Angular", "Svelte", "Tailwind CSS",
        "Redux", "Bootstrap", "Vite", "Webpack", "Responsive Design", "SASS"
    ],
    "Backend & APIs": [
        "Node.js", "FastAPI", "Django", "Flask", "Express", "Spring Boot",
        "ASP.NET", "NestJS", "GraphQL", "REST APIs", "Microservices", "gRPC"
    ],
    "Databases & Storage": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "DynamoDB",
        "Elasticsearch", "Cassandra", "Supabase", "Firebase"
    ],
    "Cloud & DevOps": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "CI/CD", "GitHub Actions", "GitLab CI", "Linux", "Nginx", "Helm", "Ansible"
    ],
    "AI, ML & Data": [
        "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "Scikit-Learn",
        "Pandas", "NumPy", "LangChain", "LlamaIndex", "HuggingFace", "NLP", "RAG",
        "Data Analysis", "Computer Vision"
    ],
    "Tools, Quality & Workflow": [
        "Git", "GitHub", "GitLab", "Jest", "PyTest", "Cypress", "Postman",
        "Docker Compose", "Agile", "Scrum", "Jira", "Figma"
    ]
}

# Synonyms and aliases mapping to canonical skill names
SYNONYM_MAP: Dict[str, str] = {
    "reactjs": "React",
    "react.js": "React",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "ts": "TypeScript",
    "js": "JavaScript",
    "py": "Python",
    "golang": "Go",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "k8s": "Kubernetes",
    "kube": "Kubernetes",
    "amazon web services": "AWS",
    "google cloud platform": "GCP",
    "google cloud": "GCP",
    "microsoft azure": "Azure",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "fast api": "FastAPI",
    "rest": "REST APIs",
    "restful": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "ml": "Machine Learning",
    "github actions": "GitHub Actions",
    "cicd": "CI/CD",
    "ci / cd": "CI/CD",
    "continuous integration": "CI/CD",
    "scikitlearn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "tf": "TensorFlow",
    "rag": "RAG",
    "llm": "LangChain",
    "large language models": "LangChain"
}

class ResumeParserService:
    """Service to parse resumes (PDF, DOCX, TXT) and extract candidate skills & profile."""

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text content from PDF bytes using pypdf."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            return "\n".join(text_parts)
        except Exception as e:
            return ""

    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Extract text content from DOCX bytes using python-docx."""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            return "\n".join(paragraphs)
        except Exception as e:
            return ""

    def parse_text(self, text: str) -> CandidateProfile:
        """Parse raw resume text into structured CandidateProfile."""
        text = text.strip()
        if not text:
            return CandidateProfile()

        # 1. Extract contact details
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = email_match.group(0) if email_match else None

        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', text)
        phone = phone_match.group(0) if phone_match else None

        # Links (GitHub, LinkedIn, Portfolio)
        links = re.findall(r'(?:https?://)?(?:www\.)?(?:github\.com/[\w-]+|linkedin\.com/in/[\w-]+|[\w-]+\.(?:dev|io|me))', text, re.IGNORECASE)

        # 2. Extract Name candidate heuristic
        name = "Candidate"
        first_lines = [line.strip() for line in text.split("\n") if line.strip()][:5]
        for line in first_lines:
            # Skip common header labels
            if any(h in line.lower() for h in ["resume", "curriculum vitae", "summary", "contact", "experience", "email"]):
                continue
            # Words count check for full name (2-4 words)
            words = line.split()
            if 1 <= len(words) <= 4 and re.match(r'^[A-Z][a-zA-Z\s\.\-]+$', line):
                name = line
                break

        # 3. Detect Years of Experience
        years_exp = 1
        exp_matches = re.findall(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', text, re.IGNORECASE)
        if exp_matches:
            try:
                years_exp = max(int(m) for m in exp_matches)
            except ValueError:
                years_exp = 2
        else:
            # Date range heuristic e.g. 2020 - 2024
            years_found = [int(y) for y in re.findall(r'\b(201\d|202\d)\b', text)]
            if len(years_found) >= 2:
                years_exp = max(1, max(years_found) - min(years_found))

        # 4. Extract Skills
        extracted_skills_set = set()
        categorized_skills: Dict[str, List[str]] = {cat: [] for cat in SKILLS_TAXONOMY}

        # Check synonyms first
        lower_text = text.lower()
        for syn, canonical in SYNONYM_MAP.items():
            pattern = rf"(?<![\w\.\-/]){re.escape(syn)}(?![\w\.\-/])"
            if re.search(pattern, lower_text):
                extracted_skills_set.add(canonical)

        # Check standard taxonomy
        for category, skills in SKILLS_TAXONOMY.items():
            for skill in skills:
                # Skill boundary regex
                # Special cases like C++, C#, Go
                if skill == "Go":
                    pattern = r"\b(?:Go|Golang)\b"
                elif skill in ["C++", "C#"]:
                    pattern = rf"(?<!\w){re.escape(skill)}(?!\w)"
                else:
                    pattern = rf"(?<!\w){re.escape(skill.lower())}(?!\w)"

                if re.search(pattern, lower_text, re.IGNORECASE):
                    extracted_skills_set.add(skill)
                    if skill not in categorized_skills[category]:
                        categorized_skills[category].append(skill)

        # Populate categories for synonym-matched skills as well
        for skill in extracted_skills_set:
            for cat, cat_skills in SKILLS_TAXONOMY.items():
                if skill in cat_skills and skill not in categorized_skills[cat]:
                    categorized_skills[cat].append(skill)

        # Clean empty categories
        categorized_skills = {k: v for k, v in categorized_skills.items() if v}

        return CandidateProfile(
            name=name,
            email=email,
            phone=phone,
            links=links,
            years_of_experience=years_exp,
            raw_text=text,
            skills=sorted(list(extracted_skills_set)),
            categorized_skills=categorized_skills
        )

    def parse_file(self, filename: str, content: bytes) -> CandidateProfile:
        """Parse file content based on extension."""
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if ext == "pdf":
            text = self.extract_text_from_pdf(content)
        elif ext == "docx":
            text = self.extract_text_from_docx(content)
        elif ext == "doc":
            # Old binary .doc files are not supported by python-docx.
            # Return a clear empty parse instead of pretending the file was read.
            text = ""
        else:
            # Fallback text decoding
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1", errors="ignore")
                
        return self.parse_text(text)

resume_parser_service = ResumeParserService()
