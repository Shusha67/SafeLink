import httpx

from app.checks.base import CheckResult, SecurityCheck
from app.config import settings


class GoogleSafeBrowsingCheck(SecurityCheck):
    name = "GoogleSafeBrowsing"

    async def _execute(self, url: str) -> CheckResult:
        if not settings.google_safe_browsing_api_key:
            return CheckResult(
                name=self.name, passed=True,
                reason="Google Safe Browsing API key not configured (skipped)",
            )

        api_url = (
            "https://safebrowsing.googleapis.com/v4/threatMatches:find"
            f"?key={settings.google_safe_browsing_api_key}"
        )
        payload = {
            "client": {"clientId": "safelink", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }

        async with httpx.AsyncClient(timeout=settings.check_timeout_seconds) as client:
            resp = await client.post(api_url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if data.get("matches"):
            threat = data["matches"][0].get("threatType", "unknown threat")
            return CheckResult(
                name=self.name, passed=False, penalty=50,
                reason=f"Flagged by Google Safe Browsing: {threat}",
            )

        return CheckResult(name=self.name, passed=True, reason="Not found in Google Safe Browsing blacklist")
