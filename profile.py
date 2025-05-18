#
# Profile: 1 witness, 2 replicas, 1 client on a single L1 switch.
#

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

class G:
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
    "phystype",
    "Switch type",
    portal.ParameterType.STRING,
    G.hw_sw,
    [("mlnx-sn2410", "Mellanox SN2410"),
     ("dell-s4048", "Dell S4048")]
)
params = pc.bindParameters()

sw = request.Switch("l1sw")
sw.hardware_type = params.phystype
sw_ifaces = [sw.addInterface() for _ in range(4)]

def make_node(idx, name, run_cmd):
    """Create node idx, connect to switch, install software, run_cmd."""
    node = request.RawPC(name)
    node.hardware_type = G.hw_node
    node.disk_image    = G.img

    iface = node.addInterface()
    ip    = f"{G.base_ip}{idx + 1}"
    iface.addAddress(pg.IPv4Address(ip, G.netmask))

    link = request.L1Link(f"link{idx}")
    link.addInterface(iface)
    link.addInterface(sw_ifaces[idx])

    cfg_lines = [
        "f 0",
        f"replica {G.base_ip}2:8080",
        f"replica {G.base_ip}3:8081",
        f"replica {G.base_ip}4:8082"
    ]
    cfg_text = "\\n".join(cfg_lines)

    setup = (
        "sudo apt update -y && "
        "sudo apt install -y git build-essential && "
        f"git clone {G.repo_url} {G.repo_dir} && "
        f"echo -e \"{cfg_text}\" > {G.repo_dir}/testConfig2.txt && "
        f"cd {G.repo_dir} && "
        f"{run_cmd}"
    )
    node.addService(pg.Execute(shell="bash", command=setup))
    return node


node0 = make_node(0, "node0",
                  "./bench/replica -c ./testConfig2.txt -i 0 -m vr")
node1 = make_node(1, "node1",
                  "./bench/replica -c ./testConfig2.txt -i 1 -w -m vr")
node2 = make_node(2, "node2",
                  "./bench/replica -c ./testConfig2.txt -i 2 -m vr")
node3 = make_node(3, "node3",
                  "./bench/client  -c ./testConfig2.txt -m vr -n 1000 -t 1 -w 5 -l latency.txt")

pc.printRequestRSpec(request)