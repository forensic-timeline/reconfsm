# reconfsm

reconfsm is a forensic reconstruction toolkit that models system activity as Finite State Machines (FSM). It enables investigators to process timeline logs from disk images, convert them into FSMs, simulate transitions, perform pathfinding analysis, and visualize everything interactively.

## Installation

Create a virtual environment using Anaconda or other tools. Open your terminal and run the command:

```bash
conda create --name reconfsm python=3.12
```

Once the virtual environment is created successfully, activate it with:

```bash
conda activate reconfsm
```

Clone the reconfsm repository:

```bash
git clone https://github.com/your-username/reconfsm.git
```

Navigate to the root project directory:

```bash
cd reconfsm
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Remember, every time you need to use this package, ensure that you activate the virtual environment using `conda activate reconfsm`.

## Project Structure

```
reconfsm/
├── converter/
│   ├── convert.py          # Main conversion script
│   ├── scripts/            # Activity extraction scripts
│   │   ├── application_activity.py
│   │   ├── system_shutdown.py
│   │   └── web_activity.py
│   └── json_machines/      # Generated JSON output (created automatically)
├── fsm/
│   ├── fsm.py             # Main FSM simulator
│   ├── graph.py           # Graph visualization functions
│   └── pathfinding.py     # Pathfinding algorithms
├── visualizer/
│   └── index.html         # Web-based FSM visualizer
└── requirements.txt
```

## Quick Start

### 1. Activate the virtual environment:

```bash
conda activate reconfsm
```

### 2. Extract timeline logs with Plaso using Docker:

```bash
docker run -v "$PWD:/data" --rm log2timeline/plaso \
  log2timeline /data/timeline.plaso /data/disk.vmdk

docker run -v "$PWD:/data" --rm log2timeline/plaso \
  psort -w /data/timeline.csv /data/timeline.plaso
```

### 3. Convert CSV to FSM JSON:

```bash
cd converter
python convert.py /path/to/timeline.csv web_activity
```

Available activity types:

- `web_activity` - Browser history and web interactions
- `application_activity` - Application launches and exits from systemd logs
- `system_shutdown` - System shutdown events from system logs

### 4. Simulate FSM (Graph & Pathfinding):

Navigate to the fsm directory:

```bash
cd ../fsm
```

Generate visual graph:

```bash
python fsm.py ../converter/json_machines/web_activity/web_activity_*.json graph
```

Find paths to specific states:

```bash
python fsm.py ../converter/json_machines/web_activity/web_activity_*.json pathfinding -s "End State" -d 3
```

### 5. Visualize FSM in browser:

Open `visualizer/index.html` in a web browser and load the generated JSON files for interactive visualization.

Alternatively, you can use the online version at: [fsm-visualizer.vercel.app](https://fsm-visualizer.vercel.app/)

## Detailed Usage

### Converting CSV to FSM

The converter processes Plaso timeline CSV files and extracts specific activity patterns:

```bash
cd converter
python convert.py <csv_file> <activity_type>
```

**Parameters:**

- `csv_file`: Path to the Plaso-generated CSV timeline file
- `activity_type`: Type of activity to extract (see supported types below)

**Output:** JSON files are saved in `json_machines/<activity_type>/` directory with timestamp.

### FSM Simulation

The FSM simulator provides two main functions:

#### Graph Generation

```bash
python fsm.py <json_file> graph
```

Generates a visual graph representation saved as PNG in `result/<machine_name>/visual.png`

#### Pathfinding Analysis

```bash
python fsm.py <json_file> pathfinding -s <target_state> -d <max_depth>
```

**Parameters:**

- `-s <target_state>`: The destination state to find paths to
- `-d <max_depth>`: Maximum search depth for pathfinding

**Example:**

```bash
python fsm.py json_machines/web_activity/web_activity_20250605_182216.json pathfinding -s "Web : google.com" -d 5
```

## Supported Activity Types

### Web Activity

- **Source:** Firefox history entries from Plaso CSV
- **Extracts:** Site visits, search queries, file downloads
- **States:** Web sites, search engines, downloaded files
- **Triggers:** `accessed_website_direct`, `accessed_website_link`, `accessed_website_redirect`, `performed_search`, `downloaded_file`

### Application Activity

- **Source:** systemd journal entries from Plaso CSV
- **Extracts:** Application launches and terminations
- **States:** Application names and Desktop
- **Triggers:** `launch_<app>`, `close_<app>`

### System Shutdown

- **Source:** systemd journal entries from Plaso CSV
- **Extracts:** Manual/forced shutdown events, shutdown completion
- **States:** System Running, Initiating Shutdown, System Shutdown, System Recovery
- **Triggers:** `cmd_sudo_poweroff`, `cmd_sudo_shutdown_now`, `shutdown_completed`, `forceful_shutdown_detected`

## Output Formats

### JSON Structure

Each generated JSON file contains a finite state machine definition:

```json
{
  "activity_type_machine": [
    {
      "name": "activity_type_YYYYMMDD_HHMMSS",
      "initial_state": "Initial State Name",
      "states": ["State1", "State2", "..."],
      "triggers": ["trigger1", "trigger2", "..."],
      "transitions": [
        {
          "trigger": "trigger_name",
          "source": "source_state",
          "dest": "destination_state"
        }
      ],
      "functions": {}
    }
  ]
}
```

### Graph Output

Visual graphs are saved as PNG files using Graphviz in the `result/` directory.

## Interactive Visualization

The web-based visualizer (`visualizer/index.html`) provides:

- **JSON Import:** Load FSM JSON files via file picker or drag-and-drop
- **Layout Options:** Grid, hierarchical, force-directed, and circular layouts
- **Pathfinding:** Interactive path discovery with configurable depth
- **Visual Controls:** Zoom, pan, node highlighting, and PNG export
- **Path Analysis:** Display all possible paths to selected end states

## Requirements

- Python 3.12+
- See `requirements.txt` for Python dependencies
- Docker (for Plaso timeline extraction)
- Modern web browser (for visualization)

## Dependencies

Key Python packages:

- `transitions` - Finite state machine implementation
- `graphviz` - Graph visualization
- Standard library modules for JSON, CSV, and regex processing

## Author

**Afiq Fawwaz Haidar**  
Final Year Project — Institut Teknologi Sepuluh Nopember

### Supervisors:

- Dr. Hudan Studiawan
- Dr. Baskoro Adi Pratomo
