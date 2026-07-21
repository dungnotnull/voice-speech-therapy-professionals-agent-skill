FROM python:3.12-slim

LABEL org.opencontainers.image.title="voice-speech-therapy-professionals"
LABEL org.opencontainers.image.description="Voice & Speech Therapy & Articulation Coach — Knowledge Pipeline"
LABEL org.opencontainers.image.version="2.0.0"

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY tools/ tools/
COPY skills/ skills/
COPY tests/ tests/
COPY SECOND-KNOWLEDGE-BRAIN.md ./

RUN pip install --no-cache-dir . && \
    chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from tools._config import load_config; load_config()" || exit 1

ENTRYPOINT ["python", "tools/knowledge_updater.py"]
CMD ["--help"]
