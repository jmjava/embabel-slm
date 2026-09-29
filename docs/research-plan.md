# embabel-slm

A research and engineering project for building and evaluating a small, locally runnable coding model specialized for the Embabel framework and the surrounding Spring/Java/Kotlin ecosystem.

## Project Goal

Determine how small a coding model can be while still achieving strong, reliable performance on Embabel-specific software engineering tasks through a combination of:

1. A strong pretrained coding model
2. Embabel-specific retrieval augmented generation (RAG)
3. LoRA / QLoRA parameter-efficient fine-tuning
4. Compiler- and test-driven evaluation
5. Automated synthetic training-data generation with verification

The core hypothesis is that a relatively small coding model can become highly effective on a narrow software framework when it is given the right retrieval context, task-specific training data, and automated feedback.

---

## Research Question

> How small can a coding model become while retaining expert-level performance on a narrow software framework through retrieval and parameter-efficient fine-tuning?

A more specific Embabel version:

> Can a 7B–32B local coding model, specialized using Embabel RAG and LoRA/QLoRA, match or exceed much larger generic coding models on Embabel-specific development tasks?

---

## Why Embabel

Embabel is a good target for narrow model specialization because it has:

- A bounded framework vocabulary
- Clear abstractions such as actions, goals, conditions, agents, plans, and domain objects
- Strong interaction with Spring, Java, and Kotlin
- Code that can be compiled and tested automatically
- Planner behavior that can be evaluated structurally
- Enough complexity to require reasoning beyond autocomplete
- A relatively small framework surface compared with general-purpose software engineering

This makes Embabel well suited to a controlled study of domain-specialized coding models.

---

# Project Phases

## Phase 1 — Baseline

Establish how well several unmodified coding models perform on a fixed Embabel benchmark.

Candidate model sizes:

- ~7B
- ~14B
- ~32B

Possible base-model families should be selected based on current coding quality, permissive licensing, local inference support, and ROCm compatibility.

Do not choose the permanent base model until baseline testing is complete.

### Baseline Questions

Measure whether the model can:

- Explain Embabel concepts
- Write a simple `@Action`
- Define goals and conditions
- Build an agent
- Understand action inputs and outputs
- Construct reachable plans
- Fix unreachable goals
- Debug broken Embabel code
- Write tests
- Integrate Embabel into Spring Boot
- Convert imperative Spring logic into Embabel-style planning
- Interpret compiler errors
- Interpret planner/runtime errors
- Refactor code toward idiomatic Embabel

---

## Phase 2 — Embabel RAG

Add retrieval over current Embabel material.

Potential corpus:

- Embabel source code
- README files
- Reference documentation
- Javadocs / KDocs
- Tests
- Examples
- Cookbook examples
- Sample applications
- GitHub issues
- GitHub discussions
- Release notes
- Migration notes
- Relevant Spring documentation

### Initial RAG Architecture

```text
Developer task
     |
     v
Query analysis
     |
     v
Embabel/Spring retrieval
     |
     v
Optional reranker
     |
     v
Prompt assembly
     |
     v
Local coding model
     |
     v
Generated code
     |
     v
Compile / test / evaluate
```

### Questions to Measure

- How much does RAG improve correctness?
- Does source retrieval outperform documentation-only retrieval?
- How many retrieved chunks are optimal?
- Does reranking improve results?
- How sensitive is performance to stale documentation?
- Does retrieval reduce hallucinated APIs?
- Does retrieval increase code compilation success?

---

## Phase 3 — Benchmark Suite

Create a stable Embabel-specific benchmark before fine-tuning.

Target initial size:

- 100–300 benchmark tasks

Later target:

- 500+ tasks

Benchmark tasks must remain separate from training data.

### Task Categories

#### 1. Code Generation

Examples:

- Write an Embabel `@Action`
- Create a goal
- Create a condition
- Define an agent
- Add planner-compatible input/output types
- Configure Embabel in Spring Boot
- Write a unit test

#### 2. Code Repair

Examples:

- Fix compilation failure
- Fix invalid action signatures
- Repair unreachable goals
- Correct missing planner dependencies
- Repair incorrect annotations
- Fix Spring bean configuration
- Fix type mismatch
- Repair broken tests

#### 3. Planning Reasoning

Examples:

- Determine whether a goal is reachable
- Identify the missing action
- Determine which action sequence satisfies a goal
- Explain why the planner gets stuck
- Identify conflicting conditions
- Predict generated plan structure

