from pathlib import Path

import pytest
from test_answer_database import database as database

from rag_audit.access import ACL_SQL, access_parameters, load_identity
from rag_audit.evaluation_data import read_json
from rag_audit.structured import visible_record

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]


def test_authored_intent_matches_all_document_subject_pairs(database):
    connection, _ = database
    intent = read_json(ROOT / "datasets/evaluation/access-intent.json")
    expected = {
        item["document_id"]: set(item["allowed_subjects"])
        for item in intent["documents"]
    }
    for subject in intent["subjects"]:
        identity = load_identity(connection, subject)
        actual = {
            row[0]
            for row in connection.execute(
                "SELECT d.id FROM demo_documents d WHERE " + ACL_SQL,
                access_parameters(identity),
            ).fetchall()
        }
        assert actual == {
            identifier for identifier, allowed in expected.items() if subject in allowed
        }
        for identifier, allowed in expected.items():
            if identifier.startswith(("synthetic-claim-", "synthetic-policy-")):
                assert (
                    visible_record(connection, identity, identifier) is not None
                ) == (subject in allowed)
