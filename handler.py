"""
RunPod Serverless handler for Demucs (htdemucs) stem separation.

Input:  { "audio_url": "https://...", "model": "htdemucs", "output_format": "wav" }
Output: { "stems": { "drums": "<url>", "bass": "<url>", "vocals": "<url>", "other": "<url>" } }
"""

import os
import subprocess
import tempfile
from pathlib import Path

import runpod
from runpod.serverless.utils.rp_upload import upload_file_to_bucket


def download_audio(url: str, output_path: str) -> None:
    """Download audio file from URL."""
    import requests
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)


def run_demucs(input_path: str, output_dir: str, model: str = "htdemucs") -> dict[str, str]:
    """Run Demucs separation and return dict of stem_name -> local file path."""
    cmd = [
        "python", "-m", "demucs",
        "--name", model,
        "--out", output_dir,
        "--mp3" if os.environ.get("OUTPUT_MP3") else "--float32",
        input_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    # Demucs outputs to: output_dir/<model>/<filename_without_ext>/
    input_name = Path(input_path).stem
    stems_dir = Path(output_dir) / model / input_name

    stem_paths = {}
    for stem_file in stems_dir.iterdir():
        stem_name = stem_file.stem  # "drums", "bass", "vocals", "other"
        stem_paths[stem_name] = str(stem_file)

    return stem_paths


def handler(event: dict) -> dict:
    """RunPod handler: download audio, run Demucs, upload stems, return URLs."""
    input_data = event.get("input", {})
    audio_url = input_data.get("audio_url")
    model = input_data.get("model", "htdemucs")

    if not audio_url:
        return {"error": "audio_url is required"}

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download audio
        input_path = os.path.join(tmpdir, "input_audio.wav")
        try:
            download_audio(audio_url, input_path)
        except Exception as e:
            return {"error": f"Failed to download audio: {str(e)[:200]}"}

        # Run Demucs
        output_dir = os.path.join(tmpdir, "output")
        try:
            stem_paths = run_demucs(input_path, output_dir, model)
        except subprocess.CalledProcessError as e:
            return {"error": f"Demucs failed: {e.stderr[:200] if e.stderr else str(e)[:200]}"}

        # Upload stems to configured bucket and collect URLs
        stem_urls = {}
        for stem_name, local_path in stem_paths.items():
            try:
                url = upload_file_to_bucket(local_path)
                stem_urls[stem_name] = url
            except Exception as e:
                return {"error": f"Failed to upload {stem_name}: {str(e)[:200]}"}

    return {"stems": stem_urls}


runpod.serverless.start({"handler": handler})
