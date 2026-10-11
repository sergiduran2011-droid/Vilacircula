# Despliegue de VilaCircula

La web de GitHub Pages es estática. Render ejecuta FastAPI y Supabase almacena los datos en PostgreSQL. El navegador solo llama a la API de Render; las claves de base de datos y administración no se publican.

## 1. Conectar Supabase

En el proyecto `https://ahkvjatqovigvphchtpw.supabase.co`, abre **Connect** y copia la cadena PostgreSQL del **Transaction pooler**. Usa la URI completa que muestra Supabase y conserva el usuario, contraseña, host y puerto del pooler. El backend añade `sslmode=require` automáticamente si falta.

## 2. Crear el servicio de Render

En Render, crea un **Blueprint** desde este repositorio y confirma el servicio `vilacircula-api-sergiduran2011-droid`. Render construye el contenedor con `render.yaml` y despliega FastAPI.

Cuando Render solicite valores secretos, introduce:

- `VILACIRCULA_DATABASE_URL`: la URI PostgreSQL del Transaction pooler de Supabase.
- `VILACIRCULA_INITIAL_CASHIER_PASSWORD`: una contraseña temporal fuerte para las cuentas de caja de ejemplo. Cámbiala después del primer acceso.

`VILACIRCULA_ADMIN_KEY` se genera automáticamente por Render. No copies ninguno de estos secretos a GitHub Pages ni a archivos versionados.

## 3. Activar Pages

`api-config.json` ya apunta a `https://vilacircula-api-sergiduran2011-droid.onrender.com`. En Render, comprueba que el servicio tenga ese dominio; si Render asigna otro, cambia `apiBaseUrl` a la URL que muestre el panel y publica el cambio en GitHub Pages.

La configuración CORS del Blueprint permite el origen `https://sergiduran2011-droid.github.io`, que es el origen del sitio aunque la página viva bajo `/Vilacircula/`.

## 4. Comprobar

Abre `https://vilacircula-api-sergiduran2011-droid.onrender.com/api/v1/health`. Debe responder con `status: ok` y `persistent_database: postgresql`. Luego prueba desde Pages el registro, el inicio de sesión, la creación de un cupón y el acceso de caja.

La base empieza sin perfiles ni cupones. Al iniciar FastAPI se crean las tablas y se cargan las fichas de comercios y las recompensas de ejemplo. Las cuentas de caja de muestra solo se crean si se configura la contraseña inicial.

## Alcance actual

Esta publicación hace persistentes las cuentas, sesiones, puntos, historial y cupones existentes de la app. La sincronización de pasos, los desafíos y las recompensas/comercios ilustrativos siguen siendo funciones de demostración; no se conectan automáticamente a sensores ni a comercios reales. En producción, la suma de puntos simulada está desactivada y el canje de cupones se realiza desde una caja autorizada.