# Optional reranker model notice

The experimental CPU reranker uses `cross-encoder/ms-marco-MiniLM-L6-v2`, published by the cross-encoder / Sentence Transformers project, revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`. The retained publisher model card declares Apache-2.0. The publisher repository has no standalone licence file at that revision; the standard Apache licence text is retained alongside the card in the ignored local cache. No model weights are committed or redistributed here. This notice does not select a licence for this repository.

Downloaded artifacts: the unmodified publisher `onnx/model.onnx`, `tokenizer.json`, `config.json`, `tokenizer_config.json`, `special_tokens_map.json`, `README.md`, plus `LICENSE-2.0.txt` from Apache. Total 91,739,913 bytes including the licence. No other weights, conversions or packages were obtained for this trial.

- Model SHA-256: `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`.
- Tokenizer SHA-256: `d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66`.
- Runtime: ONNX Runtime 1.30.0 (MIT), tokenizers 0.23.2 (Apache-2.0), NumPy 2.5.3 (BSD-3-Clause), already present as optional embedding dependencies.

The single output logit is transformed with a stable sigmoid. It is a relevance score, not a calibrated probability that the passage answers the question. Pair input is question plus section/newline/text; inputs above 512 tokens are unscorable, not truncated. See the [implementation](../src/rag_audit/reranking.py).

## Sources retained for provenance

- [Pinned publisher card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2/blob/233902d25c440f23af6f7d6e94d2946bac0bee0a/README.md).
- [Standard Apache licence text](https://www.apache.org/licenses/LICENSE-2.0.txt).
- [Publisher CrossEncoder usage](https://www.sbert.net/docs/cross_encoder/usage/usage.html).
