FROM python:3.11-slim

ARG USER=app
ARG UID=1000
ENV APP_HOME=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libffi-dev \
       libssl-dev \
       ca-certificates \
       curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid ${UID} ${USER}

WORKDIR ${APP_HOME}

COPY --chown=${USER}:${USER} requirements.txt ${APP_HOME}/
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=${USER}:${USER} . ${APP_HOME}/

USER ${USER}

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/metrics || exit 1

CMD ["python", "-u", "app.py"]