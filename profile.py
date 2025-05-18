import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

IMG = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
NETMASK = "255.255.255.0"
BASE_IP = "10.10.1."
REPO = "https://github.com/A1ex-Fu/vrpaxos.git"
DIR = "/local/repository/vrpaxos"

pc = portal.Context()
rspec = pc.makeRequestRSpec()

pc.defineParameter("phystype", "Switch type",
                   portal.ParameterType.STRING, "dell-s4048",
                   [("mlnx-sn2410", "Mellanox"), ("dell-s4048", "Dell")])
pc.defineParameter("bandwidth", "Link bandwidth Mbps",
                   portal.ParameterType.INTEGER, 1000)
pc.defineParameter("latency", "Link latency ms",
                   portal.ParameterType.INTEGER, 0)
params = pc.bindParameters()

switch = emulab.Switch("switch")
switch.hardware_type = params.phystype

nodes = []
switch_ifs = []

for i in range(4):
    node = rspec.RawPC("node{}".format(i))
    node.hardware_type = "xl170"
    node.disk_image = IMG
    iface = node.addInterface()
    ip_addr = "{}{}".format(BASE_IP, i + 1)
    iface.addAddress(pg.IPv4Address(ip_addr, NETMASK))
    nodes.append(node)

    sw_iface = switch.addInterface()
    switch_ifs.append(sw_iface)

    # Create L1Link between node interface and switch interface
    link = rspec.L1Link("link{}".format(i))
    link.addInterface(iface)
    link.addInterface(sw_iface)

    # Add bandwidth and latency shaping on this link
    link.bandwidth = params.bandwidth  # Mbps
    link.latency = params.latency       # ms

def add_node_script(idx, node):
    config_lines = [
        "f 0",
        "replica {}2:8080".format(BASE_IP),
        "replica {}3:8081".format(BASE_IP),
        "replica {}4:8082".format(BASE_IP)
    ]
    config_str = "\\n".join(config_lines)

    if idx == 0:
        cmd = "./bench/replica -c ./testConfig2.txt -i 0 -m vr"
    elif idx == 1:
        cmd = "./bench/replica -c ./testConfig2.txt -i 1 -w -m vr"
    elif idx == 2:
        cmd = "./bench/replica -c ./testConfig2.txt -i 2 -m vr"
    else:
        cmd = "./bench/client -c ./testConfig2.txt -m vr -n 1000 -t 1 -w 5 -l latency.txt"

    script = (
        "sudo apt-get update && "
        "sudo apt-get install -y git build-essential && "
        "git clone {repo} {dir} && "
        "echo -e \"{config}\" > {dir}/testConfig2.txt && "
        "cd {dir} && "
        "{cmd}"
    ).format(repo=REPO, dir=DIR, config=config_str, cmd=cmd)

    node.addService(pg.Execute(shell="bash", command=script))

for i, node in enumerate(nodes):
    add_node_script(i, node)

pc.printRequestRSpec(rspec)
