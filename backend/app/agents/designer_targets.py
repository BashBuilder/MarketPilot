"""Planning helpers for Designer image generation and revisions."""

from typing import NamedTuple

from app.agents.outputs import AssetSet, ComplianceItem, GeneratedAsset
from app.core.errors import ToolError
from app.graph.state import WorkflowState


class AssetTarget(NamedTuple):
    """One image call the Designer must make."""

    prompt: str
    negative_prompt: str
    seed: int
    source: GeneratedAsset | None
    instruction: str


def plan_assets(state: WorkflowState) -> tuple[AssetTarget, ...]:
    """Return generate targets normally, or edit targets for flagged assets."""
    failed = _failed_asset_items(state)
    if failed and state.assets is not None:
        return tuple(_edit_target(asset, failed) for asset in _flagged_assets(state.assets, failed))

    if state.direction is None:
        raise ToolError("generate_image", "designer requires creative direction")
    negative = " ".join(state.direction.negative_prompts)
    return tuple(
        AssetTarget(
            prompt=prompt,
            negative_prompt=negative,
            seed=index,
            source=None,
            instruction="",
        )
        for index, prompt in enumerate(state.direction.image_prompts)
    )


def _failed_asset_items(state: WorkflowState) -> list[ComplianceItem]:
    if state.compliance is None or state.assets is None:
        return []
    failed = [item for item in state.compliance.items if not item.passed]
    return [item for item in failed if _mentions_an_asset(item, state.assets)]


def _mentions_an_asset(item: ComplianceItem, assets: AssetSet) -> bool:
    text = f"{item.check} {item.reason}".casefold()
    if "asset" in text or "image" in text:
        return True
    return any(
        asset.uri.casefold() in text or asset.prompt.casefold() in text for asset in assets.assets
    )


def _flagged_assets(assets: AssetSet, failed: list[ComplianceItem]) -> tuple[GeneratedAsset, ...]:
    text = " ".join(f"{item.check} {item.reason}" for item in failed).casefold()
    matched = tuple(
        asset
        for asset in assets.assets
        if asset.uri.casefold() in text or asset.prompt.casefold() in text
    )
    return matched or tuple(assets.assets)


def _edit_target(asset: GeneratedAsset, failed: list[ComplianceItem]) -> AssetTarget:
    reasons = "; ".join(item.reason for item in failed)
    return AssetTarget(
        prompt=asset.prompt,
        negative_prompt="",
        seed=asset.seed,
        source=asset,
        instruction=f"Fix the flagged compliance issue: {reasons}",
    )
