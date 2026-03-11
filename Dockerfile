# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --upgrade pip setuptools wheel

COPY pyproject.toml README.md LICENSE ./
COPY reconfsm/ ./reconfsm/

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install .


FROM python:3.12-slim AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends graphviz && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY reconfsm/ /app/reconfsm/
COPY examples/ /app/examples/

WORKDIR /app

RUN useradd --create-home reconfsm
USER reconfsm

CMD ["/bin/bash"]
