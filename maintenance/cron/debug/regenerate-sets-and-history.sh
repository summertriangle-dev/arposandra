#!/bin/bash

python3 mtrack/mtrack.py -X -x jp $(python3 -m astool jp current_master)

python3 mtrack/run_script.py -f mtrack/init-sets.sql

python3 mtrack/mtrack.py en $(python3 -m astool en current_master)