# CloudLab profile: 4-node LAN, smalllan-style LAN setup, optional phystype
import geni.portal as portal
import geni.rspec.pg as pg

class G:
    image = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"

pc = portal.Context()
rs = pc.makeRequestRSpec()

# Parameters
pc.defineParameter("phystype", "Optional physical node type",
                   portal.ParameterType.NODETYPE, "",
                   longDescription="Pick a physical node type like c6525, d710, etc.")

pc.defineParameter("branch", "Git branch to checkout",
                   portal.ParameterType.STRING, "main")

params = pc.bindParameters()

# Create LAN like smalllan — no bandwidth setting
lan = pg.LAN("lan")

# Roles and setup scripts
roles = ["replica0", "witness", "replica2", "client"]
scripts = ["setup-replica.sh", "setup-witness.sh", "setup-replica.sh", "setup-client.sh"]

for i, role in enumerate(roles):
    node = rs.RawPC(role)
    node.disk_image = G.image
    if params.phystype:
        node.hardware_type = params.phystype

    iface = node.addInterface("if{}".format(i + 1))
    lan.addInterface(iface)

    script = f"/local/repository/{scripts[i]}"
    if role == "client":
        targets = "10.10.1.2 10.10.1.3 10.10.1.4"
        cmd = f"bash {script} {params.branch} {targets}"
    else:
        client_ip = "10.10.1.5"
        ip = f"10.10.1.{i+2}"
        cmd = f"bash {script} {params.branch} {i} {ip} {client_ip}"

    node.addService(pg.Execute(shell="bash", command=f"sudo -u geniuser -H {cmd}"))

pc.printRequestRSpec(rs)
