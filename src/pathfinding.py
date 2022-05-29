import functools
from dataclasses import dataclass

from world_graph import Edge, Vertex, WorlGraph

HEURISTIC_SCALE = 1
INDOOR_WEIGHT = 0
MAX_ITERATIONS = 10000
CRITERION_WHITE_LIST = [
    "Ad",
    "DM",
    "MI",
    "Mk",
    "Oc",
    "Pc",
    "QF",
    "Qo",
    "Qs",
    "Sv",
]


@dataclass
class Node:

    vertex: Vertex
    map_data: dict()
    parent: "Node" = None
    cost: int = 0
    heuristic: int = 0


def __search(graph: WorlGraph, start: Vertex, dest: Vertex):

    if start == dest:
        return None

    iterations = 0
    closed_dict: dict[Vertex, Node] = dict()
    open_dict: dict[Vertex, Node] = dict()
    open_list = [Node(start, start.map_data)]

    while len(open_list) > 0:

        iterations += 1
        if iterations > MAX_ITERATIONS:
            print("Too many iterations, aborting pathfinding.")
            return None

        current = open_list.pop(0)
        open_dict[current.vertex] = None

        if current.vertex == dest:
            print(f"Path found in {iterations} iterations.")
            return __build_result_path(graph, current)

        edges = graph.outgoing_edges.get(current.vertex.uid)

        old_len = len(open_list)
        cost = current.cost + 1

        for edge in edges or []:

            if __has_valid_transition(edge):
                existing = closed_dict.get(edge.end)
                if not (existing is not None and cost >= existing.cost):
                    existing = open_dict.get(edge.end)
                    if not (existing is not None and cost >= existing.cost):
                        map_data = edge.end.map_data
                        if map_data == None:
                            print("Map doesn't exist.")
                            continue

                        dist_x = abs(map_data["posX"] - dest.map_data["posX"])
                        dist_y = abs(map_data["posY"] - dest.map_data["posY"])
                        manh_dist = dist_x + dist_y
                        node = Node(
                            edge.end,
                            map_data,
                            current,
                            cost,
                            cost
                            + HEURISTIC_SCALE * manh_dist
                            + (
                                current.map_data["outdoor"] and INDOOR_WEIGHT
                                if not map_data["outdoor"]
                                else 0
                            ),
                        )
                        open_list.append(node)
                        open_dict[node.vertex] = node

        closed_dict[current.vertex] = current
        if old_len < len(open_list):
            open_list.sort(
                key=functools.cmp_to_key(
                    lambda a, b: 0
                    if a.heuristic == b.heuristic
                    else (1 if a.heuristic > b.heuristic else -1)
                )
            )
        # if timeout...?


def __has_valid_transition(edge: Edge) -> bool:
    valid = False
    for transition in edge.transitions:
        if len(transition.criterion) != 0:
            if (
                transition.criterion.find("&") == -1
                and transition.criterion.find("|") == -1
                and transition.criterion[0:2] in CRITERION_WHITE_LIST
            ):
                return False
            # TODO:
            # criterion = GroupItemCriterion(transition.criterion) ??
            # return criterion.is_respected()
            return True
        valid = True
    return valid


# def __has_valid_destination_subarea(edge: Edge) -> bool:
#     start_subarea_id = edge.start.map_data["subAreaId"]
#     end_subarea_id = edge.end.map_data["subAreaId"]
#     if start_subarea_id == end_subarea_id:
#         return True
#     # if forbidden_sub_areas...
#         return False
#     return True


def __build_result_path(graph: WorlGraph, node: Node) -> list[Edge]:
    result = []
    while node.parent != None:
        result.append(graph.get_edge(node.parent.vertex, node.vertex))
        node = node.parent
    result.reverse()
    return result


def find_path(
    graph: WorlGraph, start_map_id: int, dest_pos: tuple[int, int]
) -> list[tuple[int, int]]:

    start_map_data = graph.map_positions.get(start_map_id)
    if start_map_data is None:
        return None

    start = graph.vertices.get(start_map_id).get(start_map_data["worldMap"])
    if start is None:
        return None

    dest_vertices = graph.pos_to_vertex.get(dest_pos)

    if dest_vertices is None:
        return None

    for dest_vertex in dest_vertices:

        path = __search(graph, start, dest_vertex)
        if not path:
            continue

        path_coordinates = [path[0].start.pos]
        for edge in path:
            path_coordinates.append(edge.end.pos)
        return path_coordinates
