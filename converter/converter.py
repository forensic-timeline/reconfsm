#!/usr/bin/env python3
"""
CSV to State Machine Converter

A program that converts CSV files into state machine JSON configurations.
Takes command line arguments for the CSV file and extraction script type.

Usage:
    python convert.py <csv_file> <script_type>

Example:
    python convert.py data.csv web_activity
"""

import sys
import csv
import json
import os
import importlib.util
import time
from datetime import datetime

# ==== CONSTANTS ====
OUTPUT_DIR = "json_machines/"
SCRIPTS_DIR = "scripts/"
DELIMITER = ","


def load_script(script_type):
    script_file = os.path.join(SCRIPTS_DIR, f"{script_type}.py")

    if not os.path.exists(script_file):
        raise FileNotFoundError(f"Script file '{script_file}' not found")

    spec = importlib.util.spec_from_file_location(script_type, script_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    function_name = f"{script_type}"

    if not hasattr(module, function_name):
        raise AttributeError(
            f"Script '{script_file}' must contain a function named '{function_name}'")

    return getattr(module, function_name)


def get_available_scripts():
    if not os.path.exists(SCRIPTS_DIR):
        return []

    scripts = []
    for file in os.listdir(SCRIPTS_DIR):
        if file.endswith('.py') and not file.startswith('_'):
            script_name = file[:-3]
            scripts.append(script_name)

    return scripts


def extract_states_and_transitions(input_csv, extract_function):
    states = []
    transitions = set()
    previous_state = None
    allow_loop = extract_function.__name__ == "application_activity"
    if allow_loop:
        states.append("Desktop")
        previous_state = "Desktop"

    with open(input_csv, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=DELIMITER)

        for row in reader:
            extracted_data = extract_function(row)
            if not extracted_data:
                continue

            state, trigger, prev = extracted_data
            if prev is not None:
                previous_state = prev

            if state not in states:
                states.append(state)

            if allow_loop:
                if previous_state:
                    transitions.add((previous_state, state, trigger))
            else:
                if previous_state and previous_state != state:
                    transitions.add((previous_state, state, trigger))

            previous_state = state

    return states, sorted(transitions)


def generate_json(input_csv, output_dir, extract_function, prefix):
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_subdir = os.path.join(output_dir, prefix)
    os.makedirs(output_subdir, exist_ok=True)

    output_json = os.path.join(output_subdir, f"{prefix}_{current_time}.json")

    states, transitions = extract_states_and_transitions(
        input_csv, extract_function)

    unique_triggers = {trigger for _, _, trigger in transitions}

    json_data = {
        f"{prefix}_machine": [
            {
                "name": f"{prefix}_{current_time}",
                "initial_state": states[0] if states else "unknown",
                "states": states,
                "triggers": list(unique_triggers),
                "transitions": [{"trigger": trigger, "source": src, "dest": dst} for src, dst, trigger in transitions],
                "functions": {}
            }
        ]
    }

    with open(output_json, "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, indent=4)

    print(f"Conversion complete")


def main():
    if len(sys.argv) != 3:
        print("Error: Incorrect number of arguments")
        print()
        sys.exit(1)

    csv_file = sys.argv[1]
    script_type = sys.argv[2]
    available_scripts = get_available_scripts()

    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found")
        sys.exit(1)

    if script_type not in available_scripts:
        print(f"Error: Unknown script type '{script_type}'")
        sys.exit(1)

    try:
        start_time = time.time()  # Start timer

        extract_function = load_script(script_type)
        generate_json(csv_file, OUTPUT_DIR, extract_function, script_type)

        end_time = time.time()  # End timer
        duration = end_time - start_time
        print(f"Program completed in {duration:.2f} seconds.")

    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
