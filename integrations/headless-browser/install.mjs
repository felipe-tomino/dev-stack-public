import { constants } from 'node:fs';
import { access, lstat, mkdir, open, readdir, realpath, rename, unlink } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { dirname, isAbsolute, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Browser, BrowserTag, detectBrowserPlatform, install, resolveBuildId } from '@puppeteer/browsers';

const runtime = dirname(fileURLToPath(import.meta.url));
const cacheDir = join(runtime, 'browsers');
const marker = join(runtime, 'executable.txt');

async function inspect(path) {
  try {
    return await lstat(path);
  } catch (error) {
    if (error.code === 'ENOENT') return undefined;
    throw error;
  }
}

async function checkMarker() {
  const info = await inspect(marker);
  if (info && (!info.isFile() || info.isSymbolicLink())) {
    throw new Error(`Refusing non-regular executable marker: ${marker}`);
  }
}

function inside(directory, path) {
  const value = relative(directory, path);
  return value !== '' && value !== '..' && !value.startsWith(`..${sep}`) && !isAbsolute(value);
}

// Never let an existing cache redirect the installer into a foreign directory.
async function checkCache(directory, root = directory) {
  const info = await inspect(directory);
  if (!info) return;
  if (info.isSymbolicLink() || !info.isDirectory()) {
    throw new Error(`Refusing non-directory or symlinked browser cache: ${directory}`);
  }
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isSymbolicLink()) {
      if (!inside(root, await realpath(path))) {
        throw new Error(`Refusing symlink outside browser cache: ${path}`);
      }
    }
    if (entry.isDirectory()) await checkCache(path, root);
  }
}

async function provision() {
  const runtimeInfo = await lstat(runtime);
  if (runtimeInfo.isSymbolicLink() || !runtimeInfo.isDirectory()) {
    throw new Error(`Refusing symlinked browser runtime: ${runtime}`);
  }
  await checkMarker();
  await checkCache(cacheDir);
  await mkdir(cacheDir, { recursive: true, mode: 0o700 });

  const platform = detectBrowserPlatform();
  if (!platform) throw new Error('This platform is not supported by the dedicated headless browser.');
  const browser = Browser.CHROMIUM;
  const buildId = await resolveBuildId(browser, platform, BrowserTag.LATEST);
  console.log(`Provisioning ${browser} ${buildId} (${platform})`);
  const installed = await install({ browser, buildId, platform, cacheDir });
  const executable = installed.executablePath;
  const executableInfo = await lstat(executable);
  if (!isAbsolute(executable) || !executableInfo.isFile() || /[\r\n]/u.test(executable)) {
    throw new Error(`Installer returned an invalid browser executable: ${executable}`);
  }
  const resolvedCache = await realpath(cacheDir);
  const resolvedExecutable = await realpath(executable);
  if (!inside(resolvedCache, resolvedExecutable)) {
    throw new Error(`Browser executable is outside the dedicated cache: ${executable}`);
  }
  await access(executable, constants.X_OK);
  await checkMarker();

  // Publish only after a successful install. Rename replaces the marker, never its target.
  const temporary = join(runtime, `.executable-${randomUUID()}.tmp`);
  let file;
  try {
    file = await open(temporary, 'wx', 0o600);
    await file.writeFile(`${executable}\n`, 'utf8');
    await file.sync();
    await file.close();
    file = undefined;
    await checkMarker();
    await rename(temporary, marker);
  } finally {
    if (file) await file.close();
    await unlink(temporary).catch(error => {
      if (error.code !== 'ENOENT') throw error;
    });
  }
  console.log(`Dedicated browser executable: ${executable}`);
}

provision().catch(error => {
  console.error(`Headless browser provisioning failed: ${error.message}`);
  process.exitCode = 1;
});
