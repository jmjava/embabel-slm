"""Pinned framework coordinates and runner constants."""

from __future__ import annotations

EMBABEL_REPO = "embabel/embabel-agent"
EMBABEL_COMMIT = "3b9b74f494cb"
# Parent POM at the pin is 1.5.5-SNAPSHOT (not on public repos). Closest release on Central:
EMBABEL_GROUP = "com.embabel.agent"
EMBABEL_API_ARTIFACT = "embabel-agent-api"
EMBABEL_API_VERSION = "1.5.4"
MAVEN_REPO_URL = "https://repo1.maven.org/maven2"

SYSTEM_PROMPT = """You are an Embabel JVM coding assistant.
Respond with one or more fenced code blocks. Each block must use a path label on the fence, e.g.
```java src/main/java/demo/Greeter.java
...
```
Use only APIs that exist on the pinned Embabel agent version. Do not invent types or packages.
"""

OLLAMA_URL = "http://127.0.0.1:11434"