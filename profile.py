# CloudLab profile: 4 nodes (replica0, witness, replica2, client) on one LAN
import geni.portal as portal
import geni.rspec.pg as pg

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
                   [(100, "100 Mbps"), (1000, "1 Gbps"), (10000, "10 Gbps")])
pc.defineParameter("user", "Username to run startup scripts under", portal.ParameterType.STRING, "kwzhao")
pc.defineParameter("branch", "Git branch of EMU or app code to checkout", portal.ParameterType.STRING, "main")
params = pc.bindParameters()

# Create LAN
lan = rs.LAN("lan0")
lan.bandwidth = params.lanMbps

# Roles and associated setup scripts
roles = ["replica0", "witness", "replica2", "client"]
scripts = ["setup-replica.sh", "setup-witness.sh", "setup-replica.sh", "setup-client.sh"]

# Create nodes
for i, role in enumerate(roles):
    node = rs.RawPC(role)
    node.disk_image = G.image
    if params.phystype:
        node.hardware_type = params.phystype

    # Set up interface with IP address
    iface = node.addInterface("eth1")
    ip = G.base_ip + str(i + 2)  # e.g. 10.10.1.2 through .5
    iface.addAddress(pg.IPv4Address(ip, G.mask))
    lan.addInterface(iface)

    # Prepare script and command
    script_path = "/local/repository/{}".format(scripts[i])
    if role == "client":
        # Client connects to all replicas (IPs .2, .4) and witness (.3)
        targets = "10.10.1.2 10.10.1.3 10.10.1.4"
        cmd = "{} {} {}".format(script_path, params.branch, targets)
    else:
        # Pass: branch, node index, IP, client IP
        client_ip = G.base_ip + "5"
        cmd = "{} {} {} {} {}".format(script_path, params.branch, i, ip, client_ip)

    # Run as specified user, with home env
    node.addService(pg.Execute(shell="bash", command="sudo -u {} -H {}".format(params.user, cmd)))

# Print RSpec
pc.printRequestRSpec(rs)
