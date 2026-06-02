#!/usr/bin/env python3
"""
CI Pipeline Tool: Change Detection Builder.
Supports one-shot execution or infinite filesystem watching via the --watch flag.
"""

import hashlib
import json
import logging
import os
import sys
import time
from typing import List
import docker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("SmartBuilder")

REPO_NAME = "local-python-logger"
STATE_MEMO_FILE = ".build_memo.json"
TRACKED_FILES = ["deploy/Dockerfile", "src/app.py"]
INTERVAL = 5  # Scan filesystem every 5 seconds in watch mode


def get_project_fingerprint(files: List[str]) -> str:
    """Generates a combined SHA-256 hash of all tracked files."""
    hasher = hashlib.sha256()
    for file_path in sorted(files):
        # Resolve path relative to project root
        absolute_path = os.path.join(os.path.dirname(__file__), "..", file_path)
        if os.path.exists(absolute_path):
            with open(absolute_path, "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
    return hasher.hexdigest()


def load_previous_signature() -> str:
    """Reads the last recorded successful build fingerprint from disk."""
    memo_path = os.path.join(os.path.dirname(__file__), "..", STATE_MEMO_FILE)
    if os.path.exists(memo_path):
        try:
            with open(memo_path, "r") as f:
                return json.load(f).get("signature", "")
        except (json.JSONDecodeError, IOError):
            return ""
    return ""


def save_current_signature(signature: str, version: str) -> None:
    """Commits the verified build signature to disk."""
    memo_path = os.path.join(os.path.dirname(__file__), "..", STATE_MEMO_FILE)
    try:
        with open(memo_path, "w") as f:
            json.dump({"signature": signature, "version": version}, f, indent=2)
    except IOError as e:
        logger.warning(f"Failed to record build memo state: {e}")


def calculate_next_version(client: docker.DockerClient, repo: str) -> str:
    """Audits local storage to find the next sequential version string."""
    existing_images = client.images.list(name=repo)
    highest_version = 0
    for img in existing_images:
        if not img.tags:
            continue
        for tag in img.tags:
            tag_version = tag.split(":")[-1]
            if tag_version.startswith("v") and tag_version[1:].isdigit():
                v_num = int(tag_version[1:])
                if v_num > highest_version:
                    highest_version = v_num
    return f"v{highest_version + 1}"


def run_build_cycle(client: docker.DockerClient) -> None:
    """Evaluates the filesystem context and triggers a build if mutated."""
    current_sig = get_project_fingerprint(TRACKED_FILES)
    prev_sig = load_previous_signature()

    if current_sig == prev_sig:
        logger.debug("No code changes detected.")
        return

    logger.info("Source modifications detected! Initiating build sequence...")
    next_version = calculate_next_version(client, REPO_NAME)
    target_tag = f"{REPO_NAME}:{next_version}"
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dockerfile_path = os.path.join(project_root, "deploy/Dockerfile")
    
    try:
        image, _ = client.images.build(
            path=project_root, 
            dockerfile=dockerfile_path, 
            tag=target_tag, 
            rm=True
        )
        save_current_signature(current_sig, next_version)
        logger.info(f"Successfully minted image: {target_tag} (ID: {image.short_id})")
    except docker.errors.BuildError as err:
        logger.critical(f"Compilation pipeline broken: {err}")


def main() -> None:
    watch_mode = "--watch" in sys.argv
    
    try:
        client = docker.from_env()
    except Exception as e:
        logger.critical(f"Docker socket unavailable: {e}")
        sys.exit(1)

    if watch_mode:
        logger.info(f"Smart Builder running in DAEMON mode (Scanning files every {INTERVAL}s)...")
        try:
            while True:
                run_build_cycle(client)
                time.sleep(INTERVAL)
        except KeyboardInterrupt:
            logger.info("Builder daemon stopped cleanly.")
    else:
        logger.info("Smart Builder running in ONE-SHOT mode...")
        run_build_cycle(client)


if __name__ == "__main__":
    main()
