# Tacitus Infrastructure Simulation

import ipaddress
import re
from dash import Dash, html
import dash_cytoscape as cyto

class Node:
    def __init__(self, name = "", id = "", ip = "", actions = None, ingress_rules = None, egress_rules = None, access_policy = None, use_access = False, use_ingress = False, use_egress = False):
        self.name = name
        self.id = id
        self.ip = ip
        self.actions = actions
        self.ingress_rules = ingress_rules
        self.egress_rules = egress_rules
        self.access_policy = access_policy
        self.use_access = use_access
        self.use_ingress = use_ingress
        self.use_egress = use_egress
        self.hop_success = 0
        self.hop_failure = 0
        
        if not self.actions:
            self.actions = []
        if not self.ingress_rules:
            self.ingress_rules = []
        if not self.egress_rules:
            self.egress_rules = []
        if not self.access_policy:
            self.access_policy = []

    def json(self):
        return {
            "name": self.name,
            "id": self.id,
            "ip": self.ip,
            "actions": self.actions,
            "ingress_rules": self.ingress_rules,
            "egress_rules": self.egress_rules,
            "access_policy": self.access_policy,
            "use_access": self.use_access,
            "use_ingress": self.use_ingress,
            "use_egress": self.use_egress,
            "hop_success": self.hop_success,
            "hop_failure": self.hop_failure,
        }

    def ingress_check(self, src: str, port: int, protocol: str):
        for rule in self.ingress_rules:
            if port == rule["port"] and protocol == rule["protocol"] and ipaddress.ip_address(src) in ipaddress.ip_network(rule["cidr"]):
                return True
        return False

    def egress_check(self, src: str, port: int, protocol: str):
        for rule in self.egress_rules:
            if port == rule["port"] and protocol == rule["protocol"] and ipaddress.ip_address(src) in ipaddress.ip_network(rule["cidr"]):
                return True
        return False

    def access_check(self, resource: str, actions: list) -> bool:
        action_statuses = {a: False for a in actions}
        for policy in self.access_policy:
            policy_resources = [r.replace("*", ".*") for r in policy["resources"]]
            allowed = False
            for policy_resource in policy_resources:
                if re.match(policy_resource, resource):
                    allowed = True
                    break
            if not allowed:
                continue
            policy_actions = [a.replace("*", ".*") for a in policy["actions"]]
            for policy_action in policy_actions:
                for action in actions:
                    if re.match(policy_action, action):
                        action_statuses[action] = True
        for action in actions:
            if action_statuses[action]:
                return True
        return False

def rgb_to_hex(r, g, b):
    return "{:02X}{:02X}{:02X}".format(r, g, b)

def simulate(nodes = None, flows = None, max_time = 100, timestep = 1):        
    if not nodes:
        nodes = []
    if not flows:
        flows = []

    dns = {}
    for name, node in nodes.items():
        dns[name] = node.ip

    tick = 0
    statuses = []
    hops = {}
    while tick < max_time:
        for flow in flows:
            for _ in range(0, flow['reqs']):
                status = {}
                stack = []
                current = ""
                for step in flow['steps']:
                    stack.append(step)
                    if step == ".pop":
                        stack.pop(-1)
                        if len(stack) == 1:
                            break
                        parts_a = stack[-2].split('://')
                        parts_b = parts_a[1].split(':')
                        current = parts_b[0]
                    else:
                        parts_a = step.split('://')
                        parts_b = parts_a[1].split(':')
                        protocol = parts_a[0]
                        host = parts_b[0]
                        port = int(parts_b[1])
                        if current:
                            if nodes[host].use_access:
                                if not nodes[current].access_check(nodes[host].id, nodes[current].actions):
                                    key = f'{current}->{host}'
                                    status[key] = False
                                    if not key in hops:
                                        hops[key] = {
                                            "success": 0,
                                            "failure": 1
                                        }
                                    else:
                                        hops[key]['failure'] += 1
                                    nodes[host].hop_failure += 1
                                    print(f'Error on {current}->{host} access check with destination {step}')
                                    break
                            else:
                                if nodes[current].use_egress and not nodes[current].egress_check(dns[host], port, protocol):
                                    key = f'{current}->{host}'
                                    status[key] = False
                                    if not key in hops:
                                        hops[key] = {
                                            "success": 0,
                                            "failure": 1
                                        }
                                    else:
                                        hops[key]['failure'] += 1
                                    nodes[host].hop_failure += 1
                                    print(f'Error on {current}->{host} egress check with destination {step}')
                                    break
                                if nodes[host].use_ingress and not nodes[host].ingress_check(nodes[current].ip, port, protocol):
                                    key = f'{current}->{host}'
                                    status[key] = False
                                    if not key in hops:
                                        hops[key] = {
                                            "success": 0,
                                            "failure": 1
                                        }
                                    else:
                                        hops[key]["failure"] += 1
                                    nodes[host].hop_failure += 1
                                    print(f'Error on {current}->{host} ingress check with destination {step}')
                                    break
                        key = f'{current}->{host}'
                        status[key] = True
                        if not key in hops:
                            hops[key] = {
                                "success": 1,
                                "failure": 0
                            }
                        else:
                            hops[key]["success"] += 1
                        nodes[host].hop_success += 1
                        current = host
                statuses.append(status)
        tick += timestep

    return hops

