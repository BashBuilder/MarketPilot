"""Workflow state fixtures for context-budget tests."""

from app.agents.outputs import (
    AdCopySet,
    AdVariant,
    AssetSet,
    AudienceResearch,
    AudienceSegment,
    CampaignBrief,
    ComplianceItem,
    ComplianceReport,
    CreativeDirection,
    CreativeScore,
    GeneratedAsset,
    ResearchSource,
    ScoreDimension,
)
from app.graph.state import WorkflowState

PROMPT = "soft daylight portrait of a person with healthy hair"


def make_state(*, long: bool = False) -> WorkflowState:
    brief = CampaignBrief(
        product="HydraSilk Shampoo",
        goal="Launch a hydrating shampoo for adults with dry hair.",
        audience="Adults aged 25 to 40 who style their hair daily.",
        tone="Warm and confident",
        channels=["Instagram", "Email"],
        constraints=["No medical claims"],
    )
    segment = AudienceSegment(
        name="Busy professionals",
        description="Adults who want a fast routine that still feels polished.",
    )
    source = ResearchSource(title="Hair-care market report", url="https://example.com/report")
    research = AudienceResearch(
        segments=[segment] * (10 if long else 1),
        pain_points=["Frizz returns by midday"] * (20 if long else 1),
        messaging_angles=["Effortless confidence"] * (20 if long else 1),
        sources=[source] * (20 if long else 1),
    )
    copy = AdCopySet(
        variants=[
            AdVariant(
                channel="Instagram",
                headline="Morning hair, handled",
                description="A lightweight serum for all-day smoothness. " * (20 if long else 1),
                cta="Shop the serum",
            )
            for _ in range(50 if long else 1)
        ]
    )
    direction = CreativeDirection(
        image_prompts=[PROMPT] * (20 if long else 1),
        video_prompts=[PROMPT] * (20 if long else 1),
        style_guide="Warm neutral palette with editorial lighting." * (40 if long else 1),
        composition="Centered subject with generous negative space." * (40 if long else 1),
        negative_prompts=["harsh shadows"] * (20 if long else 1),
    )
    assets = AssetSet(
        assets=[
            GeneratedAsset(
                uri="assets/hero.png",
                checksum="a" * 64,
                model="fake",
                seed=7,
                prompt=PROMPT,
            )
        ]
        * (20 if long else 1)
    )
    compliance = ComplianceReport(
        items=[
            ComplianceItem(
                check="No medical claims",
                passed=True,
                reason="Copy avoids cure language",
            )
        ]
    )
    dimension = ScoreDimension(score=8, justification="Consistent with the brief")
    score = CreativeScore(
        brief_alignment=dimension,
        audience_fit=dimension,
        copy_quality=dimension,
        visual_quality=dimension,
        compliance_risk=dimension,
        total=80.0,
    )
    return WorkflowState(
        idea="Create a hair-care campaign for adults aged 25 to 40",
        brief=brief,
        research=research,
        copy=copy,
        direction=direction,
        assets=assets,
        compliance=compliance,
        score=score,
        status="awaiting_approval",
        versions=[1],
    )
