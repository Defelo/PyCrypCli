FROM python:3.11.0-alpine AS builder

RUN apk add --no-cache build-base gcc musl-dev libffi-dev python3-dev openssl-dev cargo

WORKDIR /build

RUN pip install poetry

COPY pyproject.toml /build/
COPY poetry.lock /build/

RUN poetry install -n --no-root

COPY README.md /build/
COPY PyCrypCli /build/PyCrypCli

RUN poetry build


FROM python:3.11.0-alpine

LABEL org.opencontainers.image.source=https://github.com/Defelo/PyCrypCli

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install /tmp/*.whl && rm /tmp/*.whl

CMD ["pycrypcli"]
