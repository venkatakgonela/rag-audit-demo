import math

import psycopg
from psycopg.rows import dict_row

from rag_audit.access import TIERS, Identity
from rag_audit.embeddings import Embedder

SQL = """
WITH eligible AS MATERIALIZED (
 SELECT c.* FROM demo_chunks c JOIN demo_documents d ON d.id=c.document_id
 WHERE c.model_identity=%(model)s AND (
 d.tier = ANY(%(tiers)s) OR d.team = ANY(%(teams)s)
 OR (d.kind='claim' AND d.owner=%(subject)s)
 OR (d.kind='claim' AND %(role)s='broker' AND EXISTS (
 SELECT 1 FROM demo_brokers b WHERE b.broker=%(subject)s AND b.customer=d.owner)))
), signals AS MATERIALIZED (
 SELECT *, 1-(embedding <=> %(vector)s::vector) AS cosine_similarity,
 ts_rank_cd(search,websearch_to_tsquery('english',%(query)s)) AS keyword_score,
 search @@ websearch_to_tsquery('english',%(query)s) AS keyword_match
 FROM eligible
), vectors AS (
 SELECT id,row_number() OVER (ORDER BY cosine_similarity DESC,id) AS rank
 FROM signals ORDER BY cosine_similarity DESC,id LIMIT %(candidates)s
), keywords AS (
 SELECT id,row_number() OVER (ORDER BY keyword_score DESC,id) AS rank
 FROM signals WHERE keyword_match ORDER BY keyword_score DESC,id LIMIT %(candidates)s
), fused AS (
 SELECT coalesce(v.id,k.id) AS id,
 coalesce(1.0/(60+v.rank),0)+coalesce(1.0/(60+k.rank),0) AS score,
 k.rank AS keyword_rank FROM vectors v FULL JOIN keywords k ON v.id=k.id
)
SELECT s.id,s.document_id,s.text,s.section,s.start_offset,s.end_offset,
 f.score,s.cosine_similarity,f.keyword_rank,s.keyword_score
FROM fused f JOIN signals s ON s.id=f.id ORDER BY f.score DESC,f.id LIMIT %(top_k)s
"""


def retrieve(
    connection: psycopg.Connection,
    subject: str,
    query: str,
    embedder: Embedder,
    top_k: int = 5,
    candidates: int = 50,
) -> dict:
    if (
        not query.strip()
        or len(query) > 4000
        or not 1 <= top_k <= 20
        or not top_k <= candidates <= 200
    ):
        raise ValueError("Invalid retrieval request")
    try:
        with connection.transaction():
            connection.execute("SELECT pg_advisory_xact_lock_shared(482031)")
            row = connection.execute(
                "SELECT subject,role,teams FROM demo_users WHERE subject=%s", (subject,)
            ).fetchone()
            if row is None:
                raise ValueError("Unknown fixture identity")
            identity = Identity(row[0], row[1], tuple(row[2]))
            config = connection.execute(
                "SELECT model_identity FROM demo_configuration WHERE singleton"
            ).fetchone()
            if config is None or config[0] != embedder.identity:
                raise ValueError("Embedding model mismatch; ingest again")
            vector = embedder.encode([query], query=True)[0]
            if (
                len(vector) != 384
                or not all(math.isfinite(value) for value in vector)
                or not any(vector)
            ):
                raise ValueError("Invalid query vector")
            parameters = {
                "model": embedder.identity,
                "tiers": list(TIERS[identity.role]),
                "teams": list(identity.teams),
                "subject": identity.subject,
                "role": identity.role,
                "query": query,
                "vector": str(vector),
                "top_k": top_k,
                "candidates": candidates,
            }
            with connection.cursor(row_factory=dict_row) as cursor:
                rows = cursor.execute(SQL, parameters).fetchall()
            for result in rows:
                result["score"] = float(result["score"])
            return {"chunks": rows, "authorised_chunk_ids": [row["id"] for row in rows]}
    except psycopg.Error:
        raise ValueError("Retrieval operation failed") from None
