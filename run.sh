# from project root
export LS_URL="http://localhost:8080"
export LS_API_TOKEN="YOUR_TOKEN"
export LS_PROJECT_ID="1"

apt update && apt upgrade && apt install -y sudo nano

chmod +x scripts/*.sh

scripts/00_bootstrap.sh          # install system deps, Miniconda, uv
scripts/01_create_conda_env.sh   # separate R/reticulate env (optional)
scripts/02_git_init.sh
scripts/03_uv_sync.sh
scripts/04_run_demo.sh           # optional demo
scripts/05_build_binary.sh
