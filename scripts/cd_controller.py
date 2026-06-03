#!/usr/bin/env python3
"""
CD Orchestration Tool: State Reconciliation Engine.
Supports one-shot execution or active runtime checking via the --watch flag.
"""

import logging
import os
import sys
import time
from typing import Optional
import docker
from docker.models.containers import Container
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("Orchestrator")

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
try:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
except Exception as e:
    logger.critical(f"Failed to load config.yaml: {e}")
    sys.exit(1)

REPO_NAME = config["project"]["repo_name"]
NODE_NAME = config["deployment"]["node_name"]
INTERVAL = config["runtime"]["scan_interval"]
MEM_LIMIT = config["deployment"]["mem_limit"]
CPU_LIMIT = int(config["deployment"]["cpu_limit"] * 1e9)  # Convert to nano_cpus


def find_highest_local_version(client: docker.DockerClient, repo: str) -> str:
    """Finds the absolute latest version tag built on disk cache."""
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
    if highest_version == 0:
        logger.critical(f"No versioned images found for {repo}.")
        sys.exit(1)
    return f"v{highest_version}"

def get_running_container_version(client: docker.DockerClient, name: str) -> Optional[str]:
    """Inspects the exact configuration tag used to spin up the container instance."""
    try:
        container: Container = client.containers.get(name)
        
        # This reaches into the immutable creation blueprint config of this exact process.
        # It returns exactly what you ran, e.g., "local-python-logger:v5"
        launched_image_string = container.attrs['Config']['Image']
        
        # Safely parse out just the version suffix
        if ":" in launched_image_string:
            return launched_image_string.split(":")[-1]
            
        return launched_image_string
    except docker.errors.NotFound:
        return None

def deploy_new_version(client: docker.DockerClient, repo: str, target_version: str, name: str) -> None:
    """Drops the outdated container and scales up the target version seamlessly."""
    full_image_string = f"{repo}:{target_version}"
    try:
        old_container = client.containers.get(name)
        logger.info(f"  [Reconcile] Tearing down old instance: {name}...")
        old_container.stop(timeout=2)
        old_container.remove()
    except docker.errors.NotFound:
        pass

    logger.info(f"  [Reconcile] Spawning container from layer: {full_image_string}")
    client.containers.run(
        image=full_image_string,
        name=name,
        detach=True,
        mem_limit=MEM_LIMIT,
        nano_cpus=CPU_LIMIT
    )
    logger.info(f"  [Success] Node {name} promoted to version [{target_version}].")


def reconcile_state(client: docker.DockerClient) -> None:
    """Compares running version state against target disk version state."""
    target_version = find_highest_local_version(client, REPO_NAME)
    current_version = get_running_container_version(client, NODE_NAME)

    if current_version is None:
        logger.info(f"Node '{NODE_NAME}' missing. Reconciling to baseline [{target_version}]...")
        deploy_new_version(client, REPO_NAME, target_version, NODE_NAME)
    elif current_version != target_version:
        logger.warning(f"State drift caught on '{NODE_NAME}'! Running:[{current_version}] -> Target:[{target_version}]")
        deploy_new_version(client, REPO_NAME, target_version, NODE_NAME)


def main() -> None:
    watch_mode = "--watch" in sys.argv
    
    try:
        client = docker.from_env()
    except Exception as e:
        logger.critical(f"Failed to bind daemon socket: {e}")
        sys.exit(1)

    if watch_mode:
        logger.info(f"Orchestrator running in DAEMON mode (Polling runtime state every {INTERVAL}s)...")
        try:
            while True:
                reconcile_state(client)
                time.sleep(INTERVAL)
        except KeyboardInterrupt:
            logger.info("Orchestrator daemon stopped cleanly.")
    else:
        logger.info("Orchestrator running in ONE-SHOT mode...")
        reconcile_state(client)


if __name__ == "__main__":
    main()
