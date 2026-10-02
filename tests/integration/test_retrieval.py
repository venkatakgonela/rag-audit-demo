import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psycopg
import pytest

from rag_audit.corpus import generate
from rag_audit.embeddings import FakeEmbedder
from rag_audit.ingestion import ingest
from rag_audit.retrieval import SQL, retrieve
from rag_audit.settings import Settings

pytestmark = pytest.mark.integration


@pytest.fixture
def database(tmp_path):
    settings = Settings()
    assert settings.database_url is not None
    with psycopg.connect(
        settings.database_url.get_secret_value(), autocommit=True
    ) as connection:
        connection.execute("CREATE SCHEMA retrieval_test")
        connection.execute("SET search_path TO retrieval_test,public")
        source = (
            Path(__file__).resolve().parents[2] / "docker/init/001-enable-vector.sql"
        )
        connection.execute(source.read_text())
        generate(tmp_path)
        ingest(connection, tmp_path, FakeEmbedder())
        try:
            yield connection, tmp_path
        finally:
            connection.execute("DROP SCHEMA retrieval_test CASCADE")


def expected_documents(subject):
    public = {
        f"synthetic-{kind}-{ordinal}"
        for kind in ("policy", "faq")
        for ordinal in range(6)
    }
    if "admin" in subject:
        return {
            f"synthetic-{kind}-{ordinal}"
            for kind in ("policy", "faq", "guide", "underwriting", "claim")
            for ordinal in range(6)
        }
    parity = 0 if subject.endswith("-a") else 1
    claims = {f"synthetic-claim-{ordinal}" for ordinal in range(parity, 6, 2)}
    if "customer" in subject:
        return public | claims
    if "broker" in subject:
        return public | claims | {f"synthetic-guide-{ordinal}" for ordinal in range(6)}
    return (
        public
        | claims
        | {f"synthetic-underwriting-{ordinal}" for ordinal in range(6)}
        | {f"synthetic-guide-{ordinal}" for ordinal in range(parity, 6, 2)}
    )


@pytest.mark.parametrize(
    "subject",
    [
        "synthetic-customer-a",
        "synthetic-customer-b",
        "synthetic-broker-a",
        "synthetic-broker-b",
        "synthetic-underwriter-a",
        "synthetic-underwriter-b",
        "synthetic-admin",
    ],
)
def test_exact_role_sets_and_no_leaks(database, subject):
    connection, _ = database
    params = {
        "model": FakeEmbedder.identity,
        "tiers": [],
        "teams": [],
        "subject": subject,
        "role": "customer",
    }
    from rag_audit.access import TIERS

    role, teams = connection.execute(
        "SELECT role,teams FROM demo_users WHERE subject=%s", (subject,)
    ).fetchone()
    params.update(tiers=list(TIERS[role]), teams=teams, role=role)
    predicate = (
        SQL.split("), signals")[0] + ") SELECT DISTINCT document_id FROM eligible"
    )
    actual = {row[0] for row in connection.execute(predicate, params).fetchall()}
    assert actual == expected_documents(subject)
    for query in (
        "water damage",
        "restricted sentinel",
        "synthetic-claim-1-canary",
        "synthetic-underwriting-5-canary",
    ):
        result = retrieve(connection, subject, query, FakeEmbedder(), top_k=20)
        assert {row["document_id"] for row in result["chunks"]} <= actual
        assert result["authorised_chunk_ids"] == [row["id"] for row in result["chunks"]]


def test_forbidden_content_cannot_change_results_or_signals(database):
    connection, _ = database
    before = retrieve(
        connection,
        "synthetic-customer-a",
        "secret water sentinel",
        FakeEmbedder(),
        top_k=20,
    )
    vector = str(FakeEmbedder().encode(["secret water sentinel"])[0])
    connection.execute(
        "UPDATE demo_chunks SET embedding=%s::vector,"
        "search=to_tsvector('english','secret water sentinel'),"
        "text='secret water sentinel' WHERE document_id='synthetic-claim-1'",
        (vector,),
    )
    after = retrieve(
        connection,
        "synthetic-customer-a",
        "secret water sentinel",
        FakeEmbedder(),
        top_k=20,
    )
    assert before == after
    assert all(
        "cosine_similarity" in row and "keyword_rank" in row for row in after["chunks"]
    )
    assert all(
        -1.00001 <= row["cosine_similarity"] <= 1.00001 for row in after["chunks"]
    )