#### 4. Transformation

Examples:

- Convert imperative Spring service logic to Embabel
- Split a monolithic flow into actions
- Replace manual orchestration with planner-driven execution
- Convert callback-style logic to agent actions
- Convert Java implementation to idiomatic Kotlin

#### 5. Refactoring

Examples:

- Improve Embabel idioms
- Reduce unnecessary action coupling
- Improve domain modeling
- Improve action boundaries
- Replace procedural coordination with goal-oriented planning

#### 6. Integration

Examples:

- Spring Boot
- REST APIs
- MCP
- Persistence
- Security
- LLM calls
- RAG
- Event-driven workflows
- External services

---

# Evaluation Strategy

A major advantage of coding-model research is that many outputs can be evaluated automatically.

## Automatic Checks

Where possible, every generated solution should be evaluated using:

1. Parse success
2. Compilation success
3. Unit-test success
4. Integration-test success
5. Spring application-context startup
6. Embabel planner execution
7. Expected goal reachability
8. Static analysis
9. Formatting/linting
10. API correctness

### Example Evaluation Pipeline

```text
Model response
    |
    v
Extract code
    |
    v
Create isolated project/worktree
    |
    v
Compile
    |
    +---- FAIL --> classify compiler error
    |
    v
Run tests
    |
    +---- FAIL --> classify test failure
    |
    v
Start Spring context
    |
    +---- FAIL --> classify configuration failure
    |
    v
Run Embabel scenario
    |
    +---- FAIL --> planner/runtime analysis
    |
    v
Score task
```

---

# Suggested Metrics

Track multiple dimensions rather than one overall score.

## Core Metrics

- Compile pass rate
- Unit-test pass rate
- Full task success rate
- Planner success rate
- Correct API usage rate
- Hallucinated API rate
- Number of repair iterations
- Time to successful solution
- Tokens used
- Retrieval tokens used
- Inference latency
- Peak RAM usage
- Peak GPU/unified memory usage

## Quality Metrics

Where automated evaluation is insufficient:

- Idiomatic Embabel usage
- Code maintainability
- Architectural quality
- Explanation accuracy
- Unnecessary complexity
- Spring best-practice adherence

Human review should be used sparingly and preferably against a clear rubric.

---

# Phase 4 — Synthetic Dataset Generation

The Embabel source tree can be used to generate training tasks.

## Dataset Generation Pipeline

```text
Embabel source/examples/tests
            |
            v
Identify canonical pattern
            |
            v
Generate task variants
            |
            +--> feature request
            +--> bug injection
            +--> refactoring request
            +--> planner reasoning task
            +--> transformation task
            |
            v
Generate candidate answer
            |
            v
Compile + test + execute
            |
            v
Keep only verified examples
            |
            v
Training dataset
```

A frontier model may be used to propose synthetic tasks and candidate solutions, but automatically verified examples should be strongly preferred.

---

# Training Data Format

A simple JSONL format can be used initially.

Example:

```json
{
  "id": "action-001",
  "category": "generation",
  "instruction": "Create an Embabel action that takes a Customer and produces a CreditAssessment.",
  "context": "Relevant framework/API context...",
  "answer": "Verified implementation...",
  "verification": {
    "compiled": true,
    "tests_passed": true
  }
}
```

Conversation-style formats can be generated later for the selected training framework.

---

# Phase 5 — LoRA / QLoRA

Do not fine-tune until the baseline and RAG benchmark results are understood.

Fine-tuning should answer a specific question:

> What behavior is missing after the model has access to high-quality retrieval?

Good fine-tuning targets include:

- Embabel idioms
- Planner reasoning patterns
- Action decomposition
- Goal modeling
- Framework-specific debugging
- Transformation from imperative Spring code
- Repeated framework error patterns

Avoid using LoRA merely to memorize documentation that should come from retrieval.

---

# Controlled Experiment

The primary experiment should compare four configurations using the exact same benchmark:

| Configuration | Base Model | Embabel Retrieval | LoRA |
|---|---|---|---|
| A | Yes | No | No |
| B | Yes | Yes | No |
| C | Yes | No | Yes |
| D | Yes | Yes | Yes |

This allows measurement of:

- Base model capability
- Retrieval contribution
- Fine-tuning contribution
- Retrieval + specialization interaction

