# from project root
export LS_URL="http://localhost:8080"
export LS_API_TOKEN="YOUR_TOKEN"
export LS_PROJECT_ID="1"

apt update && apt upgrade && \
  apt install --yes sudo nano && \
  bash scripts/00_bootstrap.sh && \
  source ~/.bashrc
  
bash scripts/01_create_conda_env.sh && bash scripts/02_git_init.sh
chmod +x scripts/03_uv_sync.sh
bash scripts/03_uv_sync.sh
# uv run pyinstaller --name roberta_active --onefile src/__main__.py

chmod +x scripts/*.sh

scripts/00_bootstrap.sh          # install system deps, Miniconda, uv
scripts/01_create_conda_env.sh   # separate R/reticulate env (optional)
scripts/02_git_init.sh
scripts/03_uv_sync.sh
scripts/04_run_demo.sh           # optional demo
scripts/05_build_binary.sh
