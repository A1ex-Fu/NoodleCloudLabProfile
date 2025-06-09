# CloudLab profile: Fixed 4-node LAN with same node type and LAN speed options as smalllan
import geni.portal as portal
import geni.rspec.pg as pg

class G:
    image   = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
    base_ip = "10.10.1."
    mask    = "255.255.255.0"

pc = portal.Context()
rs = pc.makeRequestRSpec()

# Use NODETYPE param to match original smalllan script behavior
pc.defineParameter("phystype",  "Optional physical node type",
                   portal.ParameterType.NODETYPE, "",
                   longDescription="Pick a single physical node type (pc3000,d710,etc) " +
                   "instead of letting the resource mapper choose for you.")

# Same LAN speed options
pc.defineParameter("lanMbps", "LAN speed (Mb/s)",
                   portal.ParameterType.INTEGER, 1000,
                   [(100, "100 Mbps"), (1000, "1 Gbps"), (10000, "10 Gbps")])

# Optional code branch param (safe to keep for flexibility)
pc.defineParameter("branch", "Git branch of EMU or app code to checkout", portal.ParameterType.STRING, "main")
params = pc.bindParameters()

# Create LAN
lan = rs.LAN("lan0")
lan.bandwidth = params.lanMbps

# Node names and setup scripts
roles = ["replica0", "witness", "replica2", "client"]
scripts = ["setup-replica.sh", "setup-witness.sh", "setup-replica.sh", "setup-client.sh"]

# Create and configure each node
for i, role in enumerate(roles):
    node = rs.RawPC(role)
    node.disk_image = G.image
    if params.phystype:
        node.hardware_type = params.phystype

    iface = node.addInterface("eth1")
    ip = G.base_ip + str(i + 2)
    iface.addAddress(pg.IPv4Address(ip, G.mask))
    lan.addInterface(iface)

    # Setup command
    script = f"/local/repository/{scripts[i]}"
    if role == "client":
        targets = "10.10.1.2 10.10.1.3 10.10.1.4"
        cmd = f"bash {script} {params.branch} {targets}"
    else:
        client_ip = G.base_ip + "5"
        cmd = f"bash {script} {params.branch} {i} {ip} {client_ip}"

    node.addService(pg.Execute(shell="bash", command=f"sudo -u geniuser -H {cmd}"))

pc.printRequestRSpec(rs)
