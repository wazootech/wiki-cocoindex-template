# Source graphs

This template keeps graph identity explicit so derived records can be traced back to the Wiki corpus that produced them.

Use source graph identifiers when the same template indexes multiple corpora, branches, or release snapshots. The manifest builder stores them in each chunk row.

## Conventions

- `source_graph` names the Wiki corpus boundary.
- `content_hash` names the exact source payload.
- `chunk_id` names a deterministic derived record.
- `derived_at` names the freshness moment.
