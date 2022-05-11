import os
import struct
from dataclasses import dataclass
from py_dofus import d2o


MAP_POSITIONS_FILE = os.path.join("content", "common", "MapPositions.d2o")
WORLD_GRAPH_BINARY_FILE = os.path.join("content", "maps", "world-graph.binary")


def read_byte(f) -> int:
    return struct.unpack("b", f.read(1))[0]


def read_int(f) -> int:
    return struct.unpack(">i", f.read(4))[0]


def read_double(f) -> int:
    # return struct.unpack(">d", f.read(8))[0]
    return int(struct.unpack(">d", f.read(8))[0])


@dataclass
class Transition:

    type: int
    direction: int
    skill_id: int
    criterion: str
    transition_map_id: int
    cell: int
    id: int

    def __init__(
        self,
        type: int,
        direction: int,
        skill_id: int,
        criterion: str,
        transition_map_id: int,
        cell: int,
        id: int,
    ):
        self.type = type
        self.direction = direction
        self.skill_id = skill_id
        self.criterion = criterion
        self.transition_map_id = transition_map_id
        self.cell = cell
        self.id = id


@dataclass
class Vertex:

    map_id: int
    zone_id: int
    uid: int
    pos: tuple[int, int]

    def __init__(
        self, map_id: int, zone_id: int, vertex_uid: int, pos: tuple[int, int]
    ):
        self.map_id = map_id
        self.zone_id = zone_id
        self.uid = vertex_uid
        self.pos = pos


@dataclass
class Edge:

    _from: Vertex
    _to: Vertex
    _transitions: list[Transition]

    def __init__(self, start: Vertex, end: Vertex):
        self._from = start
        self._to = end
        self._transitions = []

    def add_transition(
        self,
        dir: int,
        type: int,
        skill: int,
        criterion: str,
        transition_map_id: int,
        cell: int,
        id: int,
    ):
        self._transitions.append(
            Transition(type, dir, skill, criterion, transition_map_id, cell, id)
        )


@dataclass
class WorlGraph:

    vertices: dict[int, dict[int, Vertex]]
    edges: dict[int, dict[int, Edge]]
    outgoing_edges: dict[int, list[Edge]]
    _vertex_uid: int
    _map_positions: dict[int, dict]

    def __init__(self, game_dir: str):

        self.vertices = dict()
        self.edges = dict()
        self.outgoing_edges = dict()
        self._vertex_uid = 0

        with open(os.path.join(game_dir, MAP_POSITIONS_FILE), "rb") as f:
            d2o_reader = d2o.D2OReader(f)
            d2o_data = d2o_reader.get_objects()
            self._map_positions = {value["id"]: value for value in d2o_data}

        with open(os.path.join(game_dir, WORLD_GRAPH_BINARY_FILE), "rb") as f:

            edge_count = read_int(f)

            for _ in range(edge_count):
                start = self.add_vertex(read_double(f), read_int(f))
                end = self.add_vertex(read_double(f), read_int(f))
                edge = self.add_edge(start, end)

                transistion_count = read_int(f)

                for _ in range(transistion_count):
                    edge.add_transition(
                        read_byte(f),
                        read_byte(f),
                        read_int(f),
                        f.read(read_int(f)).decode("utf-8"),
                        read_double(f),
                        read_int(f),
                        read_double(f),
                    )

    def add_vertex(self, map_id: int, zone: int) -> Vertex:

        if map_id not in self.vertices:
            self.vertices[map_id] = dict()

        if zone not in self.vertices[map_id]:
            self._vertex_uid += 1
            map_data = self._map_positions.get(map_id)
            coords = map_data["posX"], map_data["posY"]
            self.vertices[map_id][zone] = Vertex(map_id, zone, self._vertex_uid, coords)

        return self.vertices[map_id][zone]

    def get_edge(self, start: Vertex, end: Vertex) -> Edge:

        if start.uid not in self.edges:
            return None

        return self.edges[start.uid].get(end.uid)

    def add_edge(self, start: Vertex, end: Vertex) -> Edge:

        edge = self.get_edge(start, end)
        if edge:
            return edge

        if not self.does_vertex_exist(start) or not self.does_vertex_exist(end):
            return None

        edge = Edge(start, end)
        if start.uid not in self.edges:
            self.edges[start.uid] = dict()
        self.edges[start.uid][end.uid] = edge

        outgoing = self.outgoing_edges.get(start.uid)
        if not outgoing:
            outgoing = []
            self.outgoing_edges[start.uid] = outgoing

        outgoing.append(edge)
        return edge

    def does_vertex_exist(self, v: Vertex) -> bool:
        return self.vertices[v.map_id][v.zone_id] is not None


def main():

    graph = WorlGraph("fake_dofus_dir")

    v = graph.vertices.get(96338944)[1]
    print(v)


if __name__ == "__main__":
    main()
