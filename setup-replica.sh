#!/bin/bash
# args: <replica-index>
set -ex
exec > /local/run.out 2>&1
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
./bench/replica -c testConfig2.txt -i "$1" -m vr &
