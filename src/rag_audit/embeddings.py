import hashlib
import json
import re
from pathlib import Path
from typing import Protocol
from urllib.request import urlopen

MODEL = "BAAI/bge-small-en-v1.5"
REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
INSTRUCTION = "Represent this sentence for searching relevant passages: "
FILES = ("tokenizer.json", "onnx/model.onnx")


class Embedder(Protocol):
    identity: str

    def offsets(self, text: str) -> list[tuple[int, int]]: ...
    def encode(self, texts: list[str], *, query: bool = False) -> list[list[float]]: ...


class FakeEmbedder:
    identity = "synthetic-fake-v1"

    def offsets(self, text: str) -> list[tuple[int, int]]:
        return [(match.start(), match.end()) for match in re.finditer(r"\S+", text)]

    def encode(self, texts: list[str], *, query: bool = False) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * 384
            for word in re.findall(r"\w+", text.lower()):
                index = (
                    int.from_bytes(hashlib.sha256(word.encode()).digest()[:4], "big")
                    % 384
                )
                vector[index] += 1
            norm = sum(value * value for value in vector) ** 0.5
            if not norm:
                raise ValueError("Empty embedding input")
            vectors.append([value / norm for value in vector])
        return vectors


def download(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for filename in FILES:
        target = directory / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(
            f"https://huggingface.co/{MODEL}/resolve/{REVISION}/{filename}", timeout=180
        ) as response:
            data = response.read()
        target.write_bytes(data)
        hashes[filename] = hashlib.sha256(data).hexdigest()
    (directory / "identity.json").write_text(
        json.dumps({"model": MODEL, "revision": REVISION, "hashes": hashes})
    )


class OnnxEmbedder:
    identity = f"{MODEL}@{REVISION}:cls:l2:section-v1"

    def __init__(self, directory: Path):
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        metadata = json.loads((directory / "identity.json").read_text())
        if metadata["model"] != MODEL or metadata["revision"] != REVISION:
            raise ValueError("Model identity mismatch")
        for filename in FILES:
            if (
                hashlib.sha256((directory / filename).read_bytes()).hexdigest()
                != metadata["hashes"][filename]
            ):
                raise ValueError("Model integrity mismatch")
        self.np = np
        self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        self.tokenizer.no_truncation()
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(directory / "onnx/model.onnx"),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )

    def offsets(self, text: str) -> list[tuple[int, int]]:
        return [
            (start, end)
            for start, end in self.tokenizer.encode(
                text, add_special_tokens=False
            ).offsets
            if start != end
        ]

    def encode(self, texts: list[str], *, query: bool = False) -> list[list[float]]:
        result = []
        for start in range(0, len(texts), 8):
            inputs = [
                INSTRUCTION + text if query else text
                for text in texts[start : start + 8]
            ]
            encoded = self.tokenizer.encode_batch(inputs)
            if any(len(value.ids) > 512 for value in encoded):
                raise ValueError("Embedding input exceeds token limit")
            feeds = {
                "input_ids": self.np.array(
                    [value.ids for value in encoded], dtype="int64"
                ),
                "attention_mask": self.np.array(
                    [value.attention_mask for value in encoded], dtype="int64"
                ),
                "token_type_ids": self.np.array(
                    [value.type_ids for value in encoded], dtype="int64"
                ),
            }
            values = self.session.run(
                None,
                {item.name: feeds[item.name] for item in self.session.get_inputs()},
            )[0][:, 0, :]
            values /= self.np.linalg.norm(values, axis=1, keepdims=True)
            result.extend(values.tolist())
        return result
