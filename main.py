import os

import uvicorn

from app import app


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("GUNICORN_WORKERS", "1"))
    use_gunicorn = os.getenv("USE_GUNICORN", "").strip().lower() in {"1", "true", "yes", "on"}
    if use_gunicorn:
        import subprocess
        subprocess.run(
            [
                "gunicorn",
                "app:app",
                "--bind",
                f"{host}:{port}",
                "--workers",
                str(workers),
                "--timeout",
                "120",
            ],
            check=False,
        )
        return
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
