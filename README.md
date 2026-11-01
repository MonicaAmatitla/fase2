# fase2
# Servicio web para inferencia de texto

Solución base para integrar una interfaz web con una API de inferencia y empaquetarlas en una sola imagen Docker. El directorio de trabajo original no incluía el modelo construido; por eso el contenedor usa un clasificador demostrativo hasta configurar `MODEL_PATH`. El modo demo valida la integración, no representa el desempeño de un modelo productivo.

## Inicio local

Requiere Docker Engine y Docker Compose v2.

```sh
docker compose up --build
```

Abre <http://localhost:8080>. Para detener: `docker compose down`.

## Conectar un modelo

El artefacto debe ser un pickle de confianza con un método `predict(list[str])`. Cópialo localmente como `model/model.pkl` y crea `.env`:

```dotenv
MODEL_DIR=./model
MODEL_PATH=/models/model.pkl
```

Luego reconstruye y arranca `docker compose up --build`. No se incluye el modelo ni debe subirse al repositorio si contiene datos, pesos restringidos o información sensible. La versión Python y dependencias del artefacto tienen que coincidir con la imagen; si el modelo requiere bibliotecas, agrégalas fijando versiones en el Dockerfile. Carga pickle solo desde orígenes confiables porque puede ejecutar código al deserializarse.

## API

- `GET /health` devuelve estado y si se está usando el modo demostrativo.
- `POST /api/predict` recibe `{"text":"..."}` y devuelve `{"prediction":"...","demo":true|false}`.
- El cuerpo se limita a 16 KiB y el texto a 4.000 caracteres.

## Desarrollo sin Docker

Python 3.12, sin dependencias externas:

```sh
cd app
python server.py
```

Pruebas: `python -m unittest discover -s tests -v` desde la raíz.

## Estructura

`app/static/` contiene la interfaz; `app/server.py` expone estáticos, salud y API; `app/model_adapter.py` carga el artefacto o activa el demo; `Dockerfile` y `compose.yaml` construyen y ejecutan el servicio.

Consulta `docs/despliegue-nube.docx` y `docs/validacion-pruebas.docx` para los procedimientos completos. La guía de nube describe Cloud Run y AWS App Runner. Antes de publicar, configura autenticación si el endpoint será privado, TLS y controles de acceso al artefacto.
