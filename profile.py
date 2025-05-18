import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

class G:
    image = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
    base_ip = "10.10.1."
    mask = "255.255.255.0"
    repo = "https://github.com/A1ex-Fu/vrpaxos.git"

pc = portal.Context()
request = pc.makeRequestRSpec()

# Parameters
pc.defineParameter("lanMbps",   "LAN speed (Mb/s)", portal.ParameterType.INTEGER, 1000,
                   [(100, "100"), (1000, "1000"), (10000, "10000")])
params = pc.bindParameters()

# LAN
lan = request.LAN("lan0")
lan.bandwidth = params.lanMbps

roles = ["replica0", "witness", "replica2", "client"]
nodes = []

# Create nodes and assign IPs
for idx, role in enumerate(roles):
    node = request.RawPC(role)
    node.disk_image = G.image


    iface = node.addInterface("eth1")
    iface.addAddress(pg.IPv4Address(f"{G.base_ip}{idx+2}", G.mask))
    lan.addInterface(iface)
    nodes.append(node)

# Add startup script logic
def upload_and_run_script(node, script_name, run_args=""):
    path = f"/local/repository/{script_name}"
    node.addService(pg.Execute(shell="bash",
        command=f"chmod +x {path} && sudo {path} {run_args}"))

# Upload and execute the setup scripts
upload_and_run_script(nodes[0], "setup-replica.sh", "0")
upload_and_run_script(nodes[1], "setup-witness.sh", "1")
upload_and_run_script(nodes[2], "setup-replica.sh", "2")
upload_and_run_script(nodes[3], "setup-client.sh",  "3")

# Output RSpec
pc.printRequestRSpec(request)
