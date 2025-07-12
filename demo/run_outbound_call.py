#!/usr/bin/env python3
"""
Script to execute LiveKit dispatch commands from JSON configuration
"""

import json
import subprocess
import sys
import argparse


def load_config(json_file):
    """Load configuration from JSON file"""
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{json_file}': {e}")
        sys.exit(1)


def build_command(config):
    """Build the LiveKit dispatch command from configuration"""
    command = ["lk", "dispatch", "create"]
    
    options = config.get("options", {})
    
    # Add flags
    if options.get("new-room"):
        command.append("--new-room")
    
    # Add agent name
    if "agent-name" in options:
        command.extend(["--agent-name", options["agent-name"]])
    
    # Add metadata
    if "metadata" in options:
        metadata_json = json.dumps(options["metadata"])
        command.extend(["--metadata", metadata_json])
    
    return command


def execute_command(command):
    """Execute the LiveKit dispatch command"""
    try:
        print(f"Executing: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Command executed successfully!")
        print("Output:", result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print("Error output:", e.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Execute LiveKit dispatch commands from JSON")
    parser.add_argument("json_file", help="Path to JSON configuration file")
    parser.add_argument("--dry-run", action="store_true", help="Show command without executing")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.json_file)
    
    # Build command
    command = build_command(config)
    
    if args.dry_run:
        print("Command that would be executed:")
        print(" ".join(command))
    else:
        # Execute command
        execute_command(command)


if __name__ == "__main__":
    main() 