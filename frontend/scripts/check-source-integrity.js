/**
 * Source Integrity Check — prebuild guard for Article III (Z-03B).
 *
 * Fails the build if any stale `.js` files shadow `.tsx`/`.ts` sources,
 * or if duplicate `src/` trees exist.
 *
 * This prevents the "stale build artifact" defect that caused the
 * production deploy to serve outdated code (Z-03A regression).
 */
import { existsSync, readdirSync, statSync } from 'fs';
import { join, relative, resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const SRC = resolve(__dirname, '..', 'src');

let errors = 0;

function checkDir(dir) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }

  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      // Skip node_modules and hidden dirs
      if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
      checkDir(full);
    } else if (entry.isFile() && entry.name.endsWith('.js')) {
      const base = entry.name.slice(0, -3);
      const tsxPath = join(dir, `${base}.tsx`);
      const tsPath = join(dir, `${base}.ts`);
      if (existsSync(tsxPath) || existsSync(tsPath)) {
        const rel = relative(SRC, full);
        console.error(`ERROR: Stale .js file shadows source: ${rel}`);
        errors++;
      }
    }
  }
}

// Check for duplicate src/ trees
function checkDuplicateSrc() {
  const entries = readdirSync(SRC, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.isDirectory() && entry.name === 'src') {
      const nestedSrc = join(SRC, 'src');
      if (existsSync(join(nestedSrc, 'app.tsx')) || existsSync(join(nestedSrc, 'main.tsx'))) {
        console.error(`ERROR: Duplicate src/ tree found: ${relative(SRC, nestedSrc)}`);
        errors++;
      }
    }
  }
}

console.log('Checking source integrity...');
checkDir(SRC);
checkDuplicateSrc();

if (errors > 0) {
  console.error(`\nFAILED: ${errors} source integrity violation(s) found.`);
  console.error('Run `find src/ -name "*.js" -exec sh -c \'test -f "${1%.js}.tsx" && rm "$1"\' _ {} \\;` to clean up.');
  process.exit(1);
}

console.log('OK: source integrity check passed.');