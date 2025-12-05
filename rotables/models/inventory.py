from dataclasses import dataclass

@dataclass
class InventoryState:
    fc: int
    bc: int
    pe: int
    ec: int

    def add(self, fc=0, bc=0, pe=0, ec=0):
        self.fc += fc; self.bc += bc; self.pe += pe; self.ec += ec

    def remove(self, fc=0, bc=0, pe=0, ec=0):
        self.fc = max(0, self.fc - fc)
        self.bc = max(0, self.bc - bc)
        self.pe = max(0, self.pe - pe)
        self.ec = max(0, self.ec - ec)
