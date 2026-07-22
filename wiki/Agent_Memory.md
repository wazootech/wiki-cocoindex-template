---
type: schema:CreativeWork
schema:about: cocoindex:IncrementalIndexing
---

# Agent memory

Wiki is the source of truth. CocoIndex materializes a derived memory layer from validated pages, then keeps it fresh by processing only changed inputs.

The important rule is simple: generated memory can inform the next retrieval pass, but it does not become canonical until it is written back into Wiki with review. See [retrieval policy](Retrieval_Policy.md) for the trust boundary.
