# wiki-cocoindex-template

Wiki CLI template for CocoIndex-backed incremental memory sidecars.

Wiki stays the source of truth. CocoIndex materializes derived indexes for agent memory, RAG, hybrid retrieval, and graph-style lookup.

## Quick start

1. Click **Use this template** on GitHub or clone the repo.
2. Install the Wiki tooling and local index dependencies:

```bash
pip install -r requirements.txt
```

3. Validate the wiki corpus:

```bash
wiki -c wiki.yml fmt --check
wiki -c wiki.yml lint --strict
wiki -c wiki.yml check --strict
```

4. Start Postgres with pgvector:

```bash
docker compose up -d
```

5. Build the deterministic manifest and load the derived index:

```bash
python scripts/build_manifest.py
python scripts/load_index.py
```

6. Query the derived index:

```bash
python scripts/query_index.py "fresh context for agents"
```

7. Optional: install CocoIndex to experiment with `sidecar/flow.py`:

```bash
pip install cocoindex
```

## What lives where

- `wiki.yml` - Wiki CLI config and RDF prefixes
- `wiki/` - validated Markdown source corpus
- `sidecar/` - manifesting, provenance, retrieval, and CocoIndex example flow
- `scripts/` - build, load, query, and demo commands
- `docker-compose.yml` - local Postgres + pgvector
- `.github/workflows/` - CI and GitHub Pages deploy

## Commands

| Command | Purpose |
| --- | --- |
| `wiki -c wiki.yml fmt --check` | Mechanical markdown formatting check |
| `wiki -c wiki.yml lint --strict` | Broken links, filename pattern, heading conventions |
| `wiki -c wiki.yml check --strict` | SHACL, JSON Schema, route, and layout integrity |
| `python scripts/build_manifest.py` | Export deterministic page/chunk/link manifests |
| `python scripts/load_index.py` | Upsert chunk records into Postgres/pgvector |
| `python scripts/query_index.py` | Search the derived index and print citations |
| `python scripts/demo_incremental_update.py` | Show what changes when a Wiki page changes |

## Architecture

```text
Wiki Markdown + wiki.yml
  -> wiki fmt / lint / check
  -> deterministic manifest build
  -> derived sidecar index
  -> Postgres + pgvector
  -> cited retrieval results
```

## Trust boundaries

- Wiki pages are authoritative.
- CocoIndex outputs are derived and rebuildable.
- Every record carries page path, heading, fragment, and content hash.
- Generated claims stay outside the source corpus until reviewed.

## Deployment

This template publishes the wiki site with GitHub Pages.

1. Enable **Settings -> Pages -> Source: GitHub Actions**.
2. Push to `main`.
3. The deploy workflow publishes the built site.

## Why not just use SPARQL or plain RAG?

- Wiki-only SPARQL is best when the answer already lives in the graph.
- Plain vector RAG is not enough when provenance and freshness matter.
- CocoIndex sits in the middle: incremental, derived, and easy to rebuild.
