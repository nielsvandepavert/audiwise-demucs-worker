FROM runpod/base:0.6.2-cuda12.2.0

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    demucs==4.0.1 \
    requests \
    runpod

# Pre-download the htdemucs model so it's baked into the image (faster cold starts)
RUN python -c "import demucs.pretrained; demucs.pretrained.get_model('htdemucs')"

# Copy handler
COPY handler.py /handler.py

CMD ["python", "/handler.py"]
