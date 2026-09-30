#!/bin/sh
set -eu
# Workstation traffic may retrieve images through HTTPS but cannot send DICOM.
# The acquisition emulator runs inside the server VM.
iptables -C DOCKER-USER -p tcp --dport 11112 ! -s 192.168.178.10 -j REJECT 2>/dev/null || iptables -I DOCKER-USER -p tcp --dport 11112 ! -s 192.168.178.10 -j REJECT
