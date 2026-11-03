import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {selectComposition, renderMedia} from '@remotion/renderer';

const root = path.dirname(fileURLToPath(import.meta.url));
const [input, output] = process.argv.slice(2);
if (!input || !output || !process.env.REMOTION_BROWSER_EXECUTABLE) {
  throw new Error('Usage: REMOTION_BROWSER_EXECUTABLE=/path/to/existing/chrome node render.mjs PREPARED.json NEW_OUTPUT_DIRECTORY');
}
const timing = JSON.parse(fs.readFileSync(input, 'utf8'));
if (!Number.isInteger(timing.durationInFrames) || timing.durationInFrames < 1 || timing.durationInFrames > 3600 || timing.activeByFrame.length !== timing.durationInFrames) {
  throw new Error('Use a bounded file from prepare.py');
}
const out = path.resolve(output);
if (fs.existsSync(out)) throw new Error('Output directory exists; choose a new directory');
fs.mkdirSync(out);
const publicDir = path.join(out, 'public');
fs.mkdirSync(publicDir);
const serveUrl = await bundle({entryPoint: path.join(root, 'Composition.tsx'), rootDir: root,
  outDir: path.join(out, 'bundle'), publicDir, enableCaching: false, rspack: false});
const inputProps = {timing};
// An available local port avoids interfering with an existing Studio/app server.
const port = await new Promise((resolve, reject) => {
  const server = net.createServer();
  server.on('error', reject);
  server.listen(0, '127.0.0.1', () => {const value = server.address().port; server.close(() => resolve(value));});
});
const common = {serveUrl, inputProps, port, browserExecutable: process.env.REMOTION_BROWSER_EXECUTABLE, logLevel: 'warn'};
for (const id of ['Source', 'Edited']) {
  const composition = await selectComposition({...common, id});
  const outputLocation = path.join(out, id === 'Source' ? 'source.mp4' : 'edited.mp4');
  await renderMedia({...common, composition, codec: 'h264', crf: 16, concurrency: 2, muted: true,
    overwrite: false, outputLocation, disableSharedMemoryCapture: true,
    offthreadVideoCacheSizeInBytes: 32 * 1024 * 1024});
  if (id === 'Source') fs.copyFileSync(outputLocation, path.join(serveUrl, 'public', 'source.mp4'));
  console.log(JSON.stringify({id, frames: composition.durationInFrames, fps: composition.fps, outputLocation}));
}
fs.writeFileSync(path.join(out, 'timing.json'), JSON.stringify(timing, null, 2) + '\n', {flag: 'wx'});
