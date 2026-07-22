# wiki-template

Generic **Wiki CLI** workspace starter — `wiki init` parity plus GitHub Pages deploy.

This is the privileged generic scaffold. For the Karpathy-pattern [LLM Wiki](https://github.com/wazootech/wiki/blob/main/docs/wiki/LLM_Wiki.md) vault (agent gardening, shapes, SPARQL indexes), use [`llm-wiki-template`](https://github.com/wazootech/llm-wiki-template) ([#83](https://github.com/wazootech/wiki/issues/83)).

Full ecosystem registry: [Wiki CLI templates](https://github.com/wazootech/wiki/blob/main/docs/wiki/Wiki_CLI.md#ecosystem-templates).

## Quick start

1. Click **Use this template** on GitHub (or clone this repo).
2. Install [Wiki CLI](https://pypi.org/project/wazootech-wiki/):

```bash
pip install wazootech-wiki
```

3. Validate and preview:

```bash
wiki check --strict
wiki serve --watch
```

4. Enable **Settings → Pages → Source: GitHub Actions** so the deploy workflow can publish `wiki build` output.

## Workspace layout

- `wiki.yaml` — config root (`wiki.inputs`, `graph.*`, `site.*`)
- `wiki/` — markdown vault with semantic frontmatter
- `layouts/` — Jinja page templates
- `assets/` — static files copied on `wiki build`

## Commands

| Command | Purpose |
| ------- | ------- |
| `wiki check` | SHACL, JSON Schema, routes, layout integrity |
| `wiki lint` | Broken links, filename pattern, heading conventions |
| `wiki fmt` | Mechanical markdown layout |
| `wiki serve --watch` | Local preview |
| `wiki build` | Static HTML for deployment |
| `wiki export` | JSON-LD, Turtle, TriG RDF serializations |

## Related

- [Wiki CLI](https://github.com/wazootech/wiki)
- [Getting started](https://github.com/wazootech/wiki/blob/main/docs/wiki/Getting_Started.md)

## Deployment

This wiki builds to a static site. Any provider that serves static files works.

### GitHub Pages (preferred)

1. Go to **Settings &rarr; Pages &rarr; Source: GitHub Actions**
2. Push to the default branch &mdash; the \.github/workflows/deploy-pages.yml\ workflow builds and deploys automatically
3. Your site appears at \https://{org}.github.io/{repo}/\

### Vercel

1. Import this repo at [vercel.com/new](https://vercel.com/new)
2. **Build command:** \pip install wazootech-wiki && wiki build --output-dir .vercel/output --site-base-url /\
3. **Output directory:** \.vercel/output\
4. Deploy

### Netlify

1. Import this repo at [app.netlify.com/start](https://app.netlify.com/start)
2. **Build command:** \pip install wazootech-wiki && wiki build --output-dir _site --site-base-url /\
3. **Publish directory:** \_site\
4. Deploy

### Cloudflare Pages

1. Import this repo in the Cloudflare dashboard
2. **Build command:** \pip install wazootech-wiki && wiki build --output-dir _site --site-base-url /\
3. **Output directory:** \_site\
4. Deploy
