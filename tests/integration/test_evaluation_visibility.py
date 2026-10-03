from pathlib import Path

import pytest
from test_answer_database import answer
from test_answer_database import database as database

from rag_audit.access import ACL_SQL, access_parameters, load_identity
from rag_audit.embeddings import FakeEmbedder
from rag_audit.evaluation_data import Case, read_cases, read_json
from rag_audit.generation import FakeGenerator
from rag_audit.policy import serialize
from rag_audit.retrieval import retrieve
from rag_audit.routing import route
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


def test_free_text_hidden_content_noninterference(database):
    connection, _ = database
    cases = read_cases(ROOT / "datasets/evaluation")["cases"]
    for data in cases:
        if data["challenge_kind"] != "free_text":
            continue
        case = Case.model_validate(data)
        for phrasing in case.phrasings:
            assert route(phrasing.text).valid and not route(phrasing.text).entities
            before = retrieve(connection, case.subject, phrasing.text, FakeEmbedder())
            response = answer(connection, case.subject, phrasing.text, FakeGenerator())
            assert not any(
                fact.casefold() in serialize(response).casefold()
                for fact in case.must_not_appear
            )
            connection.execute(
                "CREATE TEMP TABLE hidden_source AS SELECT * FROM demo_chunks "
                "WHERE document_id = ANY(%s)",
                (case.forbidden_documents,),
            )
            try:
                connection.execute(
                    "DELETE FROM demo_chunks WHERE document_id = ANY(%s)",
                    (case.forbidden_documents,),
                )
                after = retrieve(
                    connection, case.subject, phrasing.text, FakeEmbedder()
                )
                absent = answer(
                    connection, case.subject, phrasing.text, FakeGenerator()
                )
                assert before == after
                assert serialize(response) == serialize(absent)
            finally:
                connection.execute(
                    "INSERT INTO demo_chunks SELECT * FROM hidden_source"
                )
                connection.execute("DROP TABLE hidden_source")
