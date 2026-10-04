# Presentation diagram sources

These figures explain implemented behaviour, not proposed production services.
Each SVG contains an accessible title and description; the embedding Markdown
provides alt text, a caption, a legend and links to the underlying evidence.

| Figure | Editable source | Where it is explained |
| --- | --- | --- |
| Request ownership | [SVG](ownership-flow.svg), [PNG](ownership-flow.png) | [Architecture](../ARCHITECTURE.md#who-does-what) |
| Risk, control, evidence | [SVG](risk-control-evidence.svg), [PNG](risk-control-evidence.png) | [Governance](../governance.md#from-risk-to-reviewable-evidence) |
| Release gate lifecycle | [SVG](release-gate.svg), [PNG](release-gate.png) | [Release gate](../release-gate.md) |

## Render without adding dependencies

The existing [audit builder](../audit/README.md) uses installed headless Chrome
and Puppeteer. Its PDF build consumes committed figures; it does not regenerate
presentation PNGs. Use that same installed browser tooling to render these SVGs.
No package install, provider call or remote resource is needed. Existing audit
Mermaid sources and images in `docs/audit/figures/` remain unchanged.

From the repository root, set `AUDIT_CHROME` to the installed Chrome executable
and `AUDIT_PUPPETEER_MODULE` to the installed Puppeteer ES module entry point, then:

```sh
node --input-type=module <<'JS'
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
const { default: puppeteer } = await import(pathToFileURL(process.env.AUDIT_PUPPETEER_MODULE).href);
const browser = await puppeteer.launch({
  executablePath: process.env.AUDIT_CHROME,
  headless: true,
  args: ['--disable-background-networking', '--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND']
});
try {
  for (const name of ['ownership-flow', 'risk-control-evidence', 'release-gate']) {
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request', request => request.abort());
    await page.setViewport({ width: 1000, height: 1000, deviceScaleFactor: 2 });
    const svg = await readFile(`docs/images/${name}.svg`, 'utf8');
    await page.setContent(`<style>body{margin:0}svg{display:block}</style>${svg}`);
    await page.$eval('svg', element => element.getBoundingClientRect().width);
    await (await page.$('svg')).screenshot({ path: `docs/images/${name}.png` });
    await page.close();
  }
} finally {
  await browser.close();
}
JS
```

Inspect each PNG at a displayed width of about 760 pixels before committing:
labels must remain readable, arrows must not cross text, and text must stay
inside its box. The flow is also explained in prose for readers who cannot see
the image. `make test` checks local Markdown links, not visual accuracy.
