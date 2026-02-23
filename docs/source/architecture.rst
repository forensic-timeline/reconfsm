Architecture
============

This page describes the internal design and data flow of **ReconFSM**.

High-Level Design
-----------------

ReconFSM is partitioned into three main logical components:

1.  **Converter Layer**: Extracts forensic artifacts and defines the FSM logic.
2.  **Logic Engine**: Manages states, triggers, and graph traversals.
3.  **Visualization Layer**: Provides both static and interactive views.

.. code-block:: text

   [ Plaso CSV ] --> [ Converter ] --> [ FSM JSON ] --> [ FSM Engine / Visualizer ]

Data Flow
---------

1. Conversion (CSV to JSON)
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``converter.py`` script reads the CSV file row by row. It uses a **provider pattern**—dynamically loading a specific script based on the desired activity type.
*   The script determines the current state based on the log entry.
*   It records the previous state to establish a transition.
*   A set of unique states and transitions is compiled into a JSON object.

2. State Management
^^^^^^^^^^^^^^^^^^^
ReconFSM uses the ``transitions`` Python library. This allows for:
*   Standardized FSM definitions.
*   Simulation of event sequences.
*   Validation of state-to-state movement.

3. Serialization
^^^^^^^^^^^^^^^^
The intermediate data format is a JSON file. This ensures that the conversion (heavy processing) and the visualization (rendering) are decoupled. You can convert on a powerful forensic workstation and visualize on a laptop.

Detailed Component View
-----------------------

Converter
^^^^^^^^^
Located in ``reconfsm/converter/``.
*   ``converter.py``: Orchestrates the reading of CSV and writing of JSON.
*   ``scripts/``: A directory of "plug-ins" that contain the forensic logic for parsing different event types.

FSM Engine
^^^^^^^^^^
Located in ``reconfsm/fsm/``.
*   ``fsm.py``: Command-line interface for the engine.
*   ``graph.py``: Wrapper for Graphviz to generate DOT and PNG files.
*   ``pathfinding.py``: Recursive algorithm for discovering paths in the state graph.

Visualizer
^^^^^^^^^^
Located in ``reconfsm/visualizer/``.
A client-side JavaScript application using **Cytoscape.js** for high-performance graph rendering.
