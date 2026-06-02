# Micro-CICD-Docker

A lightweight, local-first CI/CD prototype
 that demonstrates automated container builds and state reconciliation using Python and Docker.

## Features
- **CI Engine (`scripts/ci_engine.py`):** Monitors source files (`src/app.py`, `deploy/Dockerfile`) and automatically builds new versioned images upon mutation using SHA-256 fingerprinting.

## Quick Start

1. **Setup Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install .
   ```

2. **Run the CI Engine (Watch Mode):**
   ```bash
   python3 scripts/ci_engine.py --watch
   ```

## Architecture
This project follows **GitOps** principles. The `ci_engine` acts as the build pipeline.
