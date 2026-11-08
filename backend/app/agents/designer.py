"""Designer agent: generate and revise image assets through image tools."""

from collections.abc import Mapping, Sequence

from app.agents.base import BaseAgent
from app.agents.designer_targets import AssetTarget, plan_assets
from app.agents.outputs import AssetSet, GeneratedAsset
from app.core.config import Settings, get_settings
from app.core.errors import ToolError
from app.graph.state import WorkflowState
from app.harness.tool_runner import ToolRunner
from app.harness.verification import (
    AssetSemanticValidator,
    EventCallback,
    SchemaValidator,
    run_with_verification,
)
from app.llm.base import LLMClient
from app.tools.image_tools import EditImageArgs, GeneratedImage, GenerateImageArgs

IMAGE_SIZE = (64, 64)


class DesignerAgent(BaseAgent[AssetSet]):
    """Tool-driven designer: assets come from image tools, not model prose."""

    def __init__(self, settings: Settings | None = None) -> None:
        resolved = settings or get_settings()
        super().__init__(
            name="designer",
            output_model=AssetSet,
            prompt_name="designer",
            settings=resolved,
        )
        self._resolved = resolved

    async def run(
        self,
        state: WorkflowState,
        llm: LLMClient,
        emit: EventCallback,
        tools: ToolRunner | None = None,
    ) -> AssetSet:
        """Generate or revise assets; guardrail denials propagate without retry."""
        if tools is None:
            raise ToolError("generate_image", "designer requires image tools")
        targets = plan_assets(state)
        if not targets:
            raise ToolError("generate_image", "designer has no image prompts to generate")

        generated = [await self._execute(target, tools) for target in targets]
        output = AssetSet(assets=_merge(state, targets, generated))

        async def step(_: Sequence[Mapping[str, str]]) -> AssetSet:
            return output

        return await run_with_verification(
            step,
            prompt=[],
            agent=self.name,
            validators=(
                SchemaValidator(AssetSet),
                AssetSemanticValidator(self._resolved.asset_dir),
            ),
            on_event=emit,
            settings=self._resolved,
        )

    async def _execute(self, target: AssetTarget, tools: ToolRunner) -> GeneratedAsset:
        if target.source is not None:
            raw = await tools(
                "edit_image",
                EditImageArgs(image_path=target.source.uri, instruction=target.instruction),
                step="designer-edit",
            )
        else:
            raw = await tools(
                "generate_image",
                GenerateImageArgs(
                    prompt=target.prompt,
                    negative_prompt=target.negative_prompt[:1000],
                    seed=target.seed,
                    size=IMAGE_SIZE,
                ),
                step="designer-generate",
            )
        if not isinstance(raw, GeneratedImage):
            raise ToolError("generate_image", "image tool returned an unexpected result")
        return GeneratedAsset(
            uri=raw.path,
            checksum=raw.checksum,
            model=raw.model,
            seed=raw.seed,
            prompt=raw.prompt,
        )


def _merge(
    state: WorkflowState,
    targets: Sequence[AssetTarget],
    generated: Sequence[GeneratedAsset],
) -> list[GeneratedAsset]:
    replacements = {
        target.source.uri: asset
        for target, asset in zip(targets, generated, strict=True)
        if target.source is not None
    }
    if not replacements:
        return list(generated)
    previous = state.assets.assets if state.assets is not None else []
    return [replacements.get(asset.uri, asset) for asset in previous]