def test_idempotence_offsets_atomic_failure_and_model_mismatch(database):
    connection, directory = database
    before = connection.execute(
        "SELECT id,text FROM demo_chunks ORDER BY id"
    ).fetchall()
    count = ingest(connection, directory, FakeEmbedder())
    assert count == len(before)
    assert (
        connection.execute("SELECT id,text FROM demo_chunks ORDER BY id").fetchall()
        == before
    )
    for text, start, end, source in connection.execute(
        "SELECT c.text,c.start_offset,c.end_offset,d.source "
        "FROM demo_chunks c JOIN demo_documents d ON d.id=c.document_id"
    ):
        assert source[start:end] == text
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest["documents"][0]["tier"] = None
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        ingest(connection, directory, FakeEmbedder())
    assert (
        connection.execute("SELECT id,text FROM demo_chunks ORDER BY id").fetchall()
        == before
    )
    embedder = FakeEmbedder()
    embedder.identity = "different-model"
    with pytest.raises(ValueError, match="mismatch"):
        retrieve(connection, "synthetic-customer-a", "query", embedder)


def test_section_path_and_rrf_raw_signals(database):
    connection, _ = database
    result = retrieve(
        connection, "synthetic-admin", "assessment", FakeEmbedder(), top_k=20
    )
    assert any(row["keyword_rank"] is not None for row in result["chunks"])
    for row in result["chunks"]:
        assert row["score"] > 0
        if row["keyword_rank"] is not None:
            assert row["score"] > 1 / (60 + row["keyword_rank"])


def test_section_only_term_is_indexed_and_affects_embedding(database):
    connection, directory = database
    manifest = json.loads((directory / "manifest.json").read_text())
    document = manifest["documents"][0]
    source = "# Synthetic zephyrunique\n\n" + "ordinary evidence " * 700
    (directory / document["path"]).write_text(source)
    document["sha256"] = hashlib.sha256(source.encode()).hexdigest()
    (directory / "manifest.json").write_text(json.dumps(manifest))
    ingest(connection, directory, FakeEmbedder())
    rows = connection.execute(
        "SELECT text,section,search @@ plainto_tsquery('english','zephyrunique'),"
        "embedding::text FROM demo_chunks WHERE document_id=%s ORDER BY ordinal",
        (document["id"],),
    ).fetchall()
    continuation = [row for row in rows if "zephyrunique" not in row[0]]
    assert continuation
    for text, section, matched, vector in continuation:
        assert matched
        expected = FakeEmbedder().encode([section + "\n" + text])[0]
        assert json.loads(vector) == pytest.approx(expected, abs=1e-6)
        assert expected != FakeEmbedder().encode([text])[0]


def test_rrf_matches_independent_reference_and_production_plan(database):
    connection, _ = database
    embedder = FakeEmbedder()
    query = "assessment"
    vector = embedder.encode([query], query=True)[0]
    signals = connection.execute(
        "SELECT id,1-(embedding <=> %s::vector),"
        "ts_rank_cd(search,websearch_to_tsquery('english',%s)),"
        "search @@ websearch_to_tsquery('english',%s) FROM demo_chunks",
        (str(vector), query, query),
    ).fetchall()
    vector_order = sorted(signals, key=lambda row: (-row[1], row[0]))[:50]
    keyword_order = sorted(
        [row for row in signals if row[3]], key=lambda row: (-row[2], row[0])
    )[:50]
    scores: dict[str, float] = {}
    for ranking in (vector_order, keyword_order):
        for rank, row in enumerate(ranking, 1):
            scores[row[0]] = scores.get(row[0], 0) + 1 / (60 + rank)
    expected = sorted(scores, key=lambda identifier: (-scores[identifier], identifier))[
        :20
    ]
    result = retrieve(connection, "synthetic-admin", query, embedder, top_k=20)
    assert result["authorised_chunk_ids"] == expected
    for row in result["chunks"]:
        assert row["score"] == pytest.approx(scores[row["id"]])
    params = {
        "model": embedder.identity,
        "tiers": ["public"],
        "teams": [],
        "subject": "synthetic-customer-a",
        "role": "customer",
        "query": query,
        "vector": str(vector),
        "top_k": 5,
        "candidates": 50,
    }
    plan = connection.execute(
        "EXPLAIN (ANALYZE, FORMAT JSON) " + SQL, params
    ).fetchone()[0]
    serialized = json.dumps(plan)
    assert '"CTE Name": "eligible"' in serialized
    assert '"CTE Name": "signals"' in serialized
    assert "hnsw" not in serialized.lower()


