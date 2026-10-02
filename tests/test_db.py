import sys
import traceback
from unittest.mock import MagicMock, patch

import psycopg
import pytest
from pydantic import SecretStr

from rag_audit.db import DatabaseCheckError, check_vector_extension, main
from rag_audit.settings import Settings

SYNTHETIC_URL = (
    "postgresql://synthetic_user:synthetic_secret_sentinel@127.0.0.1/synthetic_db"
)


@pytest.mark.parametrize("url", [None, SecretStr("")])
def test_missing_url_fails_without_connecting(url):
    with patch("rag_audit.db.psycopg.connect") as connect:
        with pytest.raises(DatabaseCheckError, match="DATABASE_URL is required"):
            check_vector_extension(Settings(database_url=url))
    connect.assert_not_called()


@pytest.mark.parametrize(
    "row, expected", [((True,), True), ((False,), False), (None, False)]
)
def test_vector_check_and_connection_cleanup(row, expected):
    with patch("rag_audit.db.psycopg.connect") as connect:
        connection = connect.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = row
        assert (
            check_vector_extension(Settings(database_url=SecretStr(SYNTHETIC_URL)))
            is expected
        )
        connect.assert_called_once_with(SYNTHETIC_URL, connect_timeout=5)
        cursor.execute.assert_called_once_with(
            "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        connection.cursor.return_value.__exit__.assert_called_once()
        connect.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize("failure_stage", ["connect", "query"])
def test_database_errors_are_sanitised(failure_stage, caplog, capsys):
    caplog.set_level("DEBUG")
    with patch("rag_audit.db.psycopg.connect") as connect:
        failure = psycopg.OperationalError(f"Synthetic driver failure: {SYNTHETIC_URL}")
        if failure_stage == "connect":
            connect.side_effect = failure
        else:
            connection = connect.return_value.__enter__.return_value
            cursor = connection.cursor.return_value.__enter__.return_value
            cursor.execute.side_effect = failure
        with pytest.raises(
            DatabaseCheckError, match="Database connection or operation failed"
        ) as caught:
            check_vector_extension(Settings(database_url=SecretStr(SYNTHETIC_URL)))
        if failure_stage == "query":
            connect.return_value.__exit__.assert_called_once()
    captured = capsys.readouterr()
    exposed = "".join(traceback.format_exception(caught.value))
    exposed += captured.out + captured.err + caplog.text
    assert SYNTHETIC_URL not in exposed
    assert "synthetic_secret_sentinel" not in exposed


def test_db_init_executes_supplied_sql(monkeypatch, tmp_path, capsys):
    sql_file = tmp_path / "synthetic-init.sql"
    sql_file.write_text("CREATE EXTENSION IF NOT EXISTS vector;\n")
    monkeypatch.setenv("DATABASE_URL", SYNTHETIC_URL)
    monkeypatch.setattr(sys, "argv", ["db", "--init-sql", str(sql_file)])
    with patch("rag_audit.db.psycopg.connect") as connect:
        connection = connect.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (True,)
        assert main() == 0
        assert cursor.execute.call_args_list[0].args == (sql_file.read_text(),)
    assert "vector extension is available" in capsys.readouterr().out


@pytest.mark.parametrize(
    "result",
    [
        False,
        OSError("synthetic read failure"),
        ValueError(SYNTHETIC_URL),
        DatabaseCheckError(SYNTHETIC_URL),
    ],
)
def test_db_init_failure_is_sanitised(monkeypatch, tmp_path, capsys, result):
    sql_file = tmp_path / "synthetic-init.sql"
    sql_file.write_text("CREATE EXTENSION IF NOT EXISTS vector;\n")
    monkeypatch.setattr(sys, "argv", ["db", "--init-sql", str(sql_file)])
    operation = MagicMock(return_value=result)
    if isinstance(result, Exception):
        operation.side_effect = result
    with patch("rag_audit.db.execute_database_command", operation):
        assert main() == 1
    output = capsys.readouterr()
    assert "initialisation failed" in output.out
    assert "synthetic_secret_sentinel" not in output.out + output.err
