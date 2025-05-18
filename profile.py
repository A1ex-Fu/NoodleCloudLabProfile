#
# 4 nodes (replica0, witness, replica2, client) on one LAN.
#
import geni.portal as portal
import geni.rspec.pg as pg

class G:
    image   = ("urn:publicid:IDN+emulab.net+image+emulab-ops//"
               "UBUNTU22-64-STD")
    base_ip = "10.10.1."
    mask    = "255.255.255.0"
    repo    = "https://github.com/A1ex-Fu/vrpaxos.git"

pc = portal.Context()
rs = pc.makeRequestRSpec()

pc.defineParameter("phystype",  "Node type", portal.ParameterType.STRING, "")
pc.defineParameter("lanMbps",   "LAN speed (Mb/s)",
                   portal.ParameterType.INTEGER, 1000,
                   [(100, "100"), (1000, "1000"), (10000, "10000")])
params = pc.bindParameters()

# ---------- LAN ----------
lan = rs.LAN("lan0")
lan.bandwidth = params.lanMbps

nodes = []
roles = ["replica0", "witness", "replica2", "client"]

for idx, role in enumerate(roles):
    n = rs.RawPC(role)
    n.disk_image = G.image
    if params.phystype:
        n.hardware_type = params.phystype
    iface = n.addInterface("eth1")
    iface.addAddress(pg.IPv4Address("%s%d" % (G.base_ip, idx+2), G.mask))
    lan.addInterface(iface)
    nodes.append(n)

# ---------- helper to drop a file ----------
def add_script(node, name, content):
    node.addFile(pg.File("/local/repository/" + name, content))
    node.addService(pg.Execute(shell="bash",
                    command="chmod +x /local/repository/%s" % name))

# ---------- upload the three scripts ----------
add_script(nodes[0], "setup-replica.sh", open("setup-replica.sh").read())
add_script(nodes[1], "setup-witness.sh", open("setup-witness.sh").read())
add_script(nodes[2], "setup-replica.sh", open("setup-replica.sh").read())
add_script(nodes[3], "setup-client.sh",  open("setup-client.sh").read())

# ---------- execute them ----------
nodes[0].addService(pg.Execute(shell="bash",
            command="/local/repository/setup-replica.sh 0"))
nodes[1].addService(pg.Execute(shell="bash",
            command="/local/repository/setup-witness.sh 1"))
nodes[2].addService(pg.Execute(shell="bash",
            command="/local/repository/setup-replica.sh 2"))
nodes[3].addService(pg.Execute(shell="bash",
            command="/local/repository/setup-client.sh 3"))

pc.printRequestRSpec(rs)
