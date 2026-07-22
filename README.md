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

4. Build the deterministic manifest:

```bash
python scripts/build_manifest.py
```

5. Load the derived index and query it. The scripts automatically detect whether Docker Postgres is available, and fall back to PGlite (in-memory or file-persisted) if not.

```bash
python scripts/load_index.py
python scripts/query_index.py "fresh context for agents"
```

### Docker Postgres path (production-like)

For a real Postgres + pgvector instance:

```bash
docker compose up -d --build
python scripts/load_index.py
python scripts/query_index.py "fresh context for agents"
```

### PGlite path (zero-Docker)

For a zero-setup local demo, install the PGlite extra:

```bash
pip install -r requirements-pglite.txt
python scripts/load_index.py
python scripts/query_index.py "fresh context for agents"
```

PGlite uses a WASM Postgres build with pgvector support — no Docker daemon required.

### CocoIndex incremental flow

`sidecar/flow.py` is a CocoIndex app that uses `@coco.fn(memo=True)` alongside the
Wiki Python API (`wiki.parser.split_frontmatter_body`) to keep the pgvector index
incrementally in sync with the wiki corpus. When a page changes, only the affected
chunks re-process.

```bash
pip install -r requirements.txt
pip install -r requirements-cocoindex.txt
python scripts/run_flow.py
```

Requires a Postgres + pgvector instance (`docker compose up -d --build`).

## What lives where

- `wiki.yml` - Wiki CLI config and RDF prefixes
- `wiki/` - validated Markdown source corpus
- `sidecar/` - manifesting, provenance, retrieval, and CocoIndex example flow
- `scripts/` - build, load, query, and demo commands
- `docker-compose.yml` - local Postgres + pgvector (optional)
- `.github/workflows/` - CI and GitHub Pages deploy
- `writeback/` - extracted claim suggestions for review

## Commands

| Command | Purpose |
| --- | --- |
| `wiki -c wiki.yml fmt --check` | Mechanical markdown formatting check |
| `wiki -c wiki.yml lint --strict` | Broken links, filename pattern, heading conventions |
| `wiki -c wiki.yml check --strict` | SHACL, JSON Schema, route, and layout integrity |
| `python scripts/build_manifest.py` | Export deterministic page/chunk/link manifests |
| `python scripts/load_index.py` | Upsert chunk records into Postgres/pgvector (auto-detects Docker or PGlite) |
| `python scripts/query_index.py` | Search the derived index and print citations |
| `python scripts/demo_incremental_update.py` | Show what changes when a Wiki page changes |

## Architecture

```text
Wiki Markdown + wiki.yml
  -> wiki fmt / lint / check
  -> deterministic manifest build
  -> derived sidecar index
  -> Postgres + pgvector (Docker) or PGlite (zero-Docker)
  -> cited retrieval results
```

## Trust boundaries

- Wiki pages are authoritative.
- CocoIndex outputs are derived and rebuildable.
- Every record carries page path, heading, fragment, content hash, and source graph.
- Freshness is verifiable: every record includes a `wiki_lock_hash` matching the current `wiki.lock` (or `"none"` for lockless mode).
- Generated claims stay in `writeback/suggestions/` until reviewed and promoted into the source corpus.

## Writeback pattern

CocoIndex-derived memory should not silently become the canonical corpus. The template uses a `writeback/suggestions/` directory for extracted claims:

1. CocoIndex extracts claims from Wiki content.
2. Claims are written to `writeback/suggestions/` as structured YAML.
3. A human reviews each suggestion.
4. Approved suggestions are promoted into `wiki/` via normal Wiki workflow.

This keeps Wiki as the single source of truth while allowing agent-generated insights to feed back into the corpus with review.

## Deployment

This template publishes the wiki site with GitHub Pages.

1. Enable **Settings -> Pages -> Source: GitHub Actions**.
2. Push to `main`.
3. The deploy workflow publishes the built site.

## Why not just use SPARQL or plain RAG?

- Wiki-only SPARQL is best when the answer already lives in the graph.
- Plain vector RAG is not enough when provenance and freshness matter.
- CocoIndex sits in the middle: incremental, derived, and easy to rebuild.

## Open questions (design decisions)

This template resolves the following design questions from [#201](https://github.com/wazootech/wiki/issues/201):

| Question | Decision | Rationale |
| --- | --- | --- |
| First target | pgvector via Docker, PGlite fallback | Production-like Docker path + zero-setup PGlite path |
| Chunk manifests | Sidecar-owned, not Wiki CLI | Section splitting is a CocoIndex concern; Wiki CLI owns RDF export |
| Source identity | `wiki_lock_hash` in every record | Verifiable freshness against `wiki.lock` |
| Writeback | Report-only in v1 | Wiki trust model requires human review before corpus promotion |
| Template shape | Standalone repo | Independent versioning, not a variant of RAG templates |
