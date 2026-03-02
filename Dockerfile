FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir demucs==4.0.1 requests runpod

RUN python -c "import demucs.pretrained; demucs.pretrained.get_model('htdemucs')"

COPY handler.py /handler.py

CMD ["python", "/handler.py"]
