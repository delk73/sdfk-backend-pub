#!/usr/bin/env node
/**
 * DocOps — tiny docs linter/rewriter
 *
 * Modes:
 *   --lint      : scan docs and report issues (non-zero exit on offenders)
 *   --verbose   : print every scanned file (works with --lint)
 *
 * Behavior:
 *   - Walks docs/** (including _graveyard and _refresh).
 *   - Skips only node_modules and .git.
 *   - Lint checks for "GridControl" references.
 *   - Rewrite mode (default) fixes legacy GRIDCONTROL.md links, if any.
 */

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const docsRoot = path.join(root, 'docs');

// Only skip the obvious; INCLUDE _graveyard and _refresh
const skipDirs = new Set(['node_modules', '.git']);

const args = new Set(process.argv.slice(2));
const VERBOSE = args.has('--verbose') || args.has('--debug');
const LINT = args.has('--lint');

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (skipDirs.has(entry.name)) continue;
      files.push(...walk(p));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(p);
    }
  }
  return files;
}

function rewriteLinks(file) {
  let text = fs.readFileSync(file, 'utf8');

  // Basic link normalizer + special-case legacy GRIDCONTROL.md
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  text = text.replace(linkRegex, (match, label, target) => {
    const normalized = target.replace(/^\.\//, '');

    // If someone links to GRIDCONTROL.md, redirect to docs/frontend/rule_bundles.md when present.
    if (/GRIDCONTROL\.md/i.test(normalized)) {
      const fallback = path.resolve(root, 'docs/frontend/rule_bundles.md');
      if (fs.existsSync(fallback)) {
        const rel = path.relative(path.dirname(file), fallback);
        return `[${label}](${rel})`;
      }
      // If no fallback, keep the label and drop the broken link to avoid confusion.
      return `[${label}]`;
    }

    return match;
  });

  fs.writeFileSync(file, text);
}

function lintFiles(files) {
  const offenders = [];
  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    if (/GridControl/i.test(content)) offenders.push(file);
  }

  console.log('DocOps Lint Summary');
  console.log('===================');
  console.log(`Root:      ${docsRoot}`);
  console.log(`Scanned:   ${files.length} markdown files`);
  console.log(`Offenders: ${offenders.length}`);

  if (VERBOSE) {
    console.log('\nScanned files:');
    for (const f of files) console.log(' - ' + path.relative(root, f));
  }

  if (offenders.length) {
    console.log('\nOffending files (contain "GridControl"):');
    for (const f of offenders) console.log(' - ' + path.relative(root, f));
    process.exit(1);
  }
}

function main() {
  const all = walk(docsRoot);

  if (LINT) {
    lintFiles(all);
    return;
  }

  // Rewrite mode (idempotent, safe)
  for (const file of all) {
    try {
      rewriteLinks(file);
      if (VERBOSE) console.log('Rewrote links in', path.relative(root, file));
    } catch (e) {
      console.error('Rewrite failed for', file, e?.message || e);
      process.exitCode = 2;
    }
  }
}

if (require.main === module) {
  main();
}
