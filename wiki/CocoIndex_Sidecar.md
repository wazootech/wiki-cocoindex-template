# CocoIndex sidecar

CocoIndex is the incremental runtime layer for this template.

It reads Wiki exports or deterministic manifests, updates downstream targets only for changed chunks, and preserves page path, heading, fragment, and content hash on every record. The source graph rules live in [Source graphs](Source_Graphs.md).

## Recommended flow

1. Validate the wiki corpus with `wiki -c wiki.yml fmt --check`, `lint --strict`, and `check --strict`.
1. Build the manifest with `python scripts/build_manifest.py`.
1. Load or update the derived index with `python scripts/load_index.py`.
1. Query the index and cite the Wiki source page.

## Where CocoIndex fits

- It owns incremental materialization.
- It does not replace the Wiki graph.
- It should be treated as disposable output that can be rebuilt from the source corpus.
