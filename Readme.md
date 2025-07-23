# Pyinstallergit package structure
pyinstaller-roberta-demo/
├─ scripts/
│  ├─ 00_bootstrap.sh
│  ├─ 01_create_conda_env.sh
│  ├─ 02_git_init.sh
│  ├─ 03_uv_sync.sh
│  ├─ 04_run_demo.sh
│  ├─ 05_build_binary.sh
│  └─ lib_common.sh
├─ config/
│  └─ extra-packages.txt
├─ src/  (Python files as before)
├─ pyproject.toml
├─ uv.lock             (auto-generated)
├─ README.md
└─ .gitignore
