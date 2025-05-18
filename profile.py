import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

class G:
    image   = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
    base_ip = "10.10.1."
    mask    = "255.255.255.0"

pc = portal.Context()
rs = pc.makeRequestRSpec()

# Parameters
pc.defineParameter("phystype",  "Node type", portal.ParameterType.STRING, "")
pc.defineParameter("lanMbps",   "LAN speed (Mb/s)",
                   portal.ParameterType.INTEGER, 1000,
                   [(100, "100"), (1000, "1000"), (10000, "10000")])
params = pc.bindParameters()

# Create shared LAN
lan = rs.LAN("lan0")
lan.bandwidth = params.lanMbps  # in Mbps

# Node roles
roles = ["replica0", "witness", "replica2", "client"]
nodes = []

for idx, role in enumerate(roles):
    node = rs.RawPC(role)
    node.disk_image = G.image
    if params.phystype:
        node.hardware_type = params.phystype

    iface = node.addInterface("eth1")
    iface.addAddress(pg.IPv4Address("{}{}".format(G.base_ip, idx+2), G.mask))
    lan.addInterface(iface)

    nodes.append(node)

# Assign scripts via /local/repository (Git checkout directory)
nodes[0].addService(pg.Execute(shell="bash", command="/local/repository/setup-replica.sh 0"))
nodes[1].addService(pg.Execute(shell="bash", command="/local/repository/setup-witness.sh 1"))
nodes[2].addService(pg.Execute(shell="bash", command="/local/repository/setup-replica.sh 2"))
nodes[3].addService(pg.Execute(shell="bash", command="/local/repository/setup-client.sh 3"))

pc.printRequestRSpec(rs)
