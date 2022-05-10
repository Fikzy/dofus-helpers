import struct
from dataclasses import dataclass
from typing import List


def read_byte(f) -> int:
    return struct.unpack("b", f.read(1))[0]


def read_int(f) -> int:
    return struct.unpack(">i", f.read(4))[0]


def read_double(f) -> int:
    # return struct.unpack(">d", f.read(8))[0]
    return int(struct.unpack(">d", f.read(8))[0])


@dataclass
class Transition:

    _type: int
    _direction: int
    _skill_id: int
    _criterion: str
    _transition_map_id: int
    _cell: int
    _id: int

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
        self._type = type
        self._direction = direction
        self._skill_id = skill_id
        self._criterion = criterion
        self._transition_map_id = transition_map_id
        self._cell = cell
        self._id = id


@dataclass
class Vertex:

    _map_id: int
    _zone_id: int
    _uid: int

    def __init__(self, map_id: int, zone_id: int, vertex_uid: int):
        self._map_id = map_id
        self._zone_id = zone_id
        self._uid = vertex_uid


@dataclass
class Edge:

    _from: Vertex
    _to: Vertex
    _transitions: List[Transition]

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

    _vertices: dict[int, dict[int, Vertex]]
    _edges: dict[int, dict[int, Edge]]
    _outgoing_edges: dict[int, List[Edge]]
    _vertex_uid: int

    def __init__(self, path: str):

        self._vertices = dict()
        self._edges = dict()
        self._outgoing_edges = dict()
        self._vertex_uid = 0

        with open(path, "rb") as f:

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

        if map_id not in self._vertices:
            self._vertices[map_id] = dict()

        if zone not in self._vertices[map_id]:
            self._vertex_uid += 1
            self._vertices[map_id][zone] = Vertex(map_id, zone, self._vertex_uid)

        return self._vertices[map_id][zone]

    def get_edge(self, start: Vertex, end: Vertex) -> Edge:

        if start._uid not in self._edges:
            return None

        return self._edges[start._uid].get(end._uid)

    def add_edge(self, start: Vertex, end: Vertex) -> Edge:

        edge = self.get_edge(start, end)
        if edge:
            return edge

        if not self.does_vertex_exist(start) or not self.does_vertex_exist(end):
            return None

        edge = Edge(start, end)
        if start._uid not in self._edges:
            self._edges[start._uid] = dict()
        self._edges[start._uid][end._uid] = edge

        outgoing = self._outgoing_edges.get(start._uid)
        if not outgoing:
            outgoing = []
            self._outgoing_edges[start._uid] = outgoing

        outgoing.append(edge)
        return edge

    def does_vertex_exist(self, v: Vertex) -> bool:
        return self._vertices[v._map_id][v._zone_id] is not None


def main():

    graph = WorlGraph("world-graph.binary")
    print(len(graph._vertices))
    print(len(graph._edges))


if __name__ == "__main__":
    main()
