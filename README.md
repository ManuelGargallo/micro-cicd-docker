# Micro-CICD-Docker

A lightweight, local-first CI/CD prototype
 that demonstrates automated container builds and state reconciliation using Python and Docker.

## Features
- **CI Engine (`scripts/ci_engine.py`):** Monitors source files (`src/app.py`, `deploy/Dockerfile`) and automatically builds new versioned images upon mutation using SHA-256 fingerprinting.
- **CD Controller (`scripts/cd_controller.py`):** A reconciliation loop that ensures the running container matches the latest built image on disk.

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

3. **Run the CD Controller (Watch Mode):**
   ```bash
   python3 scripts/cd_controller.py --watch
   ```

## Architecture
This project follows **GitOps** principles. The `ci_engine` acts as the build pipeline (Continuous Integration), while the `cd_controller` acts as the agent ensuring the "actual state" (running container) matches the "desired state" (latest local image), achieving **Continuous Deployment**.
