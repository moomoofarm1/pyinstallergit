# PyInstaller Active Learning Demo

This project demonstrates setting up a Python environment using `uv` and a separate Conda environment for R/reticulate. It also includes an example of fine-tuning a RoBERTa model using labeled data from Label Studio.

## Bootstrap

Run `scripts/00_bootstrap.sh` to install basic tools (including `git`), `micromamba`, and `uv`.

```bash
bash scripts/00_bootstrap.sh
```

## Conda Environment

Create a minimal Conda environment containing `reticulate` using micromamba:

```bash
bash scripts/01_create_conda_env.sh
```

Activate it with `micromamba activate reticulate_env`.

## PyInstaller Environment

Create a Python virtual environment managed by `uv` and install required packages:

```bash
bash scripts/02_setup_pyinstaller_env.sh
```

This uses `py_packages.txt` for package versions. Modify that file to control future package installs.

## Demo: Fine-tune RoBERTa

After setting up the environments, run the demo script:

```bash
bash scripts/03_finetune_demo.sh --label-studio-url <URL> --api-key <KEY> --project-id <ID>
```

This script downloads labeled data from Label Studio and fine-tunes a RoBERTa model.

## Notes

- The Conda environment does not contain PyInstaller.
- The Python environment managed with `uv` installs PyInstaller and project dependencies.
