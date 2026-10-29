#!/usr/bin/env bash
set -e

source /opt/conda/etc/profile.d/conda.sh
conda activate bivme311

cd /biv-me

JUPYTER_PORT="${JUPYTER_PORT:-8090}"
JUPYTER_ROOT="${JUPYTER_ROOT:-/biv-me}"

echo "Starting JupyterLab on port ${JUPYTER_PORT}..."
jupyter lab \
    --ip=0.0.0.0 \
    --port="${JUPYTER_PORT}" \
    --no-browser \
    --ServerApp.root_dir="${JUPYTER_ROOT}" \
    --ServerApp.base_url="/biv-me/lab/" \
    --NotebookApp.token='' \
    --NotebookApp.password='' \
    --ServerApp.allow_root=True 
    #>/tmp/jupyter.log 2>&1 &

#echo "JupyterLab log: /tmp/jupyter.log"

exec "$@"
