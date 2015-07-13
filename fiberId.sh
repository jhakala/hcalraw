#!/bin/bash

RUN=$1
FILE=root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal/LS1/USC_${RUN}.root

echo "VME:"
./oneRun.py --file1=${FILE} --feds1=HCAL  --patterns | ./diff.py data/ref_vme_G.txt
echo
echo "uTCA:"
./oneRun.py --file1=${FILE} --feds1=uHBEF --patterns | ./diff.py data/ref_utca_G.txt