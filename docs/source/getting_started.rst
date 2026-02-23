Getting Started
===============

This tutorial will walk you through a complete workflow using **ReconFSM**, from raw logs to an interactive visualization.

Prerequisites
-------------

Ensure you have completed the :doc:`installation` steps. For this tutorial, we will use the sample data provided in the repository.

1. Prepare Your Data
--------------------

In a real scenario, you would use **Plaso** to extract logs from a disk image. For this tutorial, we will use the pre-extracted CSV file: ``test_data/csv/web_activity.csv``.

This file contains timeline entries extracted from a browser's history and download logs.

2. Convert CSV to FSM JSON
--------------------------

The first step is to transform the flat CSV timeline into a state machine structure. We use the ``converter.py`` script for this.

.. code-block:: bash

   # Navigate to the converter directory
   cd reconfsm/converter

   # Run the conversion
   python converter.py ../../test_data/csv/web_activity.csv web_activity

**What happened?**
The script parsed the CSV, identified "web_activity" patterns, and generated a JSON file in ``reconfsm/converter/json_machines/web_activity/``.

3. Generate a Static Graph
--------------------------

Now let's visualize the FSM states and transitions as a static image.

.. code-block:: bash

   # Navigate to the fsm directory
   cd ../fsm

   # Find the generated JSON (it has a timestamp in the name)
   # Run the graph generation
   python fsm.py ../converter/json_machines/web_activity/web_activity_YYYYMMDD_HHMMSS.json graph

This will create a PNG image in the ``result/`` directory showing the flow of web activities.

4. Perform Pathfinding Analysis
-------------------------------

ReconFSM can help you find how a user reached a specific state.

.. code-block:: bash

   python fsm.py ../converter/json_machines/web_activity/web_activity_YYYYMMDD_HHMMSS.json pathfinding -s "Web : google.com" -d 5

This command searches for all paths (up to depth 5) that lead to the state "Web : google.com".

5. Interactive Visualization
----------------------------

For the best experience, use the web-based visualizer:

1.  Open ``reconfsm/visualizer/index.html`` in any modern web browser.
2.  Click **"Choose File"** and select the JSON file generated in step 2.
3.  Interact with the graph: drag nodes, zoom in/out, and change layouts.

Summary
-------

You have now:
*   Converted forensic logs into an FSM.
*   Generated a visual representation.
*   Performed automated pathfinding analysis.
*   Explored the data interactively.

Next Steps
----------
*   Read more about :doc:`activity_types` to see what else you can reconstruct.
*   Check the :doc:`usage` page for advanced command-line options.
