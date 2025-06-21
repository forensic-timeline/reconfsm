import os


def graph_simulation(machine):
    result_dir = os.path.join('result', machine.name)
    os.makedirs(result_dir, exist_ok=True)
    graph_path = os.path.join(result_dir, 'visual.png')
    machine.machine.get_graph().draw(graph_path, prog='dot')
    print(f"Graph saved to: {graph_path}")
