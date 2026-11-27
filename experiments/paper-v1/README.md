# Paper v1 experiment freeze

Committed summaries only. Raw `eval-runs/` stay in `slm-setup` (gitignored). No hostnames, LAN addresses, secrets, or raw completions.

## Publication gate

No Zenodo upload until the operator's internal publication-review checklist is complete.

## Freeze status

| Field | Value |
| --- | --- |
| Corpus repo | `jmjava/slm-setup` |
| Corpus SHA | _TBD after next pin_ |
| Protocol doc | `docs/protocol/preregistration.md` |
| Confirmatory arms | **S** (shareable 7–14B, configs A–D), **M** (24–34B, A/B), **L** (ceiling, A/B) |
| Inference backend | **Ollama** on `halo-395` for confirmatory rows |
| Quant default | Q4_K_M; one Q8_0 sensitivity row on shareable base config A |
| Fast model tag + digest | _TBD_ (starter candidate `qwen3.5:9b`) |
| Strong model tag + digest | _TBD_ (starter candidate `devstral-small-2`) |
| Live sessions completed | 0 |
| Paper host | **`halo-395` (`ubuntu-A9-Mega`)** — GEEKOM Strix Halo / 8060S, Linux 7.0.0-44, `/dev/kfd` + `renderD128` |
| Fallback host | `downstairs-4080` (3060 secondary) only if Halo AMD placement fails |
| IDE workstation | MCP only — inference non-starter |
| Halo inference OS | **Linux primary as of 2026-11-26** — Ollama **0.40.17**; tags `qwen3.5:9b`, `devstral-small-2`, `qwen3-coder:30b`, `gpt-oss:120b` installed; **no active model**; **no paper-scored rows** |
| Embabel holdout manifest SHA256 | _TBD — commit before first Embabel holdout score_ |
| Combined holdout min tasks | 742, one exam for both subjects |
| Drivine corpus repo | `jmjava/drivine-slm` |
| Drivine holdout manifest SHA256 | _TBD — commit before first Drivine holdout score_ |
| Drivine tasks in that holdout | executable; they share the 742-task exam |
| Drivine pilot harness | **exists** in `jmjava/drivine-slm` (`python/drivine_runner`); confirmatory harness **incomplete**; confirmatory scored rows **0** |
| Corpus audit (current) | **53,676** raw → **16,211** labeled exact-code targets + **34,247** review; **211** provisional over **≥16,000 clean admitted** gate (feasibility high risk, not established) |
| Mandatory seal | `python3 -m analysis seal-study` before prefixes; **0** scored confirmatory rows |
| Training formatter | `embabel-slm-code-sft-v1` (selected-tokenizer counts: blocker) |
| Drivine live sessions completed | 0 |
| Part A (MCP) freeze | target Fri 9 Jan 2027 |
| All-numbers freeze | target Fri 27 Feb 2027 |
| DOI deadline | 31 Mar 2027 |

## Raw-data contract (research quality)

Every live or Embabel scored run writes a **new** directory (never overwrite):

| Artifact | Required |
| --- | --- |
| `meta.json` | model tag, digest, quant, prompt id, corpus/repo SHAs, `host_class`, `arm`, `config`, `split`, `num_ctx`, Ollama version, peak memory GB when available, decoding block |
| `scores.json` / JSONL | layer outcomes, pass@1, greedy pass, first_failure |
| `raw/` | greedy + `sample1..k` outputs (local only; scrub before Zenodo) |
| `notes.md` | operator observations, no LAN/hostname |

Zenodo gets scrubbed tables + `artifact-manifest.md`. Negative results count.

## Oracle environment

Admission runs on the labeled JSONL and the pinned checkouts. A checkout counts only when `git rev-parse HEAD` equals that row's `source_pin`. Embabel checkouts live under `checkouts/embabel/<repo>` and Drivine checkouts under `checkouts/drivine/<repo>`. Evidence is kept outside this repo. A green local run is not a sealed study.

Install, from a clean shell:

| Tool | Role |
| --- | --- |
| Python 3 | `python3 -m analysis` commands. Stdlib only. |
| Node.js | TypeScript syntax checker `analysis/ts_syntax_check.mjs`. |
| `typescript` npm package | Parser oracle. The emit command takes the package directory, for example `node_modules/typescript` after `npm install typescript@5.9.3`. |
| `drivine-cypher-compiler==0.53.0` | Cypher compiler wheel declared by the pinned `drivine-python` package. Linux glibc x86_64 or aarch64. Pass that interpreter as `--python` for `--language cypher`. |
| JDK 21 | Gradle toolchains in `drivine4j` and `drivine-cypher-spec/compiler` request language level 21 and do not download one unless a toolchain repository is configured. A JDK 25 `javac` does not satisfy that request. Temurin `21.0.13.1+2` works. Pass `-Dorg.gradle.java.installations.paths` pointing at that JDK. |
| Maven | Embabel projects. `mvn -B -DskipTests compile` covers `src/main` only. Test sources need `mvn -B test-compile`. |

Snippet checks (Python `ast.parse`, Cypher compile to SQLite SQL, TypeScript parse). A snippet is kept only when it is present in the pinned file and the checker exits 0:

```bash
python3 -m analysis.snippet_oracle emit \
  --language python \
  --labeled LABELED.jsonl \
  --checkouts CHECKOUTS \
  --workdir WORK \
  --evidence-out python-evidence.jsonl \
  --summary-out python-summary.json
```

Use `--language cypher` with `--python` set to the interpreter that has `drivine-cypher-compiler`. Use `--language typescript` with `--typescript` set to the installed `typescript` package directory.

Project compiles cover a snippet only when the build exits 0, the source path is under a `--source-root` you name, and the suffix is `.kt`, `.java`, `.ts`, or `.tsx`. Do not name a root the command did not compile. `mvn -B -DskipTests compile` is main sources only.

```bash
python3 -m analysis.project_oracle \
  --repo liberation-data/drivine4j \
  --checkouts CHECKOUTS \
  --labeled LABELED.jsonl \
  --evidence-out drivine4j-evidence.jsonl \
  --summary-out drivine4j-summary.json \
  --source-root src/main/kotlin \
  --source-root src/test/kotlin \
  -- ./gradlew --no-daemon \
       -Dorg.gradle.java.installations.paths=JDK21 \
       compileKotlin compileJava compileTestKotlin compileTestJava
```

For `liberation-data/drivine-cypher-spec`, set `--command-cwd compiler` and compile `compileKotlinJvm compileTestKotlinJvm`. Source roots for that JVM build are `compiler/src/commonMain/kotlin`, `compiler/src/commonTest/kotlin`, `compiler/src/jvmMain/kotlin`, and `compiler/src/jvmTest/kotlin`.

On 2026-11-27 this environment admitted **11,324** labeled rows (11,321 Drivine and 3 Embabel from `kotlin-agent-template`). That is short of the 16,000 clean-admitted floor. The other Embabel checkouts are not compiled yet. Do not seal from this count.

## Result tables

Add CSV/Markdown here after live runs, e.g.:

- `layer-rates.md`
- `pass-at.md`
- `prompt-contract.md`
- `embabel-arms-holdout.md` (S/M/L after Embabel holdout)
- `drivine-arms-holdout.md` (S/M/L after Drivine holdout; executable tasks only)
- `example-dose-combined.md` (prefix 16000 minus 500 confirmatory; adjacent doublings exploratory)
- `example-dose-by-domain.md` (Embabel/Drivine slices exploratory only; executable Drivine tasks)