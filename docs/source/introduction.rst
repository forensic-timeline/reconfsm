Introduction
============

Overview
--------

**ReconFSM** is a specialized digital forensics toolkit designed to bridge the gap between raw timeline logs and meaningful behavioral analysis. In modern digital investigations, analysts often deal with thousands or millions of log entries stored in formats like Plaso Storage or CSV files. Understanding the sequence of events and the causal relationships between them can be incredibly challenging.

ReconFSM solves this problem by applying the concept of **Finite State Machines (FSM)** to forensic data. By modeling system behavior as a series of states and transitions, it allows investigators to:

*   **Visualize user behavior**: See how a user moved from browsing a website to downloading a file and then launching an application.
*   **Identify anomalies**: Spot unusual state transitions that might indicate malicious activity or unauthorized access.
*   **Pathfinding Analysis**: Automatically find all possible paths to a specific "end state" (e.g., a system shutdown or a specific file access).
*   **Interactive Exploration**: Use a web-based visualizer to zoom, filter, and interact with the reconstructed timeline.

Key Features
------------

*   **Automated Conversion**: Convert Plaso-generated CSV timelines directly into FSM JSON models.
*   **Flexible Extraction**: Built-in support for multiple activity types (Web, Application, System Shutdown).
*   **Extensible Architecture**: Easily add new activity extraction scripts to support different log formats or forensic artifacts.
*   **Simulation Engine**: A robust backend that simulates FSM transitions and provides pathfinding capabilities.
*   **Modern Visualization**: A sleek, interactive web interface for exploring generated machines.

How it Works
------------

The ReconFSM pipeline generally follows these steps:

1.  **Data Acquisition**: Extract low-level artifacts from a disk image using tools like **Plaso** (log2timeline).
2.  **Conversion**: Run the ReconFSM converter to parse the CSV logs and generate an FSM JSON file based on specific activity logic.
3.  **Analysis**: Use the FSM simulation tool to generate static graphs or perform pathfinding analysis.
4.  **Visualization**: Load the JSON into the Interactive Visualizer for a dynamic view of the reconstructed events.

Why Finite State Machines?
--------------------------

Digital forensics is fundamentally about reconstructing the "state" of a system at a given point in time. By formalizing these states and the actions (triggers) that cause transitions between them, we can apply mathematical graph theory to forensic investigations. This enables more rigorous analysis than simply scrolling through a text-based timeline.
