import argparse
import asyncio
import json
from pathlib import Path

import psycopg

from rag_audit.answering import ask
from rag_audit.auth import issue_token
from rag_audit.corpus import generate
from rag_audit.embeddings import FakeEmbedder, OnnxEmbedder, download
from rag_audit.ingestion import ingest
from rag_audit.policy import serialize
from rag_audit.provider_config import configured_provider
from rag_audit.retrieval import retrieve
from rag_audit.settings import Settings
from rag_audit.store import PostgresStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic retrieval demonstration")
    parser.add_argument(
        "command",
        choices=["generate", "download-model", "ingest", "query", "ask", "stub-token"],
    )
    parser.add_argument("--corpus", type=Path, default=Path("data/corpus"))
    parser.add_argument("--model", type=Path, default=Path("data/model"))
    parser.add_argument("--fake", action="store_true")
    parser.add_argument("--subject", default="synthetic-customer-a")
    parser.add_argument("--query", default="water damage evidence")
    arguments = parser.parse_args()
    try:
        if arguments.command == "generate":
            print(
                json.dumps(
                    {
                        "synthetic_documents": len(
                            generate(arguments.corpus)["documents"]
                        )
                    }
                )
            )
        elif arguments.command == "stub-token":
            settings = Settings()
            if settings.stub_signing_key is None:
                raise ValueError("Signing key required")
            print(
                issue_token(
                    arguments.subject, settings.stub_signing_key.get_secret_value()
                )
            )
        elif arguments.command == "download-model":
            download(arguments.model)
        else:
            embedder = (
                FakeEmbedder() if arguments.fake else OnnxEmbedder(arguments.model)
            )
            settings = Settings()
            if settings.database_url is None:
                raise ValueError("Database configuration required")
            with psycopg.connect(
                settings.database_url.get_secret_value(), autocommit=True
            ) as connection:
                if arguments.command == "ask":
                    provider, prices = configured_provider(settings)
                    response = asyncio.run(
                        ask(
                            PostgresStore(connection),
                            arguments.subject,
                            arguments.query,
                            embedder,
                            provider,
                            settings=settings,
                            prices=prices,
                        )
                    )
                    print(serialize(response))
                    return 1 if response["decision"] == "error" else 0
                result = (
                    {"ingested": ingest(connection, arguments.corpus, embedder)}
                    if arguments.command == "ingest"
                    else retrieve(
                        connection, arguments.subject, arguments.query, embedder
                    )
                )
                print(json.dumps(result))
        return 0
    except (ValueError, OSError, KeyError, psycopg.Error):
        print(
            "Operation failed; check synthetic input, model and database configuration."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
