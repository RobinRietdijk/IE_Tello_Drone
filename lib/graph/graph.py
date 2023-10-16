import typing
from . import Node
from collections.abc import Callable

class Graph:
    def __init__(self, nodes: list[Node]=[]) -> None:
        self.nodes = {}
        for node in nodes:
            self.nodes[node.getId()] = node

    def __str__(self) -> str:
        return '\n'.join(str(n) for n in self.getNodes().values())

    def getNodes(self) -> dict:
        return self.nodes
    
    def getNode(self, id: int) -> Node:
        return self.nodes[id]

    def setNodes(self, nodes: list[Node]) -> None:
        self.nodes = {}
        for node in nodes:
            self.nodes[node.getId()] = node

    def addNode(self, node: Node) -> None:
        if node.getId() in self.nodes:
            raise Exception("Item already exist, use updateNode instead.")
        self.nodes[node.getId()] = node

    def removeNode(self, node: int | Node) -> None:
        match node:
            case int():
                del self.nodes[node]
            case Node():
                del self.nodes[node.getId()]
            case _:
                raise Exception("Invalid argument")
    
    def updateNode(self, id: int, node: Node) -> None:
        if id not in self.nodes:
            raise Exception(f"Id: {id} does not exist in graph.")
        
        nodeId = node.getId()
        if nodeId != id and nodeId in self.nodes:
            raise Exception("Cannot update node, new id already exists.")
        if nodeId != id and nodeId not in self.nodes:
            self.removeNode(id)
            self.addNode(node)
        else:
            self.nodes[id] = node

    @staticmethod
    def make(nodefile, edgefile):
        nodes: dict = {}
        parseFile(nodefile, setupNodes, nodes)
        parseFile(edgefile, setupEdges, nodes)
        return Graph(nodes.values())

def parseFile(file_path: str, func: Callable[..., None], *args: typing.Any) -> None:
    with open(file_path) as f:
        f.readline()
        line = f.readline()
        while line:
            split = line.split()
            func(split, args)
            line = f.readline()

def setupNodes(split: str, nodes: tuple) -> None:
    if len(nodes) != 1 or not isinstance(nodes[0], dict):
        raise Exception("Invalid argument for setting up nodes.")
    nodes[0][split[0]] = (Node(split[0], split[1], split[2], split[3]))

def setupEdges(split: str, nodes: tuple) -> None:
    if len(nodes) != 1 or not isinstance(nodes[0], dict):
        raise Exception("Invalid argument for setting up edges.")
    nodes[0][split[0]].addEdge(nodes[0][split[1]], split[2])