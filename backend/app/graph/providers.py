"""Provider selection for one workflow runtime.

Only fake image, search and embedding providers exist today; the difference
between real and fake mode is the LLM (DeepSeek vs the scripted pipeline).
"""

from dataclasses import dataclass

from app.core.config import Settings
from app.llm.base import LLMClient
from app.llm.deepseek import DeepSeekClient
from app.llm.embeddings import Embedder, build_embedder
from app.llm.fake_pipeline import FakePipelineLLM
from app.tools.image_tools import FakeImageGenerator, ImageGenerator
from app.tools.search_tools import FakeSearchProvider, SearchProvider


@dataclass(frozen=True, slots=True)
class PipelineProviders:
    llm: LLMClient
    images: ImageGenerator
    search: SearchProvider
    embedder: Embedder


def build_providers(settings: Settings) -> PipelineProviders:
    """Return the configured provider set; fake mode never reaches the network."""
    llm: LLMClient = FakePipelineLLM() if settings.app_mode == "fake" else DeepSeekClient(settings)
    return PipelineProviders(
        llm=llm,
        images=FakeImageGenerator(settings.asset_dir),
        search=FakeSearchProvider(),
        embedder=build_embedder(settings),
    )
