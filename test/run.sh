#!/bin/sh

export PYTHONPATH=PYTHONPATH:../src/
python chatserver.py &
python chatclient.py
