# CloudLab profile: 4 nodes (replica0, witness, replica2, client) on one LAN
# Now fixed to match successful profiles' structure
import geni.portal as portal
import geni.rspec.pg as pg

class G:
    image   = ("urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD")
    base_ip = "10.10.1."
    mask    = "255.255.255.0"

pc = portal.Context()
rs = pc.makeRequestRSpec()

# Parameters
pc.defineParameter("phystype",  "Node type", portal.ParameterType.STRING, "")
pc.defineParameter("lanMbps",   "LAN speed (Mb/s)",
                   portal.ParameterType.INTEGER, 1000,
                   [(100, "100 Mbps"), (1000, "1 Gbps"), (10000, "10 Gbps")])
pc.defineParameter("user", "User", portal.ParameterType.STRING, "yourusername")
params = pc.bindParameters()

# LAN
lan = rs.LAN("lan0")
lan.bandwidth = params.lanMbps

# Nodes
roles = ["replica0", "witness", "replica2", "client"]
setup_scripts = ["setup-replica.sh", "setup-witness.sh", "setup-replica.sh", "setup-client.sh"]
run_args = ["0", "1", "2", "3"]

for idx, role in enumerate(roles):
    node = rs.RawPC(role)
    node.disk_image = G.image
    if params.phystype:
        node.hardware_type = params.phystype

    iface = node.addInterface("eth1")
    iface.addAddress(pg.IPv4Address("%s%d" % (G.base_ip, idx+2), G.mask))
    lan.addInterface(iface)

    # Set up startup script (no sudo, no chmod, run as user)
    script = "/local/repository/" + setup_scripts[idx]
    cmd = "%s %s" % (script, run_args[idx])
    node.addService(pg.Execute(shell="bash", command="sudo -u {} -H {}".format(params.user, cmd)))

pc.printRequestRSpec(rs)
