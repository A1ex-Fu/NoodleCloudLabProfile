# -*- coding: utf-8 -*-
#
# Profile: 1 witness, 2 replicas, 1 client on a single Layer‑1 switch
#

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

class G(object):
    img      = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
    netmask  = "255.255.255.0"
    base_ip  = "10.10.1."
    hw_node  = "xl170"
    hw_sw    = "dell-s4048"
    repo_url = "https://github.com/A1ex-Fu/vrpaxos.git"
    repo_dir = "/local/repository/vrpaxos"

pc = portal.Context()
request = pc.makeRequestRSpec()

pc.defineParameter(
    "phystype", "Switch type",
    portal.ParameterType.STRING, G.hw_sw,
    [("mlnx-sn2410", "Mellanox SN2410"),
     ("dell-s4048", "Dell S4048")]
)
params = pc.bindParameters()

# ----------------------------------------------------------------------
# Create Layer‑1 switch and four interfaces
sw = request.Switch("l1sw")
sw.hardware_type = params.phystype
sw_ifaces = [sw.addInterface() for _ in range(4)]

def make_node(idx, name, run_cmd):
    """
    Create node 'name' with index idx (0‑based),
    connect to switch, install software, write testConfig2.txt,
    then execute 'run_cmd'.
    """
    node = request.RawPC(name)
    node.hardware_type = G.hw_node
    node.disk_image    = G.img

    iface = node.addInterface()
    ip    = "{}{}".format(G.base_ip, idx + 1)
    iface.addAddress(pg.IPv4Address(ip, G.netmask))

    link = request.L1Link("link{}".format(idx))
    link.addInterface(iface)
    link.addInterface(sw_ifaces[idx])

    # Build contents of testConfig2.txt
    cfg_lines = [
        "f 0",
        "replica {}2:8080".format(G.base_ip),
        "replica {}3:8081".format(G.base_ip),
        "replica {}4:8082".format(G.base_ip)
    ]
    cfg_text = "\\n".join(cfg_lines)

    # One long shell command executed at boot
    setup = (
        "sudo apt update -y && "
        "sudo apt install -y git build-essential -q && "
        "git clone {0} {1} && "
        "echo -e \"{2}\" > {1}/testConfig2.txt && "
        "cd {1} && "
        "{3}"
    ).format(G.repo_url, G.repo_dir, cfg_text, run_cmd)

    node.addService(pg.Execute(shell="bash", command=setup))
    return node

# ----------------------------------------------------------------------
# Instantiate nodes and assign roles
node0 = make_node(
    0, "node0",
    "./bench/replica -c ./testConfig2.txt -i 0 -m vr"
)

node1 = make_node(
    1, "node1",
    "./bench/replica -c ./testConfig2.txt -i 1 -w -m vr"   # witness
)

node2 = make_node(
    2, "node2",
    "./bench/replica -c ./testConfig2.txt -i 2 -m vr"
)

node3 = make_node(
    3, "node3",
    "./bench/client  -c ./testConfig2.txt -m vr -n 1000 -t 1 -w 5 -l latency.txt"
)

# ----------------------------------------------------------------------
pc.printRequestRSpec(request)
