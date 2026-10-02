import argparse
import json
from pathlib import Path

import psycopg

from rag_audit.corpus import generate
from rag_audit.embeddings import FakeEmbedder, OnnxEmbedder, download
from rag_audit.ingestion import ingest
from rag_audit.retrieval import retrieve
from rag_audit.settings import Settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic retrieval demonstration")
    parser.add_argument(
        "command", choices=["generate", "download-model", "ingest", "query"]
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
                settings.database_url.get_secret_value()
            ) as connection:
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