if __name__ == '__main__':
    nodes = {
        "api": Node(
            name = "api",
            ip = "10.0.0.1",
            egress_rules = [
                {
                    "protocol": "http",
                    "cidr": "10.0.0.0/8",
                    "port": 8080
                },
                {
                    "protocol": "postgresql",
                    "cidr": "10.0.0.0/8",
                    "port": 5432
                }
            ],
            ingress_rules = [
                {
                    "protocol": "http",
                    "cidr": "10.0.0.0/8",
                    "port": 8080
                }
            ],
            use_ingress = True,
            use_egress = True,
            use_access = False,
        ),
        "portal": Node(
            name = "portal",
            ip = "10.0.0.2",
            egress_rules = [
                {
                    "protocol": "http",
                    "cidr": "10.0.0.0/8",
                    "port": 8080
                }
            ],
            ingress_rules = [
                {
                    "protocol": "https",
                    "cidr": "10.0.0.0/8",
                    "port": 443
                }
            ],
            use_ingress = True,
            use_egress = True,
        ),
        "my-s3-bucket": Node(
            name = "my-s3-bucket",
            id = "my-s3-bucket",
            ip = "10.0.0.3",
            use_access = True
        ),
        "model": Node(
            name = "model",
            ip = "10.0.0.4",
            egress_rules = [
                {
                    "protocol": "http",
                    "cidr": "10.0.0.0/8",
                    "port": 8080
                }
            ],
            ingress_rules = [
                {
                    "protocol": "http",
                    "cidr": "10.0.0.0/8",
                    "port": 8080
                }
            ],
            access_policy = [
                {
                    "actions": [
                        "s3::*"
                    ],
                    "resources": [
                        "my-s3-bucket"
                    ]
                }
            ],
            actions = [
                "s3::PutObject"
            ],
            use_ingress = True,
            use_egress = True,
        ),
        "db": Node(
            name = "db",
            ip = "10.0.0.5",
            egress_rules = [
                {
                    "protocol": "postgresql",
                    "cidr": "10.0.0.0/8",
                    "port": 5432
                }
            ],
            ingress_rules = [
                {
                    "protocol": "postgresql",
                    "cidr": "10.0.0.0/8",
                    "port": 5432
                }
            ],
            use_ingress = True,
            use_egress = True
        )
    }

    flows = [
        {
            "reqs": 2,
            "latency": 1,
            "steps": [
                "https://portal:443",
                "http://api:8080",
                "postgresql://db:5432",
                ".pop",
                "http://model:8080",
                "s3://my-s3-bucket:-1",
                ".pop",
                ".pop",
                ".pop",
                ".pop"
            ]
        },
        {
            "reqs": 4,
            "latency": 1,
            "steps": [
                "https://portal:443",
                "http://api:8080",
                "s3://my-s3-bucket:-1",
                ".pop",
                ".pop",
            ]
        }
    ]

    elements = []
    stylesheet = [
        {
            'selector': 'node',
            'style': {
                'content': 'data(label)',
                'text-halign':'center',
                'text-valign':'center',
                'width':'label',
                'height':'label',
                'shape':'square'
            }
        }
    ]
    hops = simulate(nodes, flows, 10)

    for name in nodes:
        total_requests = nodes[name].hop_success + nodes[name].hop_failure
        failure_percent = 0
        if total_requests:
            failure_percent = nodes[name].hop_failure / total_requests

        r = int(255 * failure_percent)
        g = 255 - r
        b = 0

        elements.append(
            {'data': {'id': name, "label": name}, "classes": rgb_to_hex(r, g, b)}
        )

    for hop in hops:
        total_requests = hops[hop]['success'] + hops[hop]['failure']
        failure_percent = 0
        if total_requests:
            failure_percent = hops[hop]['failure'] / total_requests

        r = int(255 * failure_percent)
        g = 255 - r
        b = 0

        parts = hop.split('->')
        src = parts[0]
        dest = parts[1]

        if src:
            elements.append(
                {'data': {'source': src, "target": dest}, "classes": rgb_to_hex(r, g, b)}
            )
    
    for i in range(0, 256):
        r = i
        g = 255 - r
        b = 0
        stylesheet.append(
            {'selector': f'.{rgb_to_hex(r, g, b)}', 'style': {'background-color': f'#{rgb_to_hex(r, g, b)}', 'line-color': f'#{rgb_to_hex(r, g, b)}'}}
        )

    app = Dash(__name__)

    app.layout = html.Div([
        html.P("Dash Cytoscape:"),
        cyto.Cytoscape(
            id='cytoscape',
            elements=elements,
            layout={'name': 'breadthfirst'},
            style={'width': '1000px', 'height': '800px'},
            stylesheet=stylesheet
        )
    ])


    app.run_server(debug=True, port=8080)