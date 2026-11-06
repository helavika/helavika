// Renders the pixel-art castle from the portfolio site (~/projects/helavika-portfolio)
// into scripts/castle-dark.png and scripts/castle-light.png (sepia), upscaled 3x with
// hard pixels. build_banner.py embeds them in the header SVGs.
//
// Run: node scripts/render_castle.mjs [path/to/portfolio/index.html]
import { chromium } from '/Users/viktoriashchipalkina/oss/kaplay/node_modules/playwright/index.mjs';
import { writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const page_ = process.argv[2] || join(homedir(), 'projects/helavika-portfolio/index.html');

const browser = await chromium.launch();
const page = await browser.newPage({ reducedMotion: 'reduce' }); // one still frame, no animation
await page.goto('file://' + page_);
await page.waitForTimeout(300);
const shots = await page.evaluate(() => {
  const src = document.getElementById('scene');
  const scale = 3;
  const out = {};
  for (const [name, filter] of [['dark', 'none'], ['light', 'grayscale(1) sepia(.85) contrast(1.15) brightness(1.25)']]) {
    const c = document.createElement('canvas');
    c.width = src.width * scale; c.height = src.height * scale;
    const ctx = c.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.filter = filter;
    ctx.drawImage(src, 0, 0, c.width, c.height);
    out[name] = c.toDataURL('image/png').split(',')[1];
  }
  return out;
});
for (const [name, b64] of Object.entries(shots)) {
  writeFileSync(join(here, `castle-${name}.png`), Buffer.from(b64, 'base64'));
  console.log(`wrote scripts/castle-${name}.png`);
}
await browser.close();
