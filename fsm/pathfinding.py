
def sort_and_display_paths(all_paths, dest_state, max_depth, transition_map):
    print(
        f"\nFound {len(all_paths)} path(s) to '{dest_state}' within max depth of {max_depth}:")

    if all_paths:
        all_paths.sort(key=len)

        for i, path in enumerate(all_paths, 1):
            path_depth = len(path) - 1
            path_str = " -> ".join(path)
            print(f"\nPath {i}: (depth {path_depth}) {path_str}")

            if len(path) > 1:
                print("  Triggers used:")
                for j in range(len(path) - 1):
                    src = path[j]
                    dst = path[j + 1]

                    transition_key = f"{src}->{dst}"
                    triggers = transition_map.get(transition_key, ['unknown'])

                    if len(triggers) == 1:
                        print(f"    {src} --[{triggers[0]}]--> {dst}")
                    else:

                        trigger_str = " | ".join(triggers)
                        print(f"    {src} --[{trigger_str}]--> {dst}")
            else:
                print("  (Single node - no transitions)")
    else:
        print(
            f"No paths found to '{dest_state}' within max depth of {max_depth}.")


def pathfinding_simulation(machine, dest_state, max_depth):
    all_paths = []
    graph = {}
    transition_map = {}

    for state in machine.states:
        graph[state] = []

    for transition in machine.transitions_data:
        if transition['source'] == '*':

            for state in machine.states:
                if state != transition['dest']:
                    graph[state].append({
                        'dest': transition['dest'],
                        'trigger': transition['trigger']
                    })

                    transition_key = f"{state}->{transition['dest']}"
                    if transition_key not in transition_map:
                        transition_map[transition_key] = []
                    transition_map[transition_key].append(
                        transition['trigger'])
        else:
            graph[transition['source']].append({
                'dest': transition['dest'],
                'trigger': transition['trigger']
            })
            transition_key = f"{transition['source']}->{transition['dest']}"
            if transition_key not in transition_map:
                transition_map[transition_key] = []
            transition_map[transition_key].append(transition['trigger'])

    def dfs(current_node, path, depth):
        path.append(current_node)

        if current_node == dest_state:
            all_paths.append(path[:])
            path.pop()
            return

        if depth >= max_depth:
            path.pop()
            return

        for neighbor in graph[current_node]:
            if neighbor['dest'] not in path:
                dfs(neighbor['dest'], path, depth + 1)

        path.pop()

    for state in machine.states:
        if state != dest_state:
            dfs(state, [], 0)

    if dest_state in machine.states:
        all_paths.append([dest_state])

    sort_and_display_paths(all_paths, dest_state, max_depth, transition_map)
