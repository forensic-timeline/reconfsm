# 🔍 reconfsm — Forensic Event Reconstruction with FSM

**reconfsm** is a forensic reconstruction toolkit that models system activity as Finite State Machines (FSM). It enables investigators to process timeline logs from disk images, convert them into FSMs, simulate transitions, perform pathfinding analysis, and visualize everything interactively.

---

## 📆 Repository Structure

```
reconfsm/
├── converter/             # CSV → FSM JSON converter
│   ├── csv/               # Timeline CSV input files
│   └── scripts/           # Activity extraction scripts (web, app, shutdown)
├── fsm/                   # FSM simulator & JSON output
│   └── json/              # FSM JSON files for each scenario
├── plaso/                 # PowerShell automation for Plaso + psort
└── visualizer/            # Interactive FSM visualizer frontend

```

---

## 🤭 Workflow Overview

```
+-----------+     +------------+     +-----------+     +--------------+
|  Plaso    | --> |  Converter | --> |  FSM Sim  | --> |  Visualizer  |
+-----------+     +------------+     +-----------+     +--------------+
 .vmdk logs        CSV → JSON         Graph/Path         Web-based UI
```

---

## ⚙️ 1. Extract Timeline Logs with Plaso

Use Docker to extract `.plaso` and convert to `.csv`:

```bash
docker run -v "$PWD:/data" --rm log2timeline/plaso \
  log2timeline /data/timeline.plaso /data/disk.vmdk

docker run -v "$PWD:/data" --rm log2timeline/plaso \
  psort -w /data/timeline.csv /data/timeline.plaso
```

Alternatively, use the `plaso/plaso.ps1` PowerShell script to automate everything on Windows.

---

## 🧪 2. Convert CSV to FSM JSON

```bash
cd converter
python convert.py csv/timeline.csv <script_type>
```

- `<script_type>` options:

  - `web_activity`
  - `application_activity`
  - `system_shutdown`

Output is saved to:

```
fsm/json/<script_type>_<timestamp>.json
```

---

## 🧠 3. Simulate FSM (Graph & Pathfinding)

```bash
cd fsm
python fsm.py json/<filename>.json graph
python fsm.py json/<filename>.json pathfinding -s "<end_state>" -d <max_depth>
```

Examples:

```bash
python fsm.py json/web_activity_*.json graph
python fsm.py json/system_shutdown_*.json pathfinding -s "System Shutdown" -d 3
```

---

## 🌐 4. Visualize FSM in Browser

View FSMs in an interactive graph at:

👉 [fsm-visualizer.vercel.app](https://fsm-visualizer.vercel.app/)

### Features:

- Upload `.json` FSM files
- Choose layout (grid, circular, hierarchical)
- Highlight paths to any end node
- Export PNG diagrams

---

## ✅ Supported Activity Types

| Activity Type        | Description                                 |
| -------------------- | ------------------------------------------- |
| Web Activity         | Site visits, search queries, file downloads |
| Application Activity | App launches and exits from systemd logs    |
| System Shutdown      | Manual/forced shutdown events from sys logs |

---

## 👨‍💻 Author

**Afiq Fawwaz Haidar**
Final Year Project — Institut Teknologi Sepuluh Nopember

### Supervisors:

- Dr. Hudan Studiawan
- Dr. Baskoro Adi Pratomo
