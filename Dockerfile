FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN adduser --disabled-password --gecos "" trmnl
USER trmnl

WORKDIR /app
COPY . /app

RUN uv sync --locked

EXPOSE 8000
CMD ["uv", "run", "gunicorn", "-w", "4", "--timeout", "120", "-b", "0.0.0.0:8000", "main:create_app()"]
