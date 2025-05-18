# CloudLab profile: 4 nodes (replica0, witness, replica2, client) on one LAN
# With configurable LAN speed and node type
import geni.portal as portal
import geni.rspec.pg as pg

class G:
    image   = ("urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD")
    base_ip = "10.10.1."
    mask    = "255.255.255.0"

pc = portal.Context()
rs = pc.makeRequestRSpec()

# Configurable parameters
pc.defineParameter("phystype",  "Node type", portal.ParameterType.STRING, "")
pc.defineParameter("lanMbps",   "LAN speed (Mb/s)",
                   portal.ParameterType.INTEGER, 1000,
                   [(100, "100 Mbps"), (1000, "1 Gbps"), (10000, "10 Gbps")])
params = pc.bindParameters()

# ---------- LAN ----------
lan = rs.LAN("lan0")
lan.bandwidth = params.lanMbps

# ---------- Node definitions ----------
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

# ---------- Helper function ----------
def upload_and_run_script(node, script_name, run_args=""):
    path = "/local/repository/" + script_name
    node.addService(pg.Execute(shell="bash",
        command="chmod +x {0} && sudo {0} {1}".format(path, run_args)))

# ---------- Upload and run startup scripts ----------
upload_and_run_script(nodes[0], "setup-replica.sh", "0")
upload_and_run_script(nodes[1], "setup-witness.sh", "1")
upload_and_run_script(nodes[2], "setup-replica.sh", "2")
upload_and_run_script(nodes[3], "setup-client.sh",  "3")

# ---------- Finalize ----------
pc.printRequestRSpec(rs)
