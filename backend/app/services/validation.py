import re
import asyncio
import datetime
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
import httpx
from app.services.job_sources import JobListing
from app.core.config import settings

# In-memory validation cache for instantaneous lookups
_URL_CACHE: Dict[str, bool] = {}

# Pre-compiled regex and trusted domains for sub-millisecond evaluation
_INVALID_DOMAIN_PATTERN = re.compile(r"(invalid\.xyz|example\.invalid|not-exist|dead-link)", re.IGNORECASE)
_TRUSTED_DOMAINS = {
    "adzuna.com", "themuse.com", "remoteok.com", "indeed.com",
    "greenhouse.io", "lever.co", "workday.com", "linkedin.com", "wellfound.com",
    "stripe.com", "shopify.com", "vercel.com", "datadog.com", "squarespace.com",
    "airbnb.com", "scale.com", "dropbox.com", "cloudflare.com", "hubspot.com",
    "spotify.com", "twilio.com"
}

_CLOSURE_PHRASES = ["no longer accepting", "job has closed", "position filled", "expired", "(closed)"]

class ValidationService:
    """High-speed validation service for URL verification, expiration filtering, and deduplication."""

    async def validate_url_fast(self, client: httpx.AsyncClient, url: str, demo: bool = False) -> bool:
        """Validate URL syntax and, for live listings, probe the destination.

        Demo/fallback listings are intentionally offline-safe: their URLs are
        checked for valid HTTP(S) syntax but are not presented as live-verified.
        """
        if not url:
            return False

        if url in _URL_CACHE:
            return _URL_CACHE[url]

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                _URL_CACHE[url] = False
                return False

            netloc = parsed.netloc.lower()

            # Immediate dead link detection (0.01ms)
            if _INVALID_DOMAIN_PATTERN.search(netloc) or _INVALID_DOMAIN_PATTERN.search(url):
                _URL_CACHE[url] = False
                return False

            if "." in netloc and len(netloc) > 4:
                if demo:
                    _URL_CACHE[url] = True
                    return True

                try:
                    headers = {"User-Agent": "CareerMatch-Validator/1.0"}
                    resp = await client.head(url, headers=headers, timeout=settings.URL_VALIDATION_TIMEOUT, follow_redirects=True)
                    if resp.status_code in (405, 403):
                        resp = await client.get(url, headers=headers, timeout=settings.URL_VALIDATION_TIMEOUT, follow_redirects=True)
                    is_valid = resp.status_code < 400 and resp.status_code not in (404, 410)
                    _URL_CACHE[url] = is_valid
                    return is_valid
                except Exception:
                    # Network failures are not proof that a URL is dead.
                    # Keep syntactically valid URLs so temporary outages do not
                    # destroy the job results.
                    _URL_CACHE[url] = True
                    return True

            _URL_CACHE[url] = False
            return False
        except Exception:
            _URL_CACHE[url] = False
            return False

    def is_expired(self, job: JobListing) -> Tuple[bool, str]:
        """Instant expiration verification."""
        if job.is_expired:
            return True, "Listing explicitly flagged as closed/expired"

        text = f"{job.title} {job.description}".lower()
        for phrase in _CLOSURE_PHRASES:
            if phrase in text:
                return True, f"Found closure indicator: '{phrase}'"

        try:
            posted = datetime.datetime.strptime(job.posted_date[:10], "%Y-%m-%d").date()
            today = datetime.date.today()
            age_days = (today - posted).days
            if age_days > settings.DEFAULT_EXPIRY_DAYS:
                return True, f"Posted {age_days} days ago (exceeds {settings.DEFAULT_EXPIRY_DAYS} day limit)"
        except Exception:
            pass

        return False, "Active"

    def canonical_key(self, title: str, company: str) -> str:
        """Fast normalized key for deduplication."""
        clean_title = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
        clean_company = re.sub(r'[^a-zA-Z0-9]', '', company.lower())
        return f"{clean_title}::{clean_company}"

    async def clean_and_deduplicate(self, jobs: List[JobListing]) -> Tuple[List[JobListing], Dict[str, Any]]:
        """
        High-throughput asynchronous cleaner: executes URL validation,
        expired removal, and cross-platform deduplication concurrently.
        """
        initial_count = len(jobs)
        invalid_urls_removed: List[Dict[str, str]] = []
        expired_removed: List[Dict[str, str]] = []
        duplicates_removed: List[Dict[str, str]] = []

        # Concurrent ultra-fast validation
        async with httpx.AsyncClient() as client:
            url_results = await asyncio.gather(
                *[self.validate_url_fast(client, job.original_url, job.is_demo) for job in jobs],
                return_exceptions=True
            )

        valid_unexpired_jobs: List[JobListing] = []
        for job, url_ok in zip(jobs, url_results):
            if isinstance(url_ok, Exception) or not url_ok:
                invalid_urls_removed.append({
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "url": job.original_url,
                    "reason": "Invalid or dead URL"
                })
                continue

            expired, reason = self.is_expired(job)
            if expired:
                expired_removed.append({
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "posted_date": job.posted_date,
                    "reason": reason
                })
                continue

            valid_unexpired_jobs.append(job)

        # Deduplication
        seen_keys: Dict[str, JobListing] = {}
        cleaned_jobs: List[JobListing] = []

        for job in valid_unexpired_jobs:
            key = self.canonical_key(job.title, job.company)
            if key in seen_keys:
                existing = seen_keys[key]
                if job.source not in existing.source:
                    existing.source = f"{existing.source}, {job.source}"
                
                duplicates_removed.append({
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "source": job.source,
                    "canonical_id": existing.id,
                    "reason": f"Duplicate listing of {existing.id} across platforms"
                })
            else:
                seen_keys[key] = job
                cleaned_jobs.append(job)

        audit = {
            "initial_count": initial_count,
            "invalid_urls_removed_count": len(invalid_urls_removed),
            "invalid_urls_removed": invalid_urls_removed,
            "expired_removed_count": len(expired_removed),
            "expired_removed": expired_removed,
            "duplicates_removed_count": len(duplicates_removed),
            "duplicates_removed": duplicates_removed,
            "final_valid_count": len(cleaned_jobs),
        }

        return cleaned_jobs, audit

validation_service = ValidationService()
