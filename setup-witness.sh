#!/bin/bash
sudo apt-get update 
sudo apt-get install -y build-essential git pkg-config protobuf-compiler libprotobuf-dev libevent-dev libssl-dev libunwind-dev libgtest-dev
git clone https://github.com/A1ex-Fu/vrpaxos.git /local/vrpaxos
cd /local/vrpaxos || exit 1
cat >/local/vrpaxos/testConfig2.txt <<EOF
f 0
replica 10.10.1.2:8080
replica 10.10.1.3:8081
replica 10.10.1.4:8082
EOF
cd /local/vrpaxos
make
cd /local
# nohup ./bench/replica -c testConfig2.txt -i "$1" -w -m vr &
# tail -f /dev/null


git clone https://github.com/UWSysLab/specpaxos.git
cd specpaxos || exit 1
cat >/local/specpaxos/testConfig2.txt <<EOF
f 0
replica 10.10.1.2:8080
replica 10.10.1.3:8081
replica 10.10.1.4:8082
EOF
cd /local/specpaxos
make
./bench/replica -c ./testConfig.txt -i 1 -m spec