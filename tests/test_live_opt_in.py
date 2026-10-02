from typing import cast

import pytest


@pytest.mark.live
def test_live_configuration_available():
    from rag_audit.provider_config import configured_provider
    from rag_audit.settings import Settings

    provider, prices = configured_provider(Settings())
    assert provider.identity == "responses" and prices


def test_live_skips_without_key_or_opt_in(monkeypatch):
    from conftest import pytest_collection_modifyitems

    class Config:
        def __init__(self, enabled):
            self.enabled = enabled

        def getoption(self, name):
            return self.enabled

    class Item:
        keywords = {"live": True}

        def __init__(self):
            self.markers = []

        def add_marker(self, mark):
            self.markers.append(mark)

    monkeypatch.setenv("GENERATION_KEY_ENV", "SYNTHETIC_ABSENT_KEY")
    monkeypatch.delenv("SYNTHETIC_ABSENT_KEY", raising=False)
    for enabled in (False, True):
        item = Item()
        pytest_collection_modifyitems(
            cast(pytest.Config, Config(enabled)), [cast(pytest.Item, item)]
        )
        assert any(mark.name == "skip" for mark in item.markers)
