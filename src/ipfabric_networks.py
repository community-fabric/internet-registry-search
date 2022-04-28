import json

from ipfabric import IPFClient
from ipaddress import IPv4Network
from rir_parse import RIRData
import pytricia
import whoisit
from collections import defaultdict
from pydantic import BaseModel

whoisit.bootstrap()

RIPE_HANDLES = dict()
CGNAT = IPv4Network('100.64.0.0/10')


class Handle(BaseModel):
    handle: str
    name: str
    rir: str


class IPFNets:
    def __init__(self):
        self.networks = self.load_networks()
        self.rir = RIRData().pyt

    @staticmethod
    def _is_public_ip(net):
        net = IPv4Network(net['net'], strict=False)
        if not net.is_private and not net.subnet_of(CGNAT):
            return True

    def load_networks(self):
        ipf = IPFClient()
        pyt = pytricia.PyTricia()
        for net in ipf.fetch_all('tables/networks', filters={"net": ["empty", False]}):
            network = IPv4Network(net['net'], strict=False)
            if not network.is_global:
                continue
            if pyt.has_key(net['net']):
                pyt[net['net']].append(net['siteName'])
            else:
                pyt.insert(net['net'], [net['siteName']])
        return pyt

    def ripe_handles(self, registrants):
        tmp = list()
        for r in registrants:
            if r['handle'] == 'RIPE-NCC-HM-MNT':
                continue
            if r['handle'] not in RIPE_HANDLES:
                whois = whoisit.entity(r['handle'], rir='ripencc')
                name = whois['description'][0] if whois['description'] and whois['name'] == whois['handle'] \
                    else whois['name']
                RIPE_HANDLES[r['handle']] = Handle(handle=whois['handle'], name=name, rir='ripencc')
            tmp.append(RIPE_HANDLES[r['handle']])
        return tmp

    def check_registrant(self, net):
        who = whoisit.ip(net.network, rir=net.source)['entities']
        if not who:
            return dict(registrant=dict(), administrative=dict())
        registrants = who['registrant'] if 'registrant' in who else list()
        if net.source == 'ripencc':
            registrant = self.ripe_handles(registrants)
            administrative = self.ripe_handles(who['administrative'])
        else:
            registrant = [Handle(handle=r['handle'], name=r['name'], rir=net.source) for r in registrants]
            administrative = [
                Handle(handle=r['handle'], name=r['name'], rir=net.source) for r in who['administrative'] if 'name' in r
            ]
        return dict(registrant=registrant, administrative=administrative)

    def check_nets(self):
        networks, top_level = dict(), list()
        nets = defaultdict(list)
        for net in self.networks.keys():
            if not self.networks.parent(net) and net in self.rir:
                nets[self.rir.get(net)[0]].append(net)
                top_level.append(net)

        for net, subnets in nets.items():
            networks[net.network.with_prefixlen] = {
                'num': len(subnets),
                'soruce': net.source,
                'networks': subnets
            }
            networks[net.network.with_prefixlen].update(self.check_registrant(net))
        return networks, {net: self.networks.children(net) for net in top_level}


if __name__ == '__main__':
    test = IPFNets()
    networks, children = test.check_nets()

    print(json.dumps(networks, default=dict))
    print(json.dumps(children))

    print()