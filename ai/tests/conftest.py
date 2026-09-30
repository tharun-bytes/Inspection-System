from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(autouse=True, scope="session")
def isolated_artifacts(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Keep test runs out of the real ``ai/artifacts`` directory.

    This must be session-scoped: the fixtures that train a model are themselves
    module-scoped, and higher-scoped fixtures are instantiated first. With a
    function-scoped patch the initial training would still write to the real
    artifacts path, and the service would later load that test-sized model at
    startup instead of training the production configuration.
    """
    import app.model as model_module

    artifact_dir: Path = tmp_path_factory.mktemp("ai-artifacts")

    with MonkeyPatch.context() as patch:
        patch.setattr(model_module, "ARTIFACT_DIR", artifact_dir)
        patch.setattr(
            model_module, "MODEL_PATH", artifact_dir / "severity_model.joblib"
        )
        patch.setattr(
            model_module, "METADATA_PATH", artifact_dir / "model_metadata.json"
        )
        yield
