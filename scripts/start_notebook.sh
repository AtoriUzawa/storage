#!/usr/bin/env bash
set -e
cd /home/atori/workspace/storage
exec .venv/bin/jupyter lab --no-browser --ip=127.0.0.1 --port=8888 --ServerApp.root_dir=/home/atori/workspace/storage
