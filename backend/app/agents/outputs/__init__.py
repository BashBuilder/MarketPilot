"""Public agent output contracts."""

from app.agents.outputs.ad_copy_set import AdCopySet, AdVariant
from app.agents.outputs.asset_set import AssetSet, GeneratedAsset
from app.agents.outputs.audience_research import (
    AudienceResearch,
    AudienceSegment,
    ResearchSource,
)
from app.agents.outputs.base import OutputModel
from app.agents.outputs.campaign_brief import CampaignBrief
from app.agents.outputs.compliance_report import ComplianceItem, ComplianceReport
from app.agents.outputs.creative_direction import CreativeDirection
from app.agents.outputs.creative_score import CreativeScore, ScoreDimension
from app.agents.outputs.route_decision import PipelineNode, RouteDecision

__all__ = [
    "AdCopySet",
    "AdVariant",
    "AssetSet",
    "AudienceResearch",
    "AudienceSegment",
    "CampaignBrief",
    "ComplianceItem",
    "ComplianceReport",
    "CreativeDirection",
    "CreativeScore",
    "GeneratedAsset",
    "OutputModel",
    "PipelineNode",
    "ResearchSource",
    "RouteDecision",
    "ScoreDimension",
]
