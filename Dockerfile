# InfoShield backend for Hugging Face Spaces (Docker SDK).
# Serves the prebuilt cache instantly; downloads the local ML models on first
# boot for the live "Check with InfoShield" draft analysis. Gemini key comes
# from the Space secret GEMINI_API_KEY (never baked into the image).
FROM python:3.11-slim

# Non-root user (HF Spaces best practice) with writable caches under $HOME.
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    HF_HOME=/home/user/.cache/huggingface \
    INFOSHIELD_HOST=0.0.0.0 \
    INFOSHIELD_PORT=7860 \
    PYTHONUNBUFFERED=1

WORKDIR /home/user/app

COPY --chown=user backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user backend/ ./

USER user
EXPOSE 7860
CMD ["python", "app.py"]
