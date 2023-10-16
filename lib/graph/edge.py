class Edge:
    def __init__(self, frm: object, to: object, w: int=1) -> None:
        self.frm = frm
        self.to = to
        self.w = w

    def __str__(self) -> str:
        return f"( {self.getFrom().getId()} -> {self.getTo().getId()}: {self.getWeight()} )"

    def getFrom(self) -> object:
        return self.frm

    def setFrom(self, frm: object) -> None:
        self.frm = frm

    def getTo(self) -> object:
        return self.to
    
    def setTo(self, to: object) -> None:
        self.to = to

    def getWeight(self) -> int:
        return self.w
    
    def setWeight(self, w: int) -> None:
        self.w = w