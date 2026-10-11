HEAD
# VilaCircula

PWA de demostración para Viladecans con API FastAPI.

## Ejecutar localmente

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Abre http://localhost:8001.

## Variables de entorno

Copia `.env.example` a `.env` y ajusta los valores antes de desplegar.

```env
VILACIRCULA_ENV=development
PORT=8000
HOST=0.0.0.0
VILACIRCULA_DATABASE=data/vilacircula.sqlite3
VILACIRCULA_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001
VILACIRCULA_ADMIN_KEY=change-me-with-a-long-random-secret
VILACIRCULA_MERCHANT_KEY=
VILACIRCULA_INITIAL_CASHIER_PASSWORD=Viladecans
VILACIRCULA_ALLOW_SELF_REDEEM=1
```

## Producción recomendada

- SQLite: solo demo/local
- PostgreSQL: recomendado para entorno real
- HTTPS obligatorio
- CORS restringido a dominios explícitos
- variables secretas solo del servidor

## Preparación para PostgreSQL + Alembic

La app ya incluye una base para migraciones con Alembic. Para usar PostgreSQL en un entorno real, configura estas variables:

```env
VILACIRCULA_ENV=production
VILACIRCULA_DATABASE_URL=postgresql+psycopg://vilacircula:vilacircula@localhost:5432/vilacircula
DATABASE_URL=postgresql+psycopg://vilacircula:vilacircula@localhost:5432/vilacircula
```

Entonces puedes generar y aplicar migraciones con:

```sh
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

> El backend actual sigue usando SQLite por compatibilidad y validación de tests, pero la configuración y la base de migración ya están listas para la transición a PostgreSQL.

## Cuentas de caja

En desarrollo se crean estas cuentas de ejemplo:

| Usuario | Comercio |
| --- | --- |
| `caja.cafe-marco` | Café Marco |
| `caja.am-bakery` | a.m bakery & coffee |
| `caja.papeleria-demo` | Papelería de ejemplo |
| `caja.moda-demo` | Moda Circular · ejemplo |

La contraseña inicial es `Viladecans`.

## Probar la API

```sh
python -m pytest tests/
```

## Despliegue con Docker

```sh
docker build -t vilacircula .
docker run --rm -p 8000:8000 --env-file .env vilacircula
```

O con Docker Compose:

```sh
docker compose up --build
```

## Proyecto

La app combina una web PWA con una API FastAPI. La parte ciudadana gestiona saldo, cuenta, cupones y recompensas; la parte comercio gestiona validación y cajeros.

## Siguientes mejoras recomendadas

1. PostgreSQL + Alembic
2. historial de validaciones por cajero
3. mejora UX de login/caja
4. separación demo vs producción
5. caché inteligente y PWA más robusta

# Vilacircula
a336e9ff0ce17392746a4d71676286bbe0b30ae0
