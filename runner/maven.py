"""Materialize and compile isolated Maven projects."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from runner.config import (
    EMBABEL_API_ARTIFACT,
    EMBABEL_API_VERSION,
    EMBABEL_GROUP,
)

POM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.embabel.benchmark</groupId>
  <artifactId>score-task</artifactId>
  <version>0.0.1-SNAPSHOT</version>
  <properties>
    <maven.compiler.release>21</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <junit.version>5.11.4</junit.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>{group}</groupId>
      <artifactId>{artifact}</artifactId>
      <version>{version}</version>
    </dependency>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>${{junit.version}}</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.5.2</version>
      </plugin>
    </plugins>
  </build>
</project>
"""


@dataclass
class CompileResult:
    ok: bool
    output: str
    hallucinated: bool
    first_error: str


HALLU_RE = re.compile(
    r"cannot find symbol|package com\.embabel\.[\w.]+ does not exist|symbol:\s+class\s+\w+",
    re.IGNORECASE,
)


def materialize_project(work_root: Path, files: dict[str, str], *, with_tests: bool) -> Path:
    project = work_root / "project"
    if project.exists():
        shutil.rmtree(project)
    project.mkdir(parents=True)
    pom = POM_TEMPLATE.format(
        group=EMBABEL_GROUP,
        artifact=EMBABEL_API_ARTIFACT,
        version=EMBABEL_API_VERSION,
    )
    (project / "pom.xml").write_text(pom, encoding="utf-8")
    for rel, content in files.items():
        target = project / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return project


def run_maven(project: Path, goal: str, local_repo: Path) -> CompileResult:
    if shutil.which("mvn") is None:
        return CompileResult(False, "", False, "mvn not found on PATH")
    env = os.environ.copy()
    cmd = [
        "mvn",
        "-q",
        f"-Dmaven.repo.local={local_repo}",
        "-f",
        str(project / "pom.xml"),
        goal,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False, timeout=600)
    text = (proc.stdout or "") + (proc.stderr or "")
    ok = proc.returncode == 0
    hallucinated = bool(HALLU_RE.search(text)) and not ok
    first = ""
    for line in text.splitlines():
        if "[ERROR]" in line or "error:" in line.lower():
            first = line.strip()
            break
    if not first and not ok:
        first = f"mvn exit {proc.returncode}"
    return CompileResult(ok, text, hallucinated, first)


def compile_tree(files: dict[str, str], *, with_tests: bool, cache_dir: Path) -> CompileResult:
    cache_dir.mkdir(parents=True, exist_ok=True)
    local_repo = cache_dir / "m2"
    local_repo.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="embabel-score-") as tmp:
        work = Path(tmp)
        project = materialize_project(work, files, with_tests=with_tests)
        compile_goal = "test" if with_tests else "compile"
        return run_maven(project, compile_goal, local_repo)