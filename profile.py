# -*- coding: utf-8 -*-
import geni.portal as portal
import geni.rspec.pg as pg

IMG      = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
NETMASK  = "255.255.255.0"
BASE_IP  = "10.10.1."
NODE_HW  = "xl170"
SW_DEF   = "dell-s4048"
REPO_URL = "https://github.com/A1ex-Fu/vrpaxos.git"
REPO_DIR = "/local/repository/vrpaxos"

pc = portal.Context()
rspec = pc.makeRequestRSpec()

pc.defineParameter(
    "phystype", "Switch type",
    portal.ParameterType.STRING, SW_DEF,
    [("mlnx-sn2410","Mellanox SN2410"),("dell-s4048","Dell S4048")]
)
p = pc.bindParameters()

sw = rspec.Switch("sw")
sw.hardware_type = p.phystype
swif = [sw.addInterface() for _ in range(4)]

def node(idx, name, cmd):
    n = rspec.RawPC(name)
    n.hardware_type = NODE_HW
    n.disk_image = IMG
    iface = n.addInterface()
    iface.addAddress(pg.IPv4Address("{}{}".format(BASE_IP,idx+1), NETMASK))
    ln = rspec.L1Link("l{}".format(idx))
    ln.addInterface(iface)
    ln.addInterface(swif[idx])

    cfg = "\\n".join([
        "f 0",
        "replica {}2:8080".format(BASE_IP),
        "replica {}3:8081".format(BASE_IP),
        "replica {}4:8082".format(BASE_IP)
    ])

    setup = (
        "sudo apt -y update && "
        "sudo apt -y install git build-essential && "
        "git clone {0} {1} && "
        "echo -e \"{2}\" > {1}/testConfig2.txt && "
        "cd {1} && {3}"
    ).format(REPO_URL, REPO_DIR, cfg, cmd)

    n.addService(pg.Execute(shell="bash", command=setup))

node(0,"node0","./bench/replica -c ./testConfig2.txt -i 0 -m vr")
node(1,"node1","./bench/replica -c ./testConfig2.txt -i 1 -w -m vr")
node(2,"node2","./bench/replica -c ./testConfig2.txt -i 2 -m vr")
node(3,"node3","./bench/client  -c ./testConfig2.txt -m vr -n 1000 -t 1 -w 5 -l latency.txt")

pc.printRequestRSpec(rspec)
