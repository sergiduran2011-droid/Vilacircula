# VilaCircula

PWA de demostración para Viladecans con API FastAPI y SQLite.

## Ejecutar

```sh
.venv/bin/python -m uvicorn app:app --reload --port 8001
```

Abre http://localhost:8001. La ciudadanía crea una cuenta con nombre, instituto, nombre de usuario y contraseña; no se pide email. El nombre de usuario es único y las contraseñas se almacenan con scrypt. El token de sesión se guarda en el navegador durante un máximo de 30 días; cerrar sesión lo revoca en el servidor.

Perfiles y cupones existentes se migran al iniciar. Si un perfil antiguo tenía un token válido, podrá usarlo para fijar su nombre de usuario y contraseña; después la sesión anterior se revoca.

Para instalar dependencias y ejecutar las pruebas:

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests/
```

## Cuentas De Caja

En desarrollo se crean estas cuentas de ejemplo:

| Usuario | Comercio |
| --- | --- |
| `caja.cafe-marco` | Café Marco |
| `caja.am-bakery` | a.m bakery & coffee |
| `caja.papeleria-demo` | Papelería de ejemplo |
| `caja.moda-demo` | Moda Circular · ejemplo |

La contraseña inicial es `Viladecans`. Cada cuenta debe cambiarla en su primer acceso antes de escanear; las contraseñas posteriores requieren confirmar la clave vigente. Cada sesión de caja está vinculada a un solo comercio y no puede canjear vales de otra tienda. Cerrar la sesión revoca el token.

En producción no se crean esas cuentas automáticamente. El administrador puede provisionarlas con `POST /api/v1/admin/cashiers`, enviando `X-Admin-Key`; el nombre de usuario y el `merchant_id` van en el JSON. Define `VILACIRCULA_ADMIN_KEY` en el entorno del servidor y entrega al cajero la contraseña temporal para rotación inmediata. Nunca pongas esa clave en la PWA.

```sh
VILACIRCULA_ENV=production VILACIRCULA_ADMIN_KEY='<secreto-largo>' \
	.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

El aprovisionamiento está disponible solo si se configura la clave municipal. El endpoint de demostración de puntos queda bloqueado en producción. La app conserva una única ruta de canje autorizada para caja; las respuestas privadas del API no pasan por la caché del service worker.

## Datos Y Límites

- Café Marco y a.m bakery & coffee tienen ubicaciones y enlaces a OpenStreetMap; Goar aparece como referencia en el mapa. Las fichas de papelería y moda están marcadas como ejemplos y no aparecen como marcadores reales.
- Los cupones quedan vinculados al `merchant_id`, expiran, se marcan en una transacción SQLite y guardan qué cajero los validó. Una repetición devuelve `409`; un intento en otra tienda, `403`.
- Hay ocho intentos de login por usuario/IP en una ventana de 15 minutos antes del bloqueo temporal.
- Pasos, EcoRutas, recompensas, saldo inicial y puntos de liga aún son de demostración. Los puntos del botón EcoID se escriben en SQLite en desarrollo, pero no son puntos municipales reales.
- El QR EcoID no implementa todavía TOTP firmado. Para una puesta en marcha municipal se necesita desplegar HTTPS, configurar secretos fuera del repositorio, activar respaldos y reemplazar el catálogo y premios ilustrativos por acuerdos confirmados.
