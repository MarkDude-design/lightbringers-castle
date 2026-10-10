FROM python:3.12-slim-bookworm
WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN python -m pip install --no-cache-dir -r requirements.lock
RUN useradd --uid 1001 --create-home probe && chown 1001:1001 /app
COPY --chown=1001:1001 runtime_probe.py workflow.py worker.py ./
ENV LOG_LEVEL=WARNING PYTHONUNBUFFERED=1
USER 1001
CMD ["python", "worker.py"]
