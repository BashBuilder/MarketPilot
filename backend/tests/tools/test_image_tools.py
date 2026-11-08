"""Tests for deterministic fake image tools and their permissions."""

import hashlib
from pathlib import Path

import pytest

from app.core.errors import GuardrailViolation, ToolError
from app.harness.image_checks import is_decodable_png
from app.harness.registry import ToolRegistry
from app.tools.image_tools import (
    EditImageArgs,
    FakeImageGenerator,
    GenerateImageArgs,
    edit_image,
    generate_image,
    register_image_tools,
)


async def test_generate_writes_a_valid_png_with_metadata(tmp_path: Path) -> None:
    result = await FakeImageGenerator(tmp_path).generate("a red bottle", "blur", 7, (32, 24))

    data = Path(result.path).read_bytes()
    assert is_decodable_png(data)
    assert result.checksum == hashlib.sha256(data).hexdigest()
    assert result.model == "fake"
    assert result.seed == 7
    assert result.prompt == "a red bottle"


async def test_same_seed_and_inputs_produce_the_same_checksum(tmp_path: Path) -> None:
    generator = FakeImageGenerator(tmp_path)

    first = await generator.generate("prompt", "", 42, (16, 16))
    second = await generator.generate("prompt", "", 42, (16, 16))
    other = await generator.generate("prompt", "", 43, (16, 16))

    assert first.checksum == second.checksum
    assert first.path == second.path
    assert first.checksum != other.checksum


async def test_edit_writes_a_new_file_and_keeps_provenance(tmp_path: Path) -> None:
    generator = FakeImageGenerator(tmp_path)
    source = await generator.generate("bottle", "", 1, (8, 8))

    edited = await generator.edit(source.path, "add a green leaf")

    assert Path(edited.path).is_file()
    assert edited.path != source.path
    assert is_decodable_png(Path(edited.path).read_bytes())
    assert edited.seed >= 0
    assert edited.prompt == "add a green leaf"


async def test_edit_rejects_missing_or_escaping_paths(tmp_path: Path) -> None:
    generator = FakeImageGenerator(tmp_path / "assets")

    with pytest.raises(ToolError, match="does not exist"):
        await generator.edit("missing.png", "add a leaf")
    with pytest.raises(ToolError, match="asset directory"):
        await generator.edit(str(tmp_path / "outside.png"), "add a leaf")


async def test_tool_functions_return_generated_metadata(tmp_path: Path) -> None:
    generator = FakeImageGenerator(tmp_path)

    generated = await generate_image(
        GenerateImageArgs(prompt="bottle", seed=5, size=(8, 8)),
        generator=generator,
    )
    edited = await edit_image(
        EditImageArgs(image_path=generated.path, instruction="warmer light"),
        generator=generator,
    )

    assert Path(generated.path).is_file()
    assert Path(edited.path).is_file()


def test_image_tools_are_registered_for_the_designer_only(tmp_path: Path) -> None:
    registry = ToolRegistry()
    register_image_tools(registry, FakeImageGenerator(tmp_path))

    assert registry.get_tool("designer", "generate_image").name == "generate_image"
    assert registry.get_tool("designer", "edit_image").name == "edit_image"
    with pytest.raises(GuardrailViolation, match="not allowed"):
        registry.get_tool("brief", "generate_image")
    with pytest.raises(GuardrailViolation, match="not allowed"):
        registry.get_tool("research", "edit_image")
