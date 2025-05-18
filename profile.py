import geni.portal as portal
import geni.rspec.pg as pg

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
params = pc.bindParameters()

switch = pg.Switch("switch")
switch.hardware_type = params.phystype
switch_ifs = [switch.addInterface() for _ in range(4)]

def add_node(idx, name, cmd):
    node = rspec.RawPC(name)
    node.hardware_type = "xl170"
    node.disk_image = IMG
    iface = node.addInterface()
    ip_addr = "{}{}".format(BASE_IP, idx + 1)
    iface.addAddress(pg.IPv4Address(ip_addr, NETMASK))

    link = rspec.L1Link("link{}".format(idx))
    link.addInterface(iface)
    link.addInterface(switch_ifs[idx])

    # Prepare testConfig2.txt content with correct IPs
    config_lines = [
        "f 0",
        "replica {}2:8080".format(BASE_IP),
        "replica {}3:8081".format(BASE_IP),
        "replica {}4:8082".format(BASE_IP)
    ]
    config_str = "\\n".join(config_lines)

    # Compose bash commands: install deps, clone repo, write config, run command
    script = (
        "sudo apt-get update && "
        "sudo apt-get install -y git build-essential && "
        "git clone {repo} {dir} && "
        "echo -e \"{config}\" > {dir}/testConfig2.txt && "
        "cd {dir} && "
        "{cmd}"
    ).format(repo=REPO, dir=DIR, config=config_str, cmd=cmd)

    node.addService(pg.Execute(shell="bash", command=script))


# Add nodes: replicas and client with witness on node1 (index 1)
add_node(0, "node0", "./bench/replica -c ./testConfig2.txt -i 0 -m vr")
add_node(1, "node1", "./bench/replica -c ./testConfig2.txt -i 1 -w -m vr")  # witness with -w flag
add_node(2, "node2", "./bench/replica -c ./testConfig2.txt -i 2 -m vr")
add_node(3, "node3", "./bench/client  -c ./testConfig2.txt -m vr -n 1000 -t 1 -w 5 -l latency.txt")

pc.printRequestRSpec(rspec)
