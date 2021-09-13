#!/bin/sh
python3 -m astool jp dl_master
python3 -m astool jp pkg_sync main card:%
