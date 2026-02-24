from __future__ import annotations

from typing import Any

import requests
from requests_oauthlib import OAuth1


class SchoologyClient:
    def __init__(
        self,
        domain: str,
        key: str,
        secret: str,
        token: str = "",
        token_secret: str = "",
    ) -> None:
        cleaned_domain = domain.strip().rstrip("/")
        if not cleaned_domain:
            raise ValueError("Schoology domain is required")
        if not key or not secret:
            raise ValueError("Schoology API key and secret are required")

        self.base_url = f"https://{cleaned_domain}/v1"
        self.auth = OAuth1(key, secret, token or None, token_secret or None)

    def _get(self, path: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.base_url}{path}",
            auth=self.auth,
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Schoology API error {response.status_code}: {response.text[:200]}")
        return response.json()

    def fetch_assignments(self, section_id: str) -> list[dict[str, Any]]:
        payload = self._get(f"/sections/{section_id}/assignments")
        assignments = payload.get("assignment", [])
        normalized: list[dict[str, Any]] = []
        for item in assignments:
            normalized.append(
                {
                    "id": item.get("id", ""),
                    "title": item.get("title", "Untitled"),
                    "description": item.get("description", "") or "No description",
                    "due": item.get("due", "No due date"),
                    "max_points": float(item.get("max_points") or 0),
                    "web_url": item.get("web_url")
                    or item.get("assignment_url")
                    or item.get("url")
                    or "",
                }
            )
        return normalized

    def fetch_grades(self, section_id: str) -> dict[str, Any]:
        payload = self._get(f"/sections/{section_id}/grades")
        grade = payload.get("grade", {})
        return {
            "current_score": grade.get("current_score") or grade.get("grade") or "",
            "current_grade": grade.get("current_grade") or grade.get("letter_grade") or "",
        }
