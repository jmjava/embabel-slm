// Syntax-check snippet files with the TypeScript compiler's parser.
// argv: node ts_syntax_check.mjs TYPESCRIPT_PACKAGE WORKDIR
import { createRequire } from "node:module";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const require = createRequire(import.meta.url);
const typescriptPackage = process.argv[2];
const workdir = process.argv[3];
if (!typescriptPackage || !workdir) {
  console.error("usage: node ts_syntax_check.mjs TYPESCRIPT_PACKAGE WORKDIR");
  process.exit(2);
}
const ts = require(typescriptPackage);
const manifest = JSON.parse(fs.readFileSync(path.join(workdir, "manifest.json"), "utf8"));
const results = [];
for (const item of manifest) {
  const bytes = fs.readFileSync(item.path);
  const digest = crypto.createHash("sha256").update(bytes).digest("hex");
  if (digest !== item.code_sha256) {
    console.error(`hash mismatch for ${item.example_id}`);
    process.exit(2);
  }
  const code = bytes.toString("utf8");
  const source = ts.createSourceFile(item.path, code, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const errors = (source.parseDiagnostics || []).filter(
    (diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error,
  );
  let detail = "typescript_parse";
  if (errors.length > 0) {
    detail = ts.flattenDiagnosticMessageText(errors[0].messageText, "\n").slice(0, 200);
    detail = detail.replace(/[^\x20-\x7e]/g, "?");
  }
  results.push({
    example_id: item.example_id,
    code_sha256: digest,
    ok: errors.length === 0,
    detail,
  });
}
const lines = results.map((row) => {
  const ordered = {};
  for (const key of Object.keys(row).sort()) ordered[key] = row[key];
  return JSON.stringify(ordered);
});
const text = lines.length ? `${lines.join("\n")}\n` : "";
fs.writeFileSync(path.join(workdir, "results.jsonl"), text);
const resultsSha = crypto.createHash("sha256").update(text).digest("hex");
process.stdout.write(
  `${JSON.stringify({
    checked: results.length,
    passed: results.filter((row) => row.ok).length,
    results_sha256: resultsSha,
  })}\n`,
);
