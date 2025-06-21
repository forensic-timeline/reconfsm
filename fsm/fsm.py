#!/usr/bin/env python3

"""
FSM Simulator Program

Usage:
    python fsm_simulator.py <json_file> graph
    python fsm_simulator.py <json_file> pathfinding -s <state_name> -d <depth>
"""

import sys
import json
import os
from transitions.extensions import GraphMachine
from pathfinding import pathfinding_simulation
from graph import graph_simulation


class FSMachine:
    def __init__(self, name, states, transitions, functions, initial_state):
        self.name = name
        self.states = states
        self.initial_state = initial_state
        self.transitions_data = transitions
        self.machine = GraphMachine(
            model=self,
            states=states,
            initial=initial_state,
            auto_transitions=True,
            show_conditions=True
        )

        for transition in transitions:
            trigger = transition["trigger"]
            source = transition["source"]
            dest = transition["dest"]
            self.machine.add_transition(trigger, source, dest)


def load_machine_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for category, machines in data.items():
        if isinstance(machines, list) and len(machines) > 0:
            machine_config = machines[0]
            break

    name = machine_config.get("name")
    initial_state = machine_config.get("initial_state")
    states = machine_config.get("states")
    transitions = machine_config.get("transitions")
    functions = machine_config.get("functions", {})

    return FSMachine(name, states, transitions, functions, initial_state)


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python fsm_simulator.py <json_file> <simulation_type> [options]")
        sys.exit(1)

    json_file = sys.argv[1]

    if not os.path.exists(json_file):
        print(f"Error: JSON file '{json_file}' not found")
        sys.exit(1)

    try:
        machine = load_machine_from_json(json_file)
    except Exception as e:
        print(f"Error loading machine: {e}")
        sys.exit(1)

    simulations = sys.argv[2:]

    i = 0
    while i < len(simulations):
        sim_type = simulations[i]

        if sim_type == 'graph':
            graph_simulation(machine)
            i += 1

        elif sim_type == 'pathfinding':
            if i + 4 >= len(simulations) or simulations[i+1] != '-s' or simulations[i+3] != '-d':
                print("Error: pathfinding requires -s <state_name> -d <depth>")
                sys.exit(1)

            state_name = simulations[i+2]
            try:
                depth = int(simulations[i+4])
            except ValueError:
                print("Error: depth must be an integer")
                sys.exit(1)

            pathfinding_simulation(machine, state_name, depth)
            i += 5

        else:
            print(f"Error: Unknown simulation type '{sim_type}'")
            print("Available types: graph, pathfinding")
            sys.exit(1)


if __name__ == "__main__":
    main()
