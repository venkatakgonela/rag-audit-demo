import { pathToFileURL } from 'node:url';
import { readFile } from 'node:fs/promises';

const [modulePath, executablePath, source, destination] = process.argv.slice(2);
const { default: puppeteer } = await import(pathToFileURL(modulePath).href);
const browser = await puppeteer.launch({
  executablePath,
  headless: true,
  args: ['--disable-background-networking', '--disable-component-update',
    '--disable-sync', '--no-first-run', '--host-resolver-rules=MAP * ~NOTFOUND'],
});
try {
  const page = await browser.newPage();
  const blocked = [];
  await page.setRequestInterception(true);
  page.on('request', request => {
    if (request.url().startsWith('data:')) request.continue();
    else { blocked.push(request.url()); request.abort(); }
  });
  await page.setContent(await readFile(source, 'utf8'), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  if (blocked.length) throw new Error('audit_external_resource: blocked request');
  await page.pdf({path: destination, format: 'A4', printBackground: true,
    preferCSSPageSize: true, displayHeaderFooter: false});
  console.log(`Browser ${await browser.version()}; external requests: ${blocked.length}`);
} finally {
  await browser.close();
}
