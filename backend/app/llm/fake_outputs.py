"""Canned agent outputs for the golden hair-care idea (GOLDEN_IDEAS[0])."""

from collections.abc import Mapping
from typing import Any

from pydantic import HttpUrl

from app.agents.outputs import (
    AdCopySet,
    AdVariant,
    AudienceResearch,
    AudienceSegment,
    CampaignBrief,
    ComplianceItem,
    ComplianceReport,
    CreativeDirection,
    CreativeScore,
    ResearchSource,
    ScoreDimension,
)
from app.agents.scoring import weighted_total
from app.tools.search_tools import FIXED_RESULTS


def brief() -> CampaignBrief:
    return CampaignBrief(
        product="HydraSilk Shampoo",
        goal="Launch a hydrating shampoo for adults with dry hair.",
        audience="Adults aged 25 to 40 who style their hair daily.",
        tone="Warm and confident",
        channels=["Instagram"],
        constraints=["No medical claims", "No guaranteed-result language"],
    )


def research(context: Mapping[str, Any]) -> AudienceResearch:
    results = context.get("search_results")
    first = results[0] if isinstance(results, list) and results else None
    title = str(first["title"]) if isinstance(first, dict) else FIXED_RESULTS[0].title
    url = str(first["url"]) if isinstance(first, dict) else str(FIXED_RESULTS[0].url)
    return AudienceResearch(
        segments=[
            AudienceSegment(
                name="Busy professionals",
                description="Adults who want a fast routine that still feels polished.",
            )
        ],
        pain_points=["Frizz returns by midday"],
        messaging_angles=["Effortless confidence"],
        sources=[ResearchSource(title=title, url=HttpUrl(url))],
    )


def copy() -> AdCopySet:
    return AdCopySet(
        variants=[
            AdVariant(
                channel="Instagram",
                headline="Morning hair, handled",
                description="A lightweight serum for all-day smoothness.",
                cta="Shop the serum",
            )
        ]
    )


def direction() -> CreativeDirection:
    return CreativeDirection(
        image_prompts=["soft daylight portrait of a person with healthy hair"],
        video_prompts=["slow shelf pan across a sunlit bathroom"],
        style_guide="Warm neutral palette with editorial lighting.",
        composition="Centered subject with generous negative space.",
        negative_prompts=["harsh shadows"],
    )


def compliance(context: Mapping[str, Any]) -> ComplianceReport:
    labels = context.get("subjects")
    if not isinstance(labels, list) or not labels:
        labels = labels_from_context(context)
    return ComplianceReport(
        items=[
            ComplianceItem(
                check=f"{label} - no unsupported claims",
                passed=True,
                reason="Copy avoids medical and guaranteed-result language.",
            )
            for label in labels
        ]
    )


def labels_from_context(context: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    copy_section = context.get("copy")
    if isinstance(copy_section, dict):
        labels.extend(f"copy:{variant['channel']}" for variant in copy_section.get("variants", []))
    assets = context.get("assets")
    if isinstance(assets, dict):
        labels.extend(f"asset:{asset['uri']}" for asset in assets.get("assets", []))
    return labels or ["copy:Instagram"]


def score() -> CreativeScore:
    dimensions = {
        "brief_alignment": _dimension("Consistent with the brief"),
        "audience_fit": _dimension("Fits the audience"),
        "copy_quality": _dimension("Clear and on brief"),
        "visual_quality": _dimension("Production ready"),
        "compliance_risk": _dimension("Low risk"),
    }
    return CreativeScore(**dimensions, total=weighted_total(dimensions.values()))


def _dimension(justification: str) -> ScoreDimension:
    return ScoreDimension(score=8, justification=justification)