def test_database_write_failure_rolls_back_snapshot(database):
    connection, directory = database
    before = connection.execute(
        "SELECT id,text FROM demo_chunks ORDER BY id"
    ).fetchall()
    connection.execute(
        "CREATE FUNCTION reject_document() RETURNS trigger LANGUAGE plpgsql AS "
        "$$ BEGIN RAISE EXCEPTION 'synthetic forced failure'; END $$"
    )
    connection.execute(
        "CREATE TRIGGER reject_document BEFORE INSERT ON demo_documents "
        "FOR EACH ROW EXECUTE FUNCTION reject_document()"
    )
    with pytest.raises(psycopg.Error):
        ingest(connection, directory, FakeEmbedder())
    assert (
        connection.execute("SELECT id,text FROM demo_chunks ORDER BY id").fetchall()
        == before
    )


def test_errors_are_redacted(database):
    connection, _ = database
    connection.execute("ALTER TABLE demo_chunks RENAME COLUMN search TO unavailable")
    with pytest.raises(ValueError) as captured:
        retrieve(connection, "synthetic-customer-a", "private sentinel", FakeEmbedder())
    assert str(captured.value) == "Retrieval operation failed"


def test_concurrent_ingestion_and_acl_replacement(database):
    connection, directory = database
    second = directory / "second"
    generate(second, seed=43)
    settings = Settings()
    assert settings.database_url is not None
    address = settings.database_url.get_secret_value()

    def write_snapshot(path):
        with psycopg.connect(address, autocommit=True) as writer:
            writer.execute("SET search_path TO retrieval_test,public")
            return ingest(writer, path, FakeEmbedder())

    with ThreadPoolExecutor(max_workers=2) as workers:
        counts = list(workers.map(write_snapshot, (directory, second)))
    versions = connection.execute(
        "SELECT DISTINCT corpus_version FROM demo_chunks"
    ).fetchall()
    assert len(versions) == 1
    assert (
        connection.execute("SELECT count(*) FROM demo_chunks").fetchone()[0] in counts
    )
    manifest = json.loads((second / "manifest.json").read_text())
    document = manifest["documents"][0]
    document["tier"] = "restricted"
    (second / "manifest.json").write_text(json.dumps(manifest))
    ingest(connection, second, FakeEmbedder())
    result = retrieve(
        connection, "synthetic-customer-a", "water damage", FakeEmbedder(), top_k=20
    )
    assert document["id"] not in {row["document_id"] for row in result["chunks"]}
    assert connection.execute(
        "SELECT DISTINCT tier FROM demo_chunks WHERE document_id=%s",
        (document["id"],),
    ).fetchall() == [("restricted",)]


def test_exact_plan_and_approximate_underfill(database):
    connection, _ = database
    connection.execute(
        "CREATE TABLE ann_probe (id integer, allowed boolean, embedding vector(3))"
    )
    connection.execute(
        "INSERT INTO ann_probe SELECT number, number > 900, "
        "ARRAY[1.0,number/1000.0,0.1]::vector "
        "FROM generate_series(1,1000) number"
    )
    connection.execute(
        "CREATE INDEX ON ann_probe USING hnsw (embedding vector_cosine_ops)"
    )
    connection.execute("ANALYZE ann_probe")
    connection.execute("SET enable_seqscan=off")
    connection.execute("SET hnsw.ef_search=10")
    connection.execute("SET hnsw.iterative_scan=off")
    approximate = connection.execute(
        "SELECT id FROM ann_probe WHERE allowed "
        "ORDER BY embedding <=> '[1,0,0.1]'::vector LIMIT 5"
    ).fetchall()
    exact = connection.execute(
        "WITH eligible AS MATERIALIZED (SELECT * FROM ann_probe WHERE allowed) "
        "SELECT id FROM eligible ORDER BY embedding <=> '[1,0,0.1]'::vector LIMIT 5"
    ).fetchall()
    plan = connection.execute(
        "EXPLAIN (FORMAT JSON) SELECT id FROM ann_probe WHERE allowed "
        "ORDER BY embedding <=> '[1,0,0.1]'::vector LIMIT 5"
    ).fetchone()[0]
    assert "Index Scan" in json.dumps(plan)
    assert len(exact) == 5
    assert len(approximate) < len(exact)
    connection.execute("RESET enable_seqscan")
    assert "eligible AS MATERIALIZED" in SQL
