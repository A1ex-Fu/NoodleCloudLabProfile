#!/bin/bash
apt-get update -y
apt-get install -y git build-essential
git clone https://github.com/A1ex-Fu/vrpaxos.git /local/vrpaxos
cd vrpaxos
cat >/local/vrpaxos/testConfig2.txt <<EOF
f 0
replica 10.10.1.2:8080
replica 10.10.1.3:8081
replica 10.10.1.4:8082
EOF
cd /local/vrpaxos
make
./bench/client -c testConfig2.txt -m vr -n 1000 -t 1 -w 5 -l latency.txt &