import pytest
from pydantic import ValidationError

from rag_audit.settings import Settings

SYNTHETIC_URL = (
    "postgresql://synthetic_user:synthetic_secret_sentinel@127.0.0.1/synthetic_db"
)


def test_defaults():
    settings = Settings()
    assert settings.database_url is None
    assert settings.database_connect_timeout == 5


def test_environment_overrides_dotenv(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text(
        "DATABASE_CONNECT_TIMEOUT=7\nPOSTGRES_DB=synthetic_db\n"
    )
    assert Settings().database_connect_timeout == 7
    monkeypatch.setenv("DATABASE_CONNECT_TIMEOUT", "9")
    monkeypatch.setenv("DATABASE_URL", SYNTHETIC_URL)
    settings = Settings()
    assert settings.database_connect_timeout == 9
    assert settings.database_url is not None
    assert settings.database_url.get_secret_value() == SYNTHETIC_URL


def test_settings_do_not_leak_database_url(monkeypatch, caplog, capsys):
    caplog.set_level("DEBUG")
    monkeypatch.setenv("DATABASE_URL", SYNTHETIC_URL)
    settings = Settings()
    captured = capsys.readouterr()
    exposed = (
        captured.out
        + captured.err
        + caplog.text
        + str(settings)
        + repr(settings)
        + settings.model_dump_json()
        + repr(settings.model_dump())
    )
    assert SYNTHETIC_URL not in exposed
    assert "synthetic_secret_sentinel" not in exposed
    assert captured.out == captured.err == ""


@pytest.mark.parametrize("value", ["0", "31", "invalid", SYNTHETIC_URL])
def test_invalid_timeout_hides_input(monkeypatch, value):
    monkeypatch.setenv("DATABASE_CONNECT_TIMEOUT", value)
    with pytest.raises(ValidationError) as caught:
        Settings()
    assert "input_value" not in str(caught.value)
    assert "synthetic_secret_sentinel" not in str(caught.value)
