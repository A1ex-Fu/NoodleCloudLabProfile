# -*- coding: utf-8 -*-
#
# CloudLab profile: 4 nodes on a shared LAN running vrpaxos.
# Compatible with Python 2.7 (no f-strings, no non-ASCII chars).
#
import geni.portal as portal
import geni.rspec.pg as pg

pc      = portal.Context()
request = pc.makeRequestRSpec()

# ---------- parameters ----------
pc.defineParameter("phystype",  "Physical node type",
                   portal.ParameterType.STRING, "",
                   longDescription="Leave blank for any available type.")

pc.defineParameter("linkSpeed", "LAN link speed",
                   portal.ParameterType.INTEGER, 1000000,
                   [(100000,  "100Mb/s"),
                    (1000000, "1Gb/s"),
                    (10000000,"10Gb/s")])

params = pc.bindParameters()

# ---------- constants ----------
NODE_COUNT = 4
BASE_IP    = "10.10.1."
PORT_START = 8080
DISK_IMAGE = ("urn:publicid:IDN+emulab.net+image+emulab-ops//"
              "UBUNTU22-64-STD")
GIT_URL    = "https://github.com/A1ex-Fu/vrpaxos.git"

# ---------- LAN ----------
lan = request.LAN("lan0")
lan.bandwidth = params.linkSpeed

nodes = []
ips   = []

# ---------- create nodes ----------
for i in range(NODE_COUNT):
    node = request.RawPC("node%d" % i)
    node.disk_image = DISK_IMAGE
    if params.phystype:
        node.hardware_type = params.phystype

    iface = node.addInterface("eth1")
    ip    = "%s%d" % (BASE_IP, i + 2)  # 10.10.1.2, .3, ...
    iface.addAddress(pg.IPv4Address(ip, "255.255.255.0"))
    lan.addInterface(iface)

    nodes.append(node)
    ips.append(ip)

# ---------- build testConfig2.txt ----------
config_lines = ["f 0"]
for idx, ip in enumerate(ips):
    config_lines.append("replica %s:%d" % (ip, PORT_START + idx))
config_text = "\\n".join(config_lines)

clone_cmd  = "git clone %s ~/vrpaxos" % GIT_URL
config_cmd = "echo -e \"%s\" > ~/testConfig2.txt" % config_text

run_cmds = [
    "cd ~/vrpaxos && ./bench/replica -c ~/testConfig2.txt -i 0 -m vr",
    "cd ~/vrpaxos && ./bench/replica -c ~/testConfig2.txt -i 1 -w -m vr",
    "cd ~/vrpaxos && ./bench/replica -c ~/testConfig2.txt -i 2 -m vr",
    "cd ~/vrpaxos && ./bench/client  -c ~/testConfig2.txt -m vr -n 1000 -t 1 -w 5 -l latency.txt"
]

for idx, node in enumerate(nodes):
    node.addService(pg.Execute(shell="bash", command=clone_cmd))
    node.addService(pg.Execute(shell="bash", command=config_cmd))
    node.addService(pg.Execute(shell="bash", command=run_cmds[idx]))

# ---------- output ----------
pc.printRequestRSpec(request)
