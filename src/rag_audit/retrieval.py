import math

import psycopg
from psycopg.rows import dict_row

from rag_audit.access import ACL_SQL, access_parameters, load_identity
from rag_audit.embeddings import Embedder

SQL = (
    """
WITH eligible AS MATERIALIZED (
 SELECT c.* FROM demo_chunks c JOIN demo_documents d ON d.id=c.document_id
 WHERE c.model_identity=%(model)s AND """
    + ACL_SQL
    + """
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
)


def retrieve(
    connection: psycopg.Connection,
    subject: str,
    query: str,
    embedder: Embedder,
    top_k: int = 5,
    candidates: int = 50,
    *,
    document_ids: tuple[str, ...] | None = None,
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
            identity = load_identity(connection, subject)
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
                **access_parameters(identity),
                "query": query,
                "vector": str(vector),
                "top_k": top_k,
                "candidates": candidates,
            }
            with connection.cursor(row_factory=dict_row) as cursor:
                query_sql = SQL
                if document_ids is not None:
                    query_sql = SQL.replace(
                        "WHERE c.model_identity=",
                        "WHERE d.id = ANY(%(documents)s) AND c.model_identity=",
                    )
                    parameters["documents"] = list(document_ids)
                rows = cursor.execute(query_sql, parameters).fetchall()
            for result in rows:
                result["score"] = float(result["score"])
            return {"chunks": rows, "authorised_chunk_ids": [row["id"] for row in rows]}
    except psycopg.Error:
        raise ValueError("Retrieval operation failed") from None
