import json
import re

from google import genai
from google.genai import types
from openai import OpenAI

from app.core.config import get_settings
from app.models.schemas import AnalysisResult, EntityGroup
from app.utils.text import (
    DATE_RE,
    EMAIL_RE,
    LOCATION_RE,
    MONEY_RE,
    NAME_RE,
    ORG_RE,
    PHONE_RE,
    classify_sentiment,
    extract_keywords,
    summarize_text,
    unique_matches,
)


class AIAnalyzer:
    EDUCATION_ORG_RE = re.compile(
        r"\b[A-Z][A-Za-z&.-]+(?:\s+[A-Z][A-Za-z&.-]+)*\s+"
        r"(?:University|College|Institute|School)(?:\s+[A-Z][A-Za-z&.-]+)*\b"
    )
    LISTED_ORG_RE = re.compile(
        r"\b(?:companies\s+such\s+as|organizations\s+such\s+as|including|such\s+as)\s+([^.;]+)",
        re.IGNORECASE,
    )
    DISALLOWED_NAME_TERMS = {
        "python", "javascript", "typescript", "react", "node", "nodejs", "sql", "mysql", "mongodb",
        "postgresql", "aws", "docker", "kubernetes", "html", "css", "git", "github", "java", "c++",
        "machine learning", "deep learning", "computer science", "software engineer", "developer",
        "engineer", "intern", "student", "project", "projects", "skills", "education", "experience",
        "summary", "objective", "profile", "resume", "curriculum vitae",
    }
    DISALLOWED_ORG_TERMS = {
        "python", "javascript", "typescript", "react", "node", "sql", "html", "css", "skills",
        "experience", "education", "project", "projects", "summary", "objective", "profile",
    }
    DISALLOWED_ORG_SUBSTRINGS = {
        "graphic design parsons school",
    }
    DISALLOWED_ORG_SUFFIXES = {
        "brand",
        "expo",
        "campaign",
    }
    GENERIC_ORG_PHRASES = {
        "financial institutions", "banking platforms", "financial service providers", "regional banks",
        "government agencies", "regulatory authorities", "technology companies", "private companies",
        "academic institutions", "banking systems", "online banking services", "digital platforms",
        "cloud infrastructure", "transaction systems",
    }
    KNOWN_SINGLE_WORD_ORGS = {
        "google", "microsoft", "nvidia", "meta", "amazon", "apple", "openai", "infosys", "tcs", "wipro",
        "ibm", "oracle", "forage", "accenture", "deloitte", "adobe", "intel", "tesla", "uber",
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self.gemini_client = genai.Client(api_key=self.settings.gemini_api_key) if self.settings.gemini_api_key else None
        self.client = (
            OpenAI(
                api_key=self.settings.openai_api_key,
                timeout=self.settings.openai_timeout_seconds,
            )
            if self.settings.openai_api_key
            else None
        )

    def analyze(self, text: str) -> AnalysisResult:
        if self.gemini_client:
            try:
                return self._analyze_with_gemini(text)
            except Exception:
                return self._analyze_with_rules(text)
        if self.client:
            try:
                return self._analyze_with_llm(text)
            except Exception:
                return self._analyze_with_rules(text)
        return self._analyze_with_rules(text)

    def _analyze_with_gemini(self, text: str) -> AnalysisResult:
        prompt = self._build_analysis_prompt(text)
        response = self.gemini_client.models.generate_content(
            model=self.settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0),
        )

        raw_text = response.text or ""
        payload = self._parse_llm_payload(raw_text)
        entities = self._normalize_entities(payload.get("entities", {}))

        return AnalysisResult(
            summary=payload.get("summary", ""),
            sentiment=self._normalize_sentiment(payload.get("sentiment", "Neutral")),
            entities=self._build_entity_group(text, entities),
            keywords=[],
            confidence=0.9,
        )

    def _analyze_with_llm(self, text: str) -> AnalysisResult:
        prompt = self._build_analysis_prompt(text)

        response = self.client.responses.create(
            model=self.settings.openai_model,
            input=prompt,
            temperature=0
        )

        raw_text = getattr(response, "output_text", "") or ""
        payload = self._parse_llm_payload(raw_text)
        entities = self._normalize_entities(payload.get("entities", {}))

        return AnalysisResult(
            summary=payload.get("summary", ""),
            sentiment=self._normalize_sentiment(payload.get("sentiment", "Neutral")),
            entities=self._build_entity_group(text, entities),
            keywords=[],  # remove noisy field
            confidence=0.9,
        )

    def _build_analysis_prompt(self, text: str) -> str:
        return f"""
You are an AI document analysis system.

Extract structured data from the document.

Return ONLY valid JSON:
{{
  "summary": "2-3 line summary",
  "entities": {{
    "names": ["Real person names only"],
    "dates": ["All dates"],
    "organizations": ["Companies, colleges, institutions"],
    "amounts": ["Money values"],
    "locations": ["Cities, states, countries"],
    "emails": ["Email addresses"],
    "phone_numbers": ["Phone numbers"]
  }},
  "sentiment": "Positive | Negative | Neutral"
}}

STRICT RULES:
- names = only humans, not skills, not technologies, not projects, not headings, not job titles
- include ALL entities present in text
- do not miss email or phone
- organizations = only real companies, colleges, universities, institutions, agencies, or teams
- dates must contain only actual dates or date ranges present in the document
- amounts must contain only monetary values
- if a category has no values, return []
- output ONLY JSON with no markdown and no explanation

TEXT:
{text[:4000]}
"""

    def _normalize_entities(self, entities: dict) -> dict[str, list[str]]:
        return {
            "names": self._filter_names(entities.get("names", [])),
            "dates": self._clean_list(entities.get("dates", [])),
            "organizations": self._filter_organizations(entities.get("organizations", [])),
            "amounts": self._filter_amounts(entities.get("amounts", [])),
            "locations": self._clean_list(entities.get("locations", [])),
            "emails": self._filter_emails(entities.get("emails", [])),
            "phone_numbers": self._filter_phone_numbers(entities.get("phone_numbers", [])),
        }

    def _build_entity_group(self, text: str, entities: dict[str, list[str]]) -> EntityGroup:
        merged = self._merge_with_rule_entities(text, entities)
        return EntityGroup(
            names=merged.get("names", []),
            dates=merged.get("dates", []),
            organizations=merged.get("organizations", []),
            monetary_amounts=merged.get("amounts", []),
            locations=merged.get("locations", []),
            emails=merged.get("emails", []),
            phone_numbers=merged.get("phone_numbers", []),
        )

    def _merge_with_rule_entities(self, text: str, entities: dict[str, list[str]]) -> dict[str, list[str]]:
        merged = dict(entities)
        merged["dates"] = self._merge_lists(merged.get("dates", []), unique_matches(DATE_RE, text))
        merged["amounts"] = self._merge_lists(merged.get("amounts", []), unique_matches(MONEY_RE, text))
        merged["locations"] = self._merge_lists(merged.get("locations", []), unique_matches(LOCATION_RE, text))
        merged["emails"] = self._merge_lists(merged.get("emails", []), unique_matches(EMAIL_RE, text))
        merged["phone_numbers"] = self._merge_lists(
            merged.get("phone_numbers", []),
            [item for item in unique_matches(PHONE_RE, text) if not re.fullmatch(r"\d{4}[-/]\d{4}", item)],
        )
        org_candidates = (
            unique_matches(ORG_RE, text)
            + unique_matches(self.EDUCATION_ORG_RE, text)
            + self._extract_listed_orgs(text)
        )
        merged["organizations"] = self._merge_lists(merged.get("organizations", []), org_candidates)
        return self._normalize_entities(merged)

    def _merge_lists(self, primary: list[str], secondary: list[str]) -> list[str]:
        combined: list[str] = []
        seen: set[str] = set()
        for value in [*primary, *secondary]:
            if not isinstance(value, str):
                continue
            normalized = re.sub(r"\s+", " ", value).strip(" ,.;:-")
            if not normalized:
                continue
            key = normalized.lower()
            if key not in seen:
                seen.add(key)
                combined.append(normalized)
        return combined[:10]

    def _extract_listed_orgs(self, text: str) -> list[str]:
        candidates: list[str] = []
        for match in self.LISTED_ORG_RE.findall(text):
            parts = re.split(r",|\band\b", match)
            for part in parts:
                item = re.sub(r"\s+", " ", part).strip(" ,.;:-")
                if re.fullmatch(r"[A-Z][A-Za-z0-9&.-]+", item) or re.fullmatch(r"[A-Z]{2,}", item):
                    candidates.append(item)
        return candidates

    def _clean_list(self, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for value in values:
            if not isinstance(value, str):
                continue
            normalized = re.sub(r"\s+", " ", value).strip(" ,.;:-")
            if not normalized:
                continue
            key = normalized.lower()
            if key not in seen:
                seen.add(key)
                cleaned.append(normalized)
        return cleaned[:10]

    def _filter_names(self, values: list[str]) -> list[str]:
        cleaned = self._clean_list(values)
        filtered: list[str] = []
        for value in cleaned:
            lowered = value.lower()
            words = re.findall(r"[A-Za-z]+", value)
            if len(words) < 2 or len(words) > 4:
                continue
            if any(term in lowered for term in self.DISALLOWED_NAME_TERMS):
                continue
            if any(word.lower() in {"university", "college", "company", "technologies", "solutions"} for word in words):
                continue
            filtered.append(value)
        return filtered[:10]

    def _filter_organizations(self, values: list[str]) -> list[str]:
        cleaned = self._clean_list(values)
        filtered: list[str] = []
        org_hints = {
            "inc", "llc", "ltd", "limited", "corp", "corporation", "company", "university", "college",
            "institute", "institution", "bank", "agency", "committee", "ministry", "school", "hospital",
            "technologies", "solutions", "labs", "systems",
        }
        for value in cleaned:
            lowered = value.lower()
            words = re.findall(r"[A-Za-z]+", value)
            if any(term == lowered for term in self.DISALLOWED_ORG_TERMS):
                continue
            if lowered in self.GENERIC_ORG_PHRASES:
                continue
            if any(term in lowered for term in self.DISALLOWED_ORG_SUBSTRINGS):
                continue
            if words and words[-1].lower() in self.DISALLOWED_ORG_SUFFIXES:
                continue
            if any(term in lowered for term in self.DISALLOWED_NAME_TERMS):
                continue
            if (
                any(word.lower() in org_hints for word in words)
                or len(words) >= 2
                or lowered in self.KNOWN_SINGLE_WORD_ORGS
                or (len(words) == 1 and words[0].isupper() and len(words[0]) >= 2)
            ):
                filtered.append(value)
        return filtered[:10]

    def _filter_amounts(self, values: list[str]) -> list[str]:
        cleaned = self._clean_list(values)
        return [value for value in cleaned if re.search(r"(\$|€|£|₹|rs\.?|inr|usd|eur|gbp)", value, re.IGNORECASE)][:10]

    def _filter_emails(self, values: list[str]) -> list[str]:
        cleaned = self._clean_list(values)
        return [value for value in cleaned if "@" in value][:10]

    def _filter_phone_numbers(self, values: list[str]) -> list[str]:
        cleaned = self._clean_list(values)
        filtered: list[str] = []
        seen_digits: set[str] = set()
        for value in cleaned:
            if not re.search(r"\+?\d[\d\s().-]{7,}", value):
                continue
            digits = re.sub(r"\D", "", value)
            normalized_digits = digits[1:] if len(digits) == 11 and digits.startswith("1") else digits
            if normalized_digits in seen_digits:
                continue
            seen_digits.add(normalized_digits)
            filtered.append(value)
        return filtered[:10]

    def _normalize_sentiment(self, value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized == "positive":
            return "Positive"
        if normalized == "negative":
            return "Negative"
        return "Neutral"

    def _parse_llm_payload(self, raw_text: str) -> dict:
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(raw_text[start : end + 1])
            raise

    def _analyze_with_rules(self, text: str) -> AnalysisResult:
        return AnalysisResult(
            summary=summarize_text(text),
            sentiment=classify_sentiment(text),
            entities=EntityGroup(
                names=unique_matches(NAME_RE, text)[:10],
                dates=unique_matches(DATE_RE, text)[:10],
                organizations=unique_matches(ORG_RE, text)[:10],
                monetary_amounts=unique_matches(MONEY_RE, text)[:10],
                locations=unique_matches(LOCATION_RE, text)[:10],
                emails=unique_matches(EMAIL_RE, text)[:10],
                phone_numbers=unique_matches(PHONE_RE, text)[:10],
            ),
            keywords=extract_keywords(text),
            confidence=0.62,
        )
