"""Shared fixtures for Supervisor routing tests."""

from app.agents.outputs import ComplianceItem, CreativeScore, ScoreDimension
from app.agents.scoring import weighted_total
from app.core.config import Settings


def settings(*, threshold: int = 70, max_loops: int = 2) -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        score_threshold=threshold,
        max_auto_loops=max_loops,
        _env_file=None,
    )


def dimension(value: float) -> ScoreDimension:
    return ScoreDimension(score=value, justification="Clear and on brief")


def score(
    *,
    brief_alignment: float = 8,
    audience_fit: float = 8,
    copy_quality: float = 8,
    visual_quality: float = 8,
    compliance_risk: float = 8,
) -> CreativeScore:
    scored = {
        "brief_alignment": dimension(brief_alignment),
        "audience_fit": dimension(audience_fit),
        "copy_quality": dimension(copy_quality),
        "visual_quality": dimension(visual_quality),
        "compliance_risk": dimension(compliance_risk),
    }
    return CreativeScore(
        brief_alignment=scored["brief_alignment"],
        audience_fit=scored["audience_fit"],
        copy_quality=scored["copy_quality"],
        visual_quality=scored["visual_quality"],
        compliance_risk=scored["compliance_risk"],
        total=weighted_total(scored.values()),
    )


def failure(check: str) -> ComplianceItem:
    return ComplianceItem(check=check, passed=False, reason="Blocked by policy")
