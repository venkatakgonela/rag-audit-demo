import uuid
from contextlib import contextmanager
from pathlib import Path

import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import Response

from rag_audit import __version__
from rag_audit.answering import ask, new_trace
from rag_audit.auth import verify_token
from rag_audit.embeddings import FakeEmbedder, OnnxEmbedder
from rag_audit.policy import envelope, serialize, strict_json
from rag_audit.provider_config import configured_provider
from rag_audit.settings import Settings
from rag_audit.store import PostgresStore

app = FastAPI(title="Synthetic RAG audit demo", version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@contextmanager
def store_context(settings: Settings):
    if settings.database_url is None:
        raise ValueError("Database configuration required")
    with psycopg.connect(
        settings.database_url.get_secret_value(),
        autocommit=True,
        connect_timeout=settings.database_connect_timeout,
    ) as connection:
        yield PostgresStore(connection)


def error_response(status: int) -> Response:
    return Response(
        serialize(envelope("error")), status_code=status, media_type="application/json"
    )


@app.post("/ask")
async def ask_endpoint(request: Request) -> Response:
    try:
        settings = Settings()
        with store_context(settings) as store:
            status, reason = 401, "authentication_failed"
            try:
                if settings.stub_signing_key is None:
                    status, reason = 503, "configuration_error"
                    raise ValueError("Missing signing key")
                key = settings.stub_signing_key.get_secret_value()
                if len(key.encode()) < 32:
                    status, reason = 503, "configuration_error"
                    raise ValueError("Invalid signing key")
                authorization = request.headers.get("authorization", "")
                if not authorization.startswith("Bearer "):
                    raise ValueError("Missing token")
                subject = verify_token(authorization[7:], key)
                status, reason = 400, "request_invalid"
                body = bytearray()
                async for part in request.stream():
                    if len(body) + len(part) > settings.http_body_bytes:
                        status = 413
                        raise ValueError("Body limit")
                    body.extend(part)
                data = strict_json(body.decode("utf-8"))
                if (
                    type(data) is not dict
                    or set(data) != {"question"}
                    or type(data["question"]) is not str
                    or not data["question"].strip()
                    or len(data["question"]) > settings.question_characters
                ):
                    raise ValueError("Invalid body")
            except Exception:
                trace = new_trace()
                trace["reason"] = reason
                store.trace(str(uuid.uuid4()), trace)
                return error_response(status)
            try:
                provider, prices = configured_provider(settings)
                embedder = (
                    OnnxEmbedder(Path("data/model"))
                    if settings.generation_backend == "responses"
                    else FakeEmbedder()
                )
            except Exception:
                trace = new_trace()
                trace["reason"] = "configuration_error"
                store.trace(str(uuid.uuid4()), trace)
                return error_response(503)
            response = await ask(
                store,
                subject,
                data["question"],
                embedder,
                provider,
                settings=settings,
                prices=prices,
            )
            return Response(
                serialize(response),
                media_type="application/json",
                status_code=503 if response["decision"] == "error" else 200,
            )
    except Exception:
        return error_response(503)
