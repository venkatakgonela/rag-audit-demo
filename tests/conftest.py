import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-integration", action="store_true", default=False)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if not config.getoption("--run-integration"):
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Use make test-integration"))


@pytest.fixture(autouse=True)
def isolate_unit_settings(request: pytest.FixtureRequest, monkeypatch, tmp_path):
    if request.node.get_closest_marker("integration") is None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("DATABASE_CONNECT_TIMEOUT", raising=False)
