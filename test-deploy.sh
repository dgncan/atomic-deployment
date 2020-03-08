#!/usr/bin/env bash
cp -fp deploy.py example-project/deploy.py
cd example-project
python deploy.py $1 $2 $3
