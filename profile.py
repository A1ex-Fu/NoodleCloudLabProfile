"""This profile allocates N bare metal nodes and connects them together via a Dell or Mellanox switch with layer1 links.

Instructions:
Click on any node in the topology and choose the `shell` menu item. When your shell window appears, use `ping` to test the link.

You will be able to ping the other node through the switch fabric. We have installed a minimal configuration on your
switches that enables the ports that are in use, and turns on spanning-tree (RSTP) in case you inadvertently created a loop with your topology. All
unused ports are disabled. The ports are in Vlan 1, which effectively gives a single broadcast domain. If you want anything fancier, you will need
to open up a shell window to your switches and configure them yourself.

If your topology has more then a single switch, and you have links between your switches, we will enable those ports too, but we do not put them into
switchport mode or bond them into a single channel, you will need to do that yourself.

If you make any changes to the switch configuration, be sure to write those changes to memory. We will wipe the switches clean and restore a default
configuration when your experiment ends."""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

class GLOBALS:
    image = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
    base_ip = "192.168.1."
    netmask = "255.255.255.0"


pc = portal.Context()
request = pc.makeRequestRSpec()

# Read parameters.
pc.defineParameter("nr_nodes", "Number of nodes", portal.ParameterType.INTEGER, 3)
pc.defineParameter(
    "phystype",
    "Switch type",
    portal.ParameterType.STRING,
    "dell-s4048",
    [("mlnx-sn2410", "Mellanox SN2410"), ("dell-s4048", "Dell S4048")],
)
pc.defineParameter("user", "User", portal.ParameterType.STRING, "kwzhao")
pc.defineParameter("branch", "emu branch", portal.ParameterType.STRING, "main")
params = pc.bindParameters()

# Create the switch with the specified type.
switch = request.Switch("mysw")
switch.hardware_type = params.phystype

# Add interfaces to the switch dynamically.
switch_interfaces = []
for i in range(params.nr_nodes):
    iface = switch.addInterface()
    switch_interfaces.append(iface)

# Create the nodes dynamically based on the number specified.
for i in range(params.nr_nodes):
    node_name = "node{}".format(i)
    node = request.RawPC(node_name)
    node.hardware_type = "xl170"
    node.disk_image = GLOBALS.image

    # Add an interface to the node.
    iface = node.addInterface()

    # Assign an IP address based on the node index.
    ip_address = GLOBALS.base_ip + str(i)
    iface.addAddress(pg.IPv4Address(ip_address, GLOBALS.netmask))

    # Add a startup script.
    if i == 0:
        # The first node is the manager.
        worker_ips = " ".join([GLOBALS.base_ip + str(j) for j in range(1, params.nr_nodes)])
        command = "/local/repository/setup-manager.sh {} {}".format(params.branch, worker_ips)
    else:
        # All the rest are workers.
        command = "/local/repository/setup-worker.sh {} {} {} {}".format(params.branch, i - 1, ip_address, GLOBALS.base_ip + "0")
    node.addService(pg.Execute(shell="bash", command="sudo -u {} -H {}".format(params.user, command)))

    # Create a link between the node's interface and the corresponding switch interface.
    link = request.L1Link("link{}".format(i))
    link.addInterface(iface)
    link.addInterface(switch_interfaces[i])

# Output the RSpec.
pc.printRequestRSpec(request)
