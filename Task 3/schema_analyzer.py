import json
import os
import sys
import glob
from typing import Dict, Any, List
from pprint import pprint
import argparse


# Recursively analyze JSON structure to determine schema
def analyze_json_structure(json_data, parent_key=""):
    if isinstance(json_data, dict):
        return {
            k: analyze_json_structure(v, f"{parent_key}.{k}" if parent_key else k)
            for k, v in json_data.items()
        }
    elif isinstance(json_data, list) and json_data:
        # check the first item in the list
        sample = json_data[0]
        # If list contains primitive types, just show the type
        if isinstance(sample, (str, int, float, bool)) or sample is None:
            return f"List[{type(sample).__name__}]"
        # else recursively analyze the structure
        return [analyze_json_structure(sample, f"{parent_key}[0]")]
    else:
        return type(json_data).__name__


# function to print the schema as output
def print_schema(schema, indent=0):
    if isinstance(schema, dict):
        for key, value in schema.items():
            if isinstance(value, dict):
                print(f"{' ' * indent}{key}:")
                print_schema(value, indent + 4)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                print(f"{' ' * indent}{key}: [Array of Objects]")
                print_schema(value[0], indent + 4)
            else:
                print(f"{' ' * indent}{key}: {value}")
    elif isinstance(schema, list) and schema:
        print(f"{' ' * indent}[Array Items]:")
        print_schema(schema[0], indent + 4)
    else:
        print(f"{' ' * indent}{schema}")


# analyze + print a single JSON file
def analyze_json_file(file_path):
    print(f"\n{'=' * 80}")
    print(f"Analyzing {os.path.basename(file_path)}:")
    print(f"{'=' * 80}")

    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        structure = analyze_json_structure(data)
        print("\nSchema Structure:")
        print_schema(structure)

        if isinstance(data, dict):
            print(f"\nTop-level keys: {len(data)}")
        elif isinstance(data, list):
            print(f"\nArray length: {len(data)}")
            if data and isinstance(data[0], dict):
                print(f"First item keys: {len(data[0])}")

        print(f"\n{'-' * 80}")
        return structure

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def find_json_files(search_paths):
    """Find JSON files in the given search paths."""
    found_files = []

    for path in search_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                print(f"Searching for JSON files in {path}...")
                json_files = [f for f in os.listdir(path) if f.endswith(".json")]
                found_files.extend([os.path.join(path, f) for f in json_files])
            elif path.endswith(".json"):
                found_files.append(path)

    return found_files


def main():
    parser = argparse.ArgumentParser(description="Analyze JSON file structures")
    parser.add_argument(
        "--data-dir", help="Directory containing JSON files", default=None
    )
    parser.add_argument("--file", help="Single JSON file to process", default=None)
    args = parser.parse_args()

    # added all possible search paths
    # this was done because I was finding error while specifying the path manually
    search_paths = [
        args.data_dir if args.data_dir else None,
        args.file if args.file else None,
        os.path.join("..", "Data", "Modified Data"),
        os.path.join("Data", "Modified Data"),
        os.path.join("..", "Modified Data"),
        os.path.join("Modified Data"),
        os.path.join("..", "Data"),
        os.path.join("Data"),
        os.path.join("."),  # Current directory
    ]

    # Remove None values
    search_paths = [p for p in search_paths if p]

    # Absolute path to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Add absolute paths
    search_paths.extend(
        [
            os.path.join(project_root, "Data", "Modified Data"),
            os.path.join(project_root, "Modified Data"),
            os.path.join(project_root, "Data"),
        ]
    )

    # Find JSON files
    json_files = find_json_files(search_paths)

    if not json_files:
        print(
            "No JSON files found! Please specify a correct path using --data-dir or --file"
        )
        print("Tried searching in:")
        for path in search_paths:
            print(f"  - {path}")
        return

    print(f"Found {len(json_files)} JSON files to process")

    # Analyze each file
    for file_path in json_files:
        analyze_json_file(file_path)


if __name__ == "__main__":
    main()
