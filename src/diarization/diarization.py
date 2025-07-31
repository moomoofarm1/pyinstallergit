#!/usr/bin/env python
"""
diarization.py
==============

Light-weight wrapper around **pyannote-audio** speaker-diarization that works
both as a command-line tool *and* as an importable library.

Usage from the shell
--------------------
$ python diarization.py my_audio.wav --token HF_TOKEN_VALUE
#             └──── input file         └──── HuggingFace token
$ python diarization.py -h             # full help

Programmatic use
----------------
from diarization import diarize_file, load_pipeline

diarize_file(
    audio_path="my_audio.wav",
    output_rttm="my_audio.rttm",
    hf_token="HF_TOKEN_VALUE"
)
"""

from __future__ import annotations

import argparse
import os
import pathlib
from typing import Optional

import torch
from pyannote.audio import Pipeline

__all__ = ["load_pipeline", "diarize_file"]


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #
def load_pipeline(
    hf_token: str,
    *,
    device: Optional[str] = None,
    model: str = "pyannote/speaker-diarization-3.1",
) -> Pipeline:
    """
    Load the pyannote speaker-diarization pipeline.

    Parameters
    ----------
    hf_token : str
        Valid HuggingFace access token with permission for the model.
    device : str | None, default None
        "cpu", "cuda", or None (auto-detect GPU if available).
    model : str, default "pyannote/speaker-diarization-3.1"
        Model repository on 🤗 Hub.

    Returns
    -------
    Pipeline
        Initialised and GPU/CPU-placed pipeline.
    """
    pipeline = Pipeline.from_pretrained(model, use_auth_token=hf_token)

    # Auto-select device unless the caller forces one
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    pipeline.to(torch.device(device))

    return pipeline


def diarize_file(
    audio_path: str | os.PathLike,
    output_rttm: str | os.PathLike | None = None,
    *,
    hf_token: str,
    device: Optional[str] = None,
) -> None:
    """
    Run diarization on ``audio_path`` and write an RTTM file.

    Parameters
    ----------
    audio_path : str or PathLike
        Path to a mono/16-kHz WAV (or any ffmpeg-readable) file.
    output_rttm : str or PathLike | None, default None
        If ``None``, write ``<audio stem>_pyannoteaudio.rttm`` next to input.
    hf_token : str
        HuggingFace access token.
    device : str | None, default None
        Force "cpu" or "cuda"; ``None`` = auto-detect.
    """
    audio_path = pathlib.Path(audio_path)
    if output_rttm is None:
        output_rttm = audio_path.with_suffix("").with_name(
            audio_path.stem + "_pyannoteaudio.rttm"
        )

    pipeline = load_pipeline(hf_token, device=device)
    diarization = pipeline(str(audio_path))

    output_rttm = pathlib.Path(output_rttm)
    with output_rttm.open("w") as fp:
        diarization.write_rttm(fp)

    # Optional: print summary to stdout
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        print(f"start={turn.start:.1f}s  stop={turn.end:.1f}s  speaker_{speaker}")

    print(f"\n✅ RTTM saved to: {output_rttm.resolve()}")


# --------------------------------------------------------------------------- #
# Command-line interface                                                      #
# --------------------------------------------------------------------------- #
def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="diarization.py",
        description="Run pyannote speaker-diarization from the terminal.",
    )
    p.add_argument("audio", help="Path to input audio (wav/mp3/flac…)")

    p.add_argument(
        "-o",
        "--output",
        metavar="RTTM",
        help="Output RTTM file (default: <input>_pyannoteaudio.rttm)",
    )
    p.add_argument(
        "--token",
        help="HuggingFace access token "
        "(or set the environment variable HF_TOKEN).",
    )
    p.add_argument(
        "--cpu",
        action="store_true",
        help="Force CPU even if a CUDA-capable GPU is available.",
    )
    return p


def _cli() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    # 1) Resolve input and output paths
    audio_path = pathlib.Path(args.audio)
    if not audio_path.exists():
        parser.error(f"Audio file not found: {audio_path}")

    output_rttm = args.output

    # 2) Resolve HF token
    hf_token = args.token or os.getenv("HF_TOKEN")
    if not hf_token:
        parser.error(
            "🤗 HuggingFace access token missing. Provide --token or set HF_TOKEN."
        )

    # 3) Choose device
    device = "cpu" if args.cpu else None

    # 4) Run diarization
    diarize_file(audio_path, output_rttm, hf_token=hf_token, device=device)


if __name__ == "__main__":
    _cli()
