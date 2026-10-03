import hashlib
import math
from pathlib import Path
from typing import Protocol

REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
MODEL_SHA256 = "5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a"
TOKENIZER_SHA256 = "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66"


class Reranker(Protocol):
    identity: str

    def score(self, question: str, chunk: dict) -> float | None: ...


def probability(logit: float) -> float:
    if not math.isfinite(logit):
        raise ValueError("Nonfinite reranker output")
    if logit >= 0:
        return 1 / (1 + math.exp(-logit))
    exponent = math.exp(logit)
    return exponent / (1 + exponent)


class OnnxReranker:
    identity = f"ms-marco-MiniLM-L6-v2@{REVISION}:onnx-f32:sigmoid:pair-v1"

    def __init__(self, directory: Path):
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        model = directory / "onnx/model.onnx"
        tokenizer_path = directory / "tokenizer.json"
        content = tokenizer_path.read_bytes()
        if (
            model.stat().st_size != 91011230
            or len(content) != 711396
            or hashlib.sha256(model.read_bytes()).hexdigest() != MODEL_SHA256
            or hashlib.sha256(content).hexdigest() != TOKENIZER_SHA256
        ):
            raise ValueError("Reranker artifact integrity mismatch")
        self.np = np
        self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(model), sess_options=options, providers=["CPUExecutionProvider"]
        )
        inputs = self.session.get_inputs()
        if (
            {item.name for item in inputs}
            != {"input_ids", "attention_mask", "token_type_ids"}
            or any(item.type != "tensor(int64)" for item in inputs)
            or len(self.session.get_outputs()) != 1
        ):
            raise ValueError("Unexpected reranker graph contract")

    def score(self, question: str, chunk: dict) -> float | None:
        encoded = self.tokenizer.encode(
            question, chunk["section"] + "\n" + chunk["text"]
        )
        if len(encoded.ids) > 512:
            return None
        feeds = {
            name: self.np.array([values], dtype="int64")
            for name, values in (
                ("input_ids", encoded.ids),
                ("attention_mask", encoded.attention_mask),
                ("token_type_ids", encoded.type_ids),
            )
        }
        result = self.session.run(None, feeds)[0]
        if result.shape != (1, 1):
            raise ValueError("Unexpected reranker output shape")
        return probability(float(result[0, 0]))


def rerank(question: str, chunks: list[dict], model: Reranker) -> list[dict]:
    if len(chunks) > 20:
        raise ValueError("Reranking accepts at most twenty eligible candidates")
    scored = []
    for chunk in chunks:
        score = model.score(question, chunk)
        if score is not None and (not math.isfinite(score) or not 0 <= score <= 1):
            raise ValueError("Invalid relevance probability")
        scored.append({**chunk, "reranker_score": score})
    return sorted(
        scored,
        key=lambda chunk: (
            -(chunk["reranker_score"] if chunk["reranker_score"] is not None else -1),
            chunk["id"],
        ),
    )
