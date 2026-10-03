import asyncio
import uuid

from rag_audit.answering import ask
from rag_audit.evaluation.baseline import BaselineGenerator
from rag_audit.evaluation.metrics import assess
from rag_audit.evaluation_data import Case
from rag_audit.gate import Gate, lexical_coverage
from rag_audit.policy import serialize
from rag_audit.settings import Settings
from rag_audit.store import PostgresStore


class ObservedStore(PostgresStore):
    def snapshot(self, *args, **kwargs):
        self.observed = super().snapshot(*args, **kwargs)
        return self.observed


async def run_phrasing(
    connection, embedder, case: Case, style: str, question: str, gate: Gate | None
) -> dict:
    provider = BaselineGenerator()
    store = ObservedStore(connection)
    request_id = str(uuid.uuid4())
    response = await ask(
        store,
        case.subject,
        question,
        embedder,
        provider,
        Settings(),
        gate=gate,
        id_factory=lambda: request_id,
    )
    stored = connection.execute(
        "SELECT payload FROM demo_traces WHERE request_id=%s", (request_id,)
    ).fetchone()
    if not stored:
        raise ValueError("Persisted trace missing")
    trace = stored[0]
    chunks = store.observed.chunks
    assessment = assess(case, response, trace, chunks, provider.calls)
    attack_documents = {support.document_id for support in case.attack_support}
    attack_chunks = [
        chunk["id"]
        for chunk in chunks
        if chunk["document_id"] in attack_documents
        and any(
            phrase.casefold() in chunk["text"].casefold()
            for support in case.attack_support
            for phrase in support.key_facts
        )
    ]
    return dict(
        case=case.id,
        style=style,
        split=case.split,
        category=case.category,
        challenge_kind=case.challenge_kind,
        response=response,
        response_bytes=serialize(response),
        trace=trace,
        chunks=chunks,
        assessment=assessment,
        hard_failures=assessment["hard_failures"],
        lexical_coverage=[lexical_coverage(question, chunk) for chunk in chunks],
        attack_retrieved=bool(attack_chunks),
        attack_sent=bool(set(attack_chunks) & set(trace["sent_ids"])),
    )


def run_cases(connection, embedder, cases: list[Case], gate: Gate | None) -> list[dict]:
    rows = []
    for case in cases:
        for index, phrasing in enumerate(case.phrasings):
            row = asyncio.run(
                run_phrasing(
                    connection, embedder, case, phrasing.style, phrasing.text, gate
                )
            )
            if case.category == "unauthorised":
                hidden = case.challenge_kind == "free_text"
                if hidden:
                    connection.execute(
                        "CREATE TEMP TABLE removed_chunks AS SELECT * FROM demo_chunks "
                        "WHERE document_id=ANY(%s)",
                        (case.forbidden_documents,),
                    )
                    connection.execute(
                        "DELETE FROM demo_chunks WHERE document_id=ANY(%s)",
                        (case.forbidden_documents,),
                    )
                try:
                    question = phrasing.text if hidden else case.absent_phrasings[index]
                    paired = asyncio.run(
                        run_phrasing(
                            connection, embedder, case, phrasing.style, question, gate
                        )
                    )
                    if row["response_bytes"] != paired["response_bytes"]:
                        row["hard_failures"].append("counterfactual_bytes")
                    if hidden and (
                        row["chunks"] != paired["chunks"]
                        or row["lexical_coverage"] != paired["lexical_coverage"]
                    ):
                        row["hard_failures"].append("counterfactual_signals")
                    row["counterfactual"] = paired
                    row["hard_failures"].extend(
                        "paired:" + failure for failure in paired["hard_failures"]
                    )
                finally:
                    if hidden:
                        connection.execute(
                            "INSERT INTO demo_chunks SELECT * FROM removed_chunks"
                        )
                        connection.execute("DROP TABLE removed_chunks")
            rows.append(row)
    return rows
