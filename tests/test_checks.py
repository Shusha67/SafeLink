import pytest

from app.checks.base import CheckResult, SecurityCheck


class FailingCheck(SecurityCheck):
    name = "Failing"

    async def _execute(self, url: str) -> CheckResult:
        raise RuntimeError("Intentional failure")


class PassingCheck(SecurityCheck):
    name = "Passing"

    async def _execute(self, url: str) -> CheckResult:
        return CheckResult(name=self.name, passed=True, reason="All good")


@pytest.mark.asyncio
async def test_failing_check_is_isolated():
    check = FailingCheck()
    result = await check.run("http://example.com")
    assert result.passed is True
    assert result.penalty == 0
    assert "error" in result.reason.lower() or "skipped" in result.reason.lower()


@pytest.mark.asyncio
async def test_passing_check_returns_result():
    check = PassingCheck()
    result = await check.run("http://example.com")
    assert result.passed is True
    assert result.reason == "All good"
