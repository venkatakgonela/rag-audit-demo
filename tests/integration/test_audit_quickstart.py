import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

from rag_audit.corpus import generate
from rag_audit.settings import Settings

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.integration


def test_readme_fake_quickstart_answer_refusal_and_rule(tmp_path):
    settings = Settings()
    assert settings.database_url is not None
    url = settings.database_url.get_secret_value()
    commands = re.findall(
        r"^make ask ARGS='([^']+)'$", (ROOT / "README.md").read_text(), re.M
    )
    assert len(commands) == 3
    environment = {
        "PATH": os.environ["PATH"],
        "DATABASE_URL": url,
        "GENERATION_BACKEND": "fake",
        "PGOPTIONS": "-c search_path=audit_quickstart_test,public",
    }
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute("CREATE SCHEMA audit_quickstart_test")
        try:
            connection.execute("SET search_path TO audit_quickstart_test,public")
            connection.execute((ROOT / "docker/init/001-enable-vector.sql").read_text())
            generate(tmp_path / "data/corpus")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "rag_audit.cli",
                    "ingest",
                    "--fake",
                    "--corpus",
                    str(tmp_path / "data/corpus"),
                ],
                cwd=tmp_path,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            responses = []
            for command in commands:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "rag_audit.cli",
                        "ask",
                        *shlex.split(command),
                    ],
                    cwd=tmp_path,
                    env=environment,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                responses.append(json.loads(result.stdout))
            assert responses[0]["decision"] == "answered"
            assert (
                "The drying diary must show a reading every 24 hours."
                in responses[0]["text"]
            )
            assert responses[1]["decision"] == "no_answer"
            assert (
                responses[1]["text"] == "I cannot answer from the available evidence."
            )
            assert responses[2]["decision"] == "answered"
            assert responses[2]["text"] == (
                "Payout in GBP: 400.00 (calculation only; claim status: pending)."
            )
        finally:
            connection.execute("DROP SCHEMA audit_quickstart_test CASCADE")
