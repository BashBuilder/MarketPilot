"""Deterministic agent outputs used by workflow integration tests."""

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

PROMPT = "soft daylight portrait of a person with healthy hair"
NEGATIVE = "harsh shadows"


def brief() -> CampaignBrief:
    return CampaignBrief(
        product="HydraSilk Shampoo",
        goal="Launch a hydrating shampoo for adults with dry hair.",
        audience="Adults aged 25 to 40 who style their hair daily.",
        tone="Warm and confident",
        channels=["Instagram"],
        constraints=["No medical claims"],
    )


def research() -> AudienceResearch:
    return AudienceResearch(
        segments=[
            AudienceSegment(
                name="Busy professionals",
                description="Adults who want a fast routine that still feels polished.",
            )
        ],
        pain_points=["Frizz returns by midday"],
        messaging_angles=["Effortless confidence"],
        sources=[ResearchSource(title="Hair care market overview", url=FIXED_RESULTS[0].url)],
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
        image_prompts=[PROMPT],
        video_prompts=["slow shelf pan across a sunlit bathroom"],
        style_guide="Warm neutral palette with editorial lighting.",
        composition="Centered subject with generous negative space.",
        negative_prompts=[NEGATIVE],
    )


def compliance(
    asset_path: str,
    *,
    copy_passed: bool = True,
    asset_passed: bool = True,
) -> ComplianceReport:
    return ComplianceReport(
        items=[
            ComplianceItem(
                check="copy:Instagram - no unsupported claims",
                passed=copy_passed,
                reason=(
                    "Copy avoids medical and guaranteed-result language."
                    if copy_passed
                    else "The headline promises results that need evidence."
                ),
            ),
            ComplianceItem(
                check=f"asset:{asset_path} - no brand imagery",
                passed=asset_passed,
                reason=(
                    "No brand or likeness is described."
                    if asset_passed
                    else "The image prompt mentions a brand logo."
                ),
            ),
        ]
    )


def score(
    *,
    brief_alignment: float = 8,
    audience_fit: float = 8,
    copy_quality: float = 8,
    visual_quality: float = 8,
    compliance_risk: float = 8,
) -> CreativeScore:
    scored = {
        "brief_alignment": ScoreDimension(
            score=brief_alignment, justification="Consistent with the brief"
        ),
        "audience_fit": ScoreDimension(score=audience_fit, justification="Fits the audience"),
        "copy_quality": ScoreDimension(score=copy_quality, justification="Clear and on brief"),
        "visual_quality": ScoreDimension(score=visual_quality, justification="Production ready"),
        "compliance_risk": ScoreDimension(score=compliance_risk, justification="Low risk"),
    }
    return CreativeScore(
        brief_alignment=scored["brief_alignment"],
        audience_fit=scored["audience_fit"],
        copy_quality=scored["copy_quality"],
        visual_quality=scored["visual_quality"],
        compliance_risk=scored["compliance_risk"],
        total=weighted_total(scored.values()),
    )
