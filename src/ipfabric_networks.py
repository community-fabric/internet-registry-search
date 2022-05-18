import json

from ipfabric import IPFClient
from ipaddress import IPv4Network
from rir_parse import RIRData
import pytricia
import whoisit
from collections import defaultdict
from pydantic import BaseModel
import pandas as pd

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
            if not self.networks.parent(net):
                if net in self.rir:
                    nets[self.rir.get(net)[0]].append(net)
                    top_level.append(net)
                else:
                    print(f"Error: {net}")

        for net, subnets in nets.items():
            networks[net.network.with_prefixlen] = {
                'num': len(subnets),
                'source': net.source,
                'networks': subnets
            }
            networks[net.network.with_prefixlen].update(self.check_registrant(net))
        return networks, {net: self.networks.children(net) for net in top_level}


def format_handles(data, reg_type):
    registrant = ''
    if reg_type in data:
        for reg in data[reg_type]:
            registrant += f"{reg.handle}: {reg.name}\n"
    return registrant.rstrip('\n')


def format_networks(nets, childs):
    formatted, mapping = list(), list()
    for net, data in nets.items():
        formatted.append([net, data['source'], data['num'], format_handles(data, 'registrant'),
                          format_handles(data, 'administrative')])
        for n in data['networks']:
            mapping.append([net, n])
    irr_df = pd.DataFrame(formatted, columns=['Network', 'Source', 'IPF Networks', 'Registrant', 'Administrative'])
    map_df = pd.DataFrame(mapping, columns=['IRR Network', 'IPF Network'])

    tmp = list()
    for n, c in childs.items():
        for s in c:
            tmp.append([n, s])
    child_df = pd.DataFrame(tmp, columns=['IPF Network', 'IPF Subnets'])
    return irr_df, map_df, child_df


if __name__ == '__main__':
    test = IPFNets()
    networks, children = test.check_nets()
    irr_df, map_df, child_df = format_networks(networks, children)
    with pd.ExcelWriter('IPFabric_IRR_Report.xlsx', engine='xlsxwriter') as writer:
        writer.book.formats[0].set_text_wrap()
        irr_df.to_excel(writer, sheet_name='IRR Summary', index=False)
        map_df.to_excel(writer, sheet_name='IPF Networks', index=False)
        child_df.to_excel(writer, sheet_name='IPF Subnets', index=False)


    # print(json.dumps(networks, default=dict))
    # print(json.dumps(children))

    print()
