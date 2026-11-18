# Evolve LLM chunk manifests

SHA-256 hashes of every 256 KiB chunk of open-weight GGUF models, so browsers running
[Evolve LLM](https://github.com/anthony-firn/evolve-llm) can check model pieces they receive
from each other. With peer-to-peer sharing on, a visitor's browser fetches the pieces it needs
from other visitors who already have them, and from Hugging Face for the rest; each piece from a
peer is checked against these hashes before use, and a peer that sends a wrong piece is dropped.

## Format

Files are named by the SHA-256 of the whole file, which Hugging Face lists as the LFS `oid` of
every GGUF file, so the same file in any repository shares one manifest.

```
v1/<file sha256>/index.json   format, sha256, size, chunk (262144), page_chunks (4096),
                              pages: [SHA-256 of each page], source: {repo, file, revision}
v1/<file sha256>/<n>.bin      page n: the 32-byte SHA-256 of chunks n*4096 .. n*4096+4095
```

Each page covers 1 GiB of the model. A browser reads `index.json` from this repository over
TLS, checks each page it fetches against the index, and each chunk against its page.

## How the manifests are made

**Actions → Build chunk manifests → Run workflow**, with one `owner/repo path/to/file.gguf` per
line (any part of a split model stands for every part). The workflow pins each file to the
repository's current commit, streams it from Hugging Face on GitHub's runners (nothing but the
hashes is stored), requires the whole file to hash to the SHA-256 Hugging Face lists, and
commits the result. `tools/chunk_manifest.py` (from evolve-llm) does the hashing and runs
anywhere with Python 3:

```sh
python3 tools/chunk_manifest.py model.gguf --out . --sha256 <expected>
```

The hashes say what the bytes of a published file are; they say nothing about the model itself.
Each model keeps its own license.
