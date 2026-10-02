# 0016: Pinned local ONNX embeddings

Status: Accepted

## Context

The local English embedding model must work on CPU without a Linux CUDA dependency tree. Model: BAAI/bge-small-en-v1.5, revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, MIT-declared publisher artifacts, 384 dimensions. The ONNX export and tokenizer are from that immutable revision.

## Decision drivers

Cross-platform installed footprint, equivalent rankings, exact tokenizer offsets and a small optional dependency graph.

## Options considered

Measured October 2, 2026, on Apple M4 Pro/24 GiB and Linux x86_64 emulation under Docker on the same host. Two threads, batches of eight, 10 passages plus 10 queries, and 100 short passages for throughput. Environments include baseline/dev packages and exclude model files. Cold figures include imports and are first-process loads, not flushed disk-cache measurements. Linux emulation timings are not native deployment benchmarks.

| Runtime | Added locked packages | macOS allocated KiB | Linux allocated KiB | macOS / Linux median query ms | macOS / Linux passages/s |
| --- | --- | --- | --- | --- | --- |
| Sentence Transformers 5.1.1 + CPU PyTorch 2.14.1 | 29 lock records | 1,014,888 | 1,221,224 | 6.49 / 20.71 | 545.8 / 71.2 |
| ONNX Runtime 1.30.0 + tokenizers 0.23.2 + NumPy 2.5.3 | 10 | 253,700 | 275,328 | 3.23 / 11.08 | 527.2 / 82.9 |
| FastEmbed 0.8.1, custom local pinned export | 19 | 271,364 | 298,824 | 3.00 / 11.29 | 564.0 / 82.4 |

All three resolved/installed on both platforms, had no NVIDIA/Triton lock entries, preserved baseline package versions and passed 384-dimensional L2/Unicode-offset smoke tests. Both ONNX routes had minimum/mean cosine agreement greater than 0.999999999999 with the reference on each platform and identical complete retrieval orders for the fixed query set. This is an equivalence smoke test, not broad quality evaluation.

PyTorch used an explicit Linux-only official CPU index; macOS and all other packages used PyPI. Its default PyPI Linux resolution was rejected earlier for roughly 3 GB of GPU-wheel artifacts. FastEmbed's built-in model alias points at a different quantised repository; the comparison instead registered a custom CLS model with `specific_model_path`, using the original pinned publisher export, offline. It is viable but adds dependencies and still needs custom artifact management.

Hosted APIs were excluded without benchmarks because this stage requires local, key-free inference. A separate model server adds a service. Changing the model does not address runtime packaging.

## Decision

Choose direct ONNX Runtime, tokenizers and NumPy as pinned optional dependencies. It has the smallest measured environment and graph, with short explicit CLS pooling/normalisation code. Execute only a downloaded ONNX graph and tokenizer, not remote Python model code. Prefix retrieval queries with the publisher's instruction; passages get section path and source text only. Verify artifact identity/local hashes and reject overlong inputs rather than truncate. No automatic fallback to fake vectors.

## Consequences

We own batching, CLS selection and normalisation; tests and equivalence evidence must protect them. Default CI never downloads or executes real embeddings. Future retrieval evaluation must add real-model CI coverage with an explicit cache strategy. The model cache is separate from the optional environment. Pinned runtime versions are not a claim of perpetual security or latest release.

Direct-dependency licence evidence: ONNX Runtime MIT; tokenizers Apache-2.0; NumPy BSD-3-Clause with additional bundled licence notices. Published release dates observed: ONNX Runtime 1.30.0 September 10, 2026; tokenizers 0.23.2 September 3, 2026; NumPy 2.5.3 September 6, 2026. FastEmbed 0.8.1 was released September 22, 2026 (Apache-2.0); Sentence Transformers 5.1.1 September 22, 2025 (Apache-2.0), while its observed latest release was 6.1.0 September 18, 2026. These dates indicate publication activity, not maintenance guarantees.

## Revisit when

Model changes, ONNX equivalence fails, dependency support changes, or native Linux performance becomes a requirement.

## Sources

[Publisher model](https://huggingface.co/BAAI/bge-small-en-v1.5/tree/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a), [ONNX licence](https://github.com/microsoft/onnxruntime/blob/v1.30.0/LICENSE), [tokenizers licence](https://github.com/huggingface/tokenizers/blob/v0.23.2/LICENSE), [NumPy metadata](https://pypi.org/pypi/numpy/2.5.3/json), [uv CPU sources](https://docs.astral.sh/uv/guides/integration/pytorch/), [FastEmbed custom model API](https://github.com/qdrant/fastembed/blob/v0.8.1/fastembed/text/text_embedding.py), [adapter](../../src/rag_audit/embeddings.py), [smoke tests](../../tests/test_embedding_adapter.py).
