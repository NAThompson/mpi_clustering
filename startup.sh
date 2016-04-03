#!/bin/bash

sudo apt-get update
sudo apt-get install -y libopenmpi-dev openmpi-bin git emacs gcc
echo "StrictHostKeyChecking no" | sudo tee --append /etc/ssh/ssh_config
echo "HashKnownHosts No" | sudo tee --append ~/.ssh/ssh_config