---

# Example Hypotheses

## H1

Embabel RAG will significantly reduce hallucinated APIs and improve compile success.

## H2

LoRA specialization will provide more improvement on planner reasoning and idiomatic framework usage than on simple API recall.

## H3

RAG + LoRA will outperform either technique independently.

## H4

A specialized 14B model may outperform a much larger generic coding model on Embabel-specific tasks.

## H5

Compiler/test feedback can generate a high-quality synthetic training dataset with less manual annotation.

---

# Hardware Target

Initial development target:

- AMD Ryzen AI Max+ 395
- 128 GB unified LPDDR5X memory
- Linux
- ROCm-supported environment
- Fast NVMe storage

The system should be treated as an experimentation workstation rather than a platform for training foundation models from scratch.

Expected useful workloads:

- Local inference
- Embedding generation
- RAG
- Benchmark execution
- Dataset generation
- LoRA training
- QLoRA training
- Agent evaluation
- Automated compile/test loops

Initial training work should focus on 7B and 14B models.

32B models can be explored after the pipeline is stable.

---

# Software Stack

Potential components:

## Model Runtime

- Ollama
- llama.cpp
- vLLM
- Hugging Face Transformers
- ROCm-compatible PyTorch

The initial project should avoid unnecessary coupling to one runtime.

## Fine-Tuning

Candidate tools:

- Hugging Face Transformers
- PEFT
- TRL
- bitsandbytes where supported
- Axolotl
- Unsloth where hardware/runtime support is appropriate

Tool choice should be validated against ROCm support before committing.

## Retrieval

Possible components:

- Spring AI
- Embedding model
- Vector store
- Reranker
- Source-code-aware chunking

A simple local stack should be preferred for the first version.

---

# Proposed Repository Structure

```text
embabel-slm/
├── README.md
├── LICENSE
├── docs/
│   ├── research-plan.md
│   ├── benchmark-design.md
│   ├── dataset-design.md
│   ├── hardware.md
│   └── experiments.md
│
├── benchmark/
│   ├── tasks/
│   │   ├── generation/
│   │   ├── repair/
│   │   ├── planning/
│   │   ├── transformation/
│   │   ├── refactoring/
│   │   └── integration/
│   ├── fixtures/
│   ├── expected/
│   └── runner/
│
├── rag/
│   ├── ingestion/
│   ├── chunking/
│   ├── embeddings/
│   ├── retrieval/
│   └── evaluation/
│
├── datasets/
│   ├── raw/
│   ├── generated/
│   ├── verified/
│   └── splits/
│
├── training/
│   ├── configs/
│   ├── lora/
│   ├── qlora/
│   └── scripts/
│
├── evaluation/
│   ├── compile/
│   ├── tests/
│   ├── planner/
│   ├── metrics/
│   └── reports/
│
├── models/
│   └── README.md
│
├── experiments/
│   ├── baseline/
│   ├── rag/
│   ├── lora/
│   └── rag-lora/
│
└── tools/
    ├── task-generator/
    ├── bug-injector/
    ├── verifier/
    └── result-analyzer/
```

---

# First Milestone

Do not begin with fine-tuning.

The first milestone should be:

> Build a reproducible benchmark capable of evaluating a local coding model against real Embabel projects.

## Milestone 1 Tasks

1. Select one candidate local coding model.
2. Install and validate local inference on the AMD Halo system.
3. Clone/pin an Embabel version.
4. Create 20 initial benchmark tasks.
5. Build an isolated compile/test runner.
6. Record baseline results.
7. Add Embabel documentation/source retrieval.
8. Re-run exactly the same tasks.
9. Compare results.
10. Expand benchmark to 100 tasks.

Only after this should LoRA experiments begin.

---

# Initial 20-Task Benchmark

Suggested first task set:

1. Create a simple `@Action`.
2. Create an action with two required inputs.
3. Produce a domain object from an action.
4. Define a simple goal.
5. Create a two-step reachable plan.
6. Diagnose an unreachable goal.
7. Fix a missing action dependency.
8. Fix incorrect action annotations.
9. Write an action unit test.
10. Configure Embabel in a Spring Boot application.
11. Convert a Spring service method into an Embabel action.
12. Split one large action into three actions.
13. Add a condition controlling action eligibility.
14. Diagnose why an action cannot execute.
15. Refactor manual orchestration into planner-driven logic.
16. Add persistence to an Embabel workflow.
17. Create a REST endpoint triggering an Embabel agent.
18. Repair a Spring-context startup failure.
19. Explain the plan that should satisfy a specified goal.
20. Build a small complete Embabel application from a written requirement.

---

# Reproducibility

Every experiment should record:

- Date
- Git commit
- Embabel version
- Base model
- Model hash/revision
- Quantization
- Runtime
- Runtime version
- Prompt template
- Retrieval configuration
- LoRA adapter version
- Temperature
- Seed where applicable
- Context size
- Hardware
- ROCm version
- Test results
- Raw model output

Do not overwrite experiment results.

---

# Model Versioning

A useful naming scheme:

```text
embabel-slm-<base>-<size>-<stage>-<version>
```

Examples:

```text
embabel-slm-qwen-14b-baseline-v0
embabel-slm-qwen-14b-rag-v1
embabel-slm-qwen-14b-lora-v1
embabel-slm-qwen-14b-rag-lora-v1
```

---

# Data Leakage Rules

Benchmark tasks must never be included directly in training data.

Maintain separate directories for:

- training
- validation
- benchmark/test

Synthetic variations of benchmark tasks should be checked for near-duplication before training.

---

# Success Criteria

A specialized model should demonstrate measurable improvement over its own base model.

Possible initial success targets:

- Higher compile pass rate
- Higher full-test pass rate
- Lower hallucinated API rate
- Better planner success
- Fewer repair iterations
- Comparable or better Embabel task success than a substantially larger generic model

The project should not claim "expert-level" behavior without a clearly defined benchmark and reproducible results.

---

# Long-Term Research Directions

Potential future experiments:

## Framework Transfer

Test whether an Embabel-specialized model loses or retains general Spring ability.

## Multi-Framework Specialization

Compare:

- Spring-only adapter
- Embabel-only adapter
- Spring + Embabel adapter

## Adapter Composition

Explore separate adapters for:

- Spring
- Embabel
- Security
- Persistence
- Testing

## Continual Framework Updates

Determine whether RAG can absorb Embabel version changes without retraining the LoRA adapter.

## Distillation

Use a larger model as a teacher for a smaller local model.

## Self-Repair

Allow the model to:

1. Generate code
2. Compile
3. Read the failure
4. Repair
5. Repeat

Measure how specialization affects the number of repair cycles.

## Agentic Evaluation

Allow the local model to modify an actual repository rather than answering isolated prompts.

## Repository-Level Reasoning

Test whether the specialized model can understand a real multi-module Embabel/Spring application.

---

# Preprint track (Nov 2026 – Mar 2027)

Ship a citable Zenodo preprint by **31 March 2027** that proves or disproves usefulness of the local coding SLM under the layered MCP evaluation contract, plus Embabel base-vs-retrieval (M1–M3). Optional M4/M5 inside the window only if numbers freeze by late February. Full production (M6–M7) stays after the DOI.

- Calendar and venue: [paper-calendar-2026.md](paper-calendar-2026.md)
- Citations: [citation-workflow.md](citation-workflow.md)
- Outline / claim freeze: [paper/outline.md](paper/outline.md)

---

# Near-Term Implementation Plan

## Step 1

Create the repository and commit this document.

## Step 2

Pin a specific Embabel release/commit for the first benchmark.

## Step 3

Choose one 7B–14B coding model as the initial baseline.

## Step 4

Build a CLI benchmark runner.

Example concept:

```bash
./run-benchmark \
  --model local-model \
  --suite benchmark/tasks \
  --embabel-version <pinned-version> \
  --output experiments/baseline/run-001
```

## Step 5

Implement compile/test verification.

## Step 6

Add source/document RAG.

## Step 7

Run the controlled baseline-vs-RAG experiment.

## Step 8

Design the synthetic-data pipeline.

## Step 9

Generate and automatically verify the first 500 training examples.

## Step 10

Run the first LoRA/QLoRA experiment.

---

# Guiding Principle

Do not start by asking:

> How do we fine-tune a model on Embabel?

Start by asking:

> What does a generic coding model fail at when working with Embabel, and what is the cheapest reliable intervention that fixes that failure?

The intervention might be:

- better prompting,
- better retrieval,
- better tool feedback,
- LoRA specialization,
- or some combination.

The purpose of `embabel-slm` is to measure those differences rather than assume training is always the answer.
