from . import Edge
from typing_extensions import Self

class Node:
    def __init__(self, id: int, x: float, y: float, z: float) -> None:
        self.id = id
        self.x = x
        self.y = y
        self.z = z

        self.edges = []

    def __str__(self) -> str:
        return f"( {self.getId()} | x:{self.getX()}, y:{self.getY()}, z:{self.getZ()} | {' '.join(str(e) for e in self.getEdges())})"

    def getEdges(self) -> list[Edge]:
        return self.edges

    def setEdges(self, edges: list[Edge]) -> None:
        self.edges = edges

    def addEdge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def addEdge(self, to: Self, w: int=1) -> None:
        self.edges.append(Edge(self, to, w))

    def removeEdge(self, edge: Edge) -> None:
        self.edges.remove(edge)

    def getId(self) -> int:
        return self.id
    
    def setId(self, id: int) -> None:
        self.id = id

    def getX(self) -> float:
        return self.x
    
    def setX(self, x: float) -> None:
        self.x = x

    def getY(self) -> float:
        return self.y
    
    def setY(self, y: float) -> None:
        self.y = y

    def getZ(self) -> float:
        return self.z
    
    def setZ(self, z: float) -> None:
        self.z = z