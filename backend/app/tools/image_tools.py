"""Image generation tools backed by a deterministic, pluggable provider."""

import hashlib
from pathlib import Path
from typing import Annotated, Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings
from app.core.errors import ToolError
from app.harness.registry import ToolRegistry, ToolSpec
from app.tools.image_png import encode_solid_png

Checksum = Annotated[str, Field(pattern=r"^[0-9a-fA-F]{64}$")]
Dimension = Annotated[int, Field(ge=1, le=1024)]


class GeneratedImage(BaseModel):
    """Metadata for one generated or edited image file."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    path: Annotated[str, Field(min_length=1, max_length=2000)]
    checksum: Checksum
    model: Annotated[str, Field(min_length=1, max_length=100)]
    seed: Annotated[int, Field(ge=0)]
    prompt: Annotated[str, Field(min_length=1, max_length=1000)]


class ImageGenerator(Protocol):
    """Provider contract for image generation and editing."""

    async def generate(
        self,
        prompt: str,
        negative_prompt: str,
        seed: int,
        size: tuple[int, int],
    ) -> GeneratedImage: ...

    async def edit(self, image_path: str, instruction: str) -> GeneratedImage: ...


class FakeImageGenerator:
    """Write small deterministic PNGs without calling a real model."""

    model = "fake"

    def __init__(self, asset_dir: Path | None = None) -> None:
        configured = asset_dir if asset_dir is not None else get_settings().asset_dir
        self._root = Path(configured).resolve()

    async def generate(
        self,
        prompt: str,
        negative_prompt: str,
        seed: int,
        size: tuple[int, int],
    ) -> GeneratedImage:
        width, height = size
        digest = _digest("generate", prompt, negative_prompt, seed, width, height)
        path = self._root / f"generated-{digest[:16]}.png"
        self._write(path, width, height, digest)
        return self._metadata(path, seed, prompt)

    async def edit(self, image_path: str, instruction: str) -> GeneratedImage:
        source = self._resolve(image_path)
        if not source.is_file():
            raise ToolError("edit_image", f"source image does not exist: {image_path}")
        source_bytes = source.read_bytes()
        seed = int(hashlib.sha256(source_bytes + instruction.encode("utf-8")).hexdigest()[:16], 16)
        digest = _digest("edit", hashlib.sha256(source_bytes).hexdigest(), instruction)
        path = self._root / f"edited-{digest[:16]}.png"
        self._write(path, 64, 64, digest)
        return self._metadata(path, seed, instruction)

    def _write(self, path: Path, width: int, height: int, digest: str) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        rgb = (int(digest[0:2], 16), int(digest[2:4], 16), int(digest[4:6], 16))
        path.write_bytes(encode_solid_png(width, height, rgb))

    def _resolve(self, image_path: str) -> Path:
        candidate = Path(image_path)
        resolved = (candidate if candidate.is_absolute() else self._root / candidate).resolve()
        try:
            resolved.relative_to(self._root)
        except ValueError as error:
            message = "source image must live in the asset directory"
            raise ToolError("edit_image", message) from error
        return resolved

    def _metadata(self, path: Path, seed: int, prompt: str) -> GeneratedImage:
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        return GeneratedImage(
            path=str(path),
            checksum=checksum,
            model=self.model,
            seed=seed,
            prompt=prompt,
        )


class GenerateImageArgs(BaseModel):
    """Inputs for one text-to-image call."""

    prompt: Annotated[str, Field(min_length=1, max_length=1000)]
    negative_prompt: Annotated[str, Field(max_length=1000)] = ""
    seed: Annotated[int, Field(ge=0, le=2**63 - 1)] = 0
    size: tuple[Dimension, Dimension] = (64, 64)


class EditImageArgs(BaseModel):
    """Inputs for one instruction-based image edit."""

    image_path: Annotated[str, Field(min_length=1, max_length=2000)]
    instruction: Annotated[str, Field(min_length=1, max_length=1000)]


def _default_generator() -> ImageGenerator:
    return FakeImageGenerator()


async def generate_image(
    args: GenerateImageArgs,
    generator: ImageGenerator | None = None,
) -> GeneratedImage:
    """Generate one image through the configured provider."""
    return await (generator or _default_generator()).generate(
        args.prompt,
        args.negative_prompt,
        args.seed,
        args.size,
    )


async def edit_image(
    args: EditImageArgs,
    generator: ImageGenerator | None = None,
) -> GeneratedImage:
    """Edit one existing asset through the configured provider."""
    return await (generator or _default_generator()).edit(args.image_path, args.instruction)


def register_image_tools(
    registry: ToolRegistry,
    generator: ImageGenerator | None = None,
) -> None:
    """Register the Designer's image tools with the harness registry."""
    active = generator or _default_generator()

    async def bound_generate(args: GenerateImageArgs) -> GeneratedImage:
        return await generate_image(args, generator=active)

    async def bound_edit(args: EditImageArgs) -> GeneratedImage:
        return await edit_image(args, generator=active)

    registry.register_tool(
        ToolSpec(
            name="generate_image",
            args_model=GenerateImageArgs,
            handler=bound_generate,
            side_effecting=True,
        )
    )
    registry.register_tool(
        ToolSpec(
            name="edit_image",
            args_model=EditImageArgs,
            handler=bound_edit,
            side_effecting=True,
        )
    )


def _digest(*parts: object) -> str:
    payload = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
