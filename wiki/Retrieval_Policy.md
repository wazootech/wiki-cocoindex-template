# Retrieval policy

Derived results must always keep the source trail visible.

## Rules

- Cite the page path.
- Cite the heading or fragment.
- Keep the source graph and content hash on every derived row.
- Prefer validated Wiki metadata over embedding similarity when both are available.
- Treat generated claims as suggestions until reviewed. The memory flow in [Agent memory](Agent_Memory.md) shows the review boundary.

## Good output

`wiki/CocoIndex_Sidecar.md#recommended-flow` `sha256:...`

## Bad output

Uncited summaries with no trace back to the Wiki page they came from.
