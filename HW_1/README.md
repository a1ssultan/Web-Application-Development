# Homework 1

Simple FastAPI application running inside a Docker container.

## Run locally

Install dependencies:

```bash
uv sync
```

Run the application:

```bash
uv run python main.py
```

The application will be available at:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

## Build Docker image

```bash
docker build -t hw-1 .
```

## Run Docker container

```bash
docker run -e HOST=0.0.0.0 -e PORT=8000 -p 8000:8000 hw-1
```

Then open:

```text
http://localhost:8000
```

## Environment variables

The application uses two environment variables:

- `HOST`
- `PORT`

For example:

```bash
docker run -e HOST=0.0.0.0 -e PORT=8000 -p 8000:8000 hw-1
```

If the variables are not provided, the application uses:

```text
HOST=0.0.0.0
PORT=8000
```

## Project structure

```text
HW_1/
├── main.py
├── Dockerfile
├── .dockerignore
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```