import math

from rir_ftp import download_all
import csv
from pydantic import BaseModel
from ipaddress import IPv4Network
import pytricia


class Network(BaseModel):
    source: str
    net: str
    addresses: int
    network: IPv4Network

    def __hash__(self):
        return hash(self.network)


class RIRData:
    def __init__(self):
        self.pyt = self.load_pyt()

    def load_pyt(self):
        pyt = pytricia.PyTricia()
        for lir in ['arin', 'apnic', 'afrinic', 'lacnic', 'ripe']:
            for net in self.load_lir(lir + '.txt'):
                if pyt.has_key(net.network):
                    pyt[net.network].append(net)
                else:
                    pyt.insert(net.network, [net])
        return pyt

    @staticmethod
    def load_lir(lir_file) -> list[Network]:
        data = list()
        with open('rir/' + lir_file, 'r') as f:
            csv_reader = csv.reader(f, delimiter='|')
            for row in csv_reader:
                if row[0][0] == '#' or row[2] != 'ipv4' or \
                        (row[2] == 'ipv4' and (row[3] == '*' or
                                               (len(row) >= 7 and row[6] not in ['allocated', 'assigned']))):
                    continue
                network = IPv4Network(row[3] + f'/{str(32 - int(math.log(int(row[4]), 2)))}', strict=False)
                data.append(Network(source=row[0], net=row[3], addresses=row[4], network=network))
        return data


if __name__ == '__main__':

    test = RIRData()
    print()