import os
import socket

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-integration", action="store_true", default=False)
    parser.addoption("--run-live", action="store_true", default=False)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        if "live" in item.keywords:
            key_name = os.environ.get("GENERATION_KEY_ENV", "")
            if (
                not config.getoption("--run-live")
                or not key_name
                or not os.environ.get(key_name)
            ):
                item.add_marker(
                    pytest.mark.skip(
                        reason="Live requires explicit opt-in and environment key"
                    )
                )
    if not config.getoption("--run-integration"):
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Use make test-integration"))


@pytest.fixture(autouse=True)
def isolate_unit_settings(request: pytest.FixtureRequest, monkeypatch, tmp_path):
    if (
        request.node.get_closest_marker("integration") is None
        and request.node.get_closest_marker("live") is None
    ):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("DATABASE_CONNECT_TIMEOUT", raising=False)

        def deny_network(*args, **kwargs):
            raise AssertionError("Offline tests cannot access network")

        monkeypatch.setattr(socket.socket, "connect", deny_network)
