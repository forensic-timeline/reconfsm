Installation
============

This guide provides step-by-step instructions for setting up **ReconFSM** on your local machine.

System Requirements
-------------------

Before you begin, ensure your system meets the following requirements:

*   **Operating System**: Windows, macOS, or Linux.
*   **Python**: Version 3.12 or higher.
*   **Git**: Required for cloning the repository.
*   **Conda (Recommended)**: For isolated environment management.
*   **Docker**: Required if you plan to use Plaso for timeline extraction.

Step 1: Environment Setup
-------------------------

We highly recommend using a virtual environment to manage dependencies and avoid conflicts with other Python projects.

Using Conda (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Create a new environment
   conda create --name reconfsm python=3.12 -y

   # Activate the environment
   conda activate reconfsm

Using venv (Standard Library)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Create a virtual environment
   python -m venv .venv

   # Activate the environment (Windows)
   .venv\Scripts\activate

   # Activate the environment (macOS/Linux)
   source .venv/bin/activate

Step 2: Clone the Repository
----------------------------

Clone the ReconFSM project from GitHub:

.. code-block:: bash

   git clone https://github.com/forensic-timeline/reconfsm.git
   cd reconfsm

Step 3: Install Dependencies
----------------------------

Install the required Python packages using ``pip``:

.. code-block:: bash

   pip install -r requirements.txt

The core dependencies include:
*   **transitions**: The engine used for finite state machine logic.
*   **graphviz**: Used for generating static graph images (PNG/PDF).

Step 4: Verify Installation
---------------------------

To verify that everything is set up correctly, you can try running the converter script (note: use the correct path relative to root):

.. code-block:: bash

   python reconfsm/converter/converter.py --help

External Tool: Graphviz
-----------------------

To generate visual graphs, you must have the **Graphviz** binary installed on your system PATH.

*   **Windows**: Download and install from `graphviz.org <https://graphviz.org/download/>`_. During installation, make sure to select "Add Graphviz to the system PATH".
*   **macOS**: Install via Homebrew: ``brew install graphviz``.
*   **Linux**: Install via your package manager: ``sudo apt-get install graphviz``.

Troubleshooting
---------------

Common issues during installation:

*   **Python Version Mismatch**: If you see errors related to syntax or missing modules, ensure you are using Python 3.12+. Run ``python --version`` to check.
*   **Graphviz Not Found**: If the graph generation fails with a "FileNotFoundError" or "Executable not found", ensure Graphviz is in your PATH and you can run ``dot -V`` in your terminal.
*   **Missing Dependencies**: If a module is missing, try running ``pip install -r requirements.txt`` again.

Building the Documentation
--------------------------

To build a local copy of this documentation:

1.  Install Sphinx and the required extensions:

    .. code-block:: bash

       pip install sphinx sphinx-rtd-theme

2.  Navigate to the ``docs`` directory and run the build command:

    .. code-block:: bash

       # On Windows
       .\make.bat html

       # On macOS/Linux
       make html

3.  Open ``docs/build/html/index.html`` in your browser.