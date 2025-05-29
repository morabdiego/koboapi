# KoboAPI

[![PyPI version](https://img.shields.io/pypi/v/koboapi.svg?logo=pypi&logoColor=white)](https://badge.fury.io/py/koboapi)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)
[![requests](https://img.shields.io/badge/requests-dependency-blue.svg?logo=python&logoColor=white)](https://docs.python-requests.org/)
[![KoBo Toolbox](https://img.shields.io/badge/KoBo-Toolbox-orange.svg?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSIjZmY2OTAwIiBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnptMCAxOGMtNC40MiAwLTgtMy41OC04LThzMy41OC04IDgtOCA4IDMuNTggOCA4LTMuNTggOC04IDh6bTMtMTNIOXYyaDZ2LTJ6bTAgNEg5djJoNnYtMnptLTIgNEg5djJoNHYtMnoiLz48L3N2Zz4=)](https://www.kobotoolbox.org/)
[![GitHub](https://img.shields.io/badge/GitHub-morabdiego-black.svg?logo=github&logoColor=white)](https://github.com/morabdiego/koboapi)

Un paquete de Python para interactuar con la API de KoBo Toolbox. Esta librería proporciona una interfaz simple e intuitiva para acceder a encuestas, respuestas y metadatos de KoBo Toolbox.

## Agradecimientos

Este proyecto está basado en el excelente trabajo de [koboextractor](https://github.com/heiko-r/koboextractor) por Heiko Rohde. Esta modificación resuelve un problema en `get_data` y agrega funcionalidades de uso común para proyectos de análisis de datos y encuestas del Observatorio Villero de La Poderosa.

**Autor de las modificaciones**: Diego Mora [@morabdiego](https://github.com/morabdiego)

## Características

- 🔐 **Autenticación**: Autenticación segura basada en tokens
- 📊 **Gestión de Encuestas**: Listar, recuperar y gestionar assets de encuestas
- 📋 **Extracción de Datos**: Extraer respuestas de encuestas con opciones de filtrado
- 🔄 **Múltiples Endpoints**: Soporte para instancias por defecto y de respuesta humanitaria

## Instalación

### Desde PyPI
```bash
pip install koboapi
```

## Inicio Rápido

```python
import os
from dotenv import load_dotenv
from koboapi import Kobo

# Cargar variables de entorno
load_dotenv()
API_TOKEN = os.getenv("YOUR_API_TOKEN")

# Inicializar cliente
client = Kobo(token=API_TOKEN)

# Listar todas las encuestas
surveys = client.list_uid()
print(surveys)

# Obtener datos de encuesta específica
survey_uid = surveys['MI_ENCUESTA']
asset = client.get_asset(survey_uid)
questions = client.get_questions(asset)
choices = client.get_choices(asset)
```

## Configuración

### Variables de Entorno

Crea un archivo `.env` en la raíz de tu proyecto:

```bash
KOBO_KEY=tu_token_api_kobo_aqui
```

### Endpoints

La librería soporta múltiples instancias de KoBo Toolbox:

```python
# Endpoint por defecto (kf.kobotoolbox.org)
client = Kobo(token=API_TOKEN)

# Endpoint de Respuesta Humanitaria
client = Kobo(token=API_TOKEN, endpoint='humanitarian')

# Endpoint personalizado
client = Kobo(token=API_TOKEN, endpoint='https://tu-instancia-kobo-personalizada.org/')

# Habilitar modo debug
client = Kobo(token=API_TOKEN, debug=True)
```

## Referencia de API

### Métodos Principales

#### `Kobo(token, endpoint='default', debug=False)`

Inicializa el cliente de KoBo.

**Parámetros:**
- `token` (str): Tu token de autenticación de la API de KoBo
- `endpoint` (str): Tipo de endpoint ('default', 'humanitarian', o URL personalizada)
- `debug` (bool): Habilitar salida de debug

#### `list_assets()`

Devuelve una lista de todos los assets de encuestas como diccionarios.

```python
assets = client.list_assets()
for asset in assets:
    print(f"Nombre: {asset['name']}, UID: {asset['uid']}")
```

#### `list_uid()`

Devuelve un diccionario que mapea nombres de encuestas a sus UIDs.

```python
surveys = client.list_uid()
# Salida: {'Nombre de Encuesta': 'survey_uid_123', ...}
```

#### `get_asset(asset_uid)`

Obtiene información detallada sobre un asset de encuesta específico.

```python
asset = client.get_asset('survey_uid_123')
print(asset['name'])
print(asset['deployment__submission_count'])
```

#### `get_data(asset_uid, query=None, start=None, limit=None, submitted_after=None)`

Extrae respuestas de encuestas con filtrado opcional.

**Parámetros:**
- `asset_uid` (str): Identificador de la encuesta
- `query` (str): Cadena de consulta estilo MongoDB
- `start` (int): Índice inicial para paginación
- `limit` (int): Número máximo de respuestas a devolver
- `submitted_after` (str): Cadena de fecha ISO para filtrar envíos recientes

```python
# Obtener todas las respuestas
data = client.get_data('survey_uid_123')
```

#### `get_questions(asset, unpack_multiples=False)`

Extrae metadatos de preguntas de un asset de encuesta.

```python
asset = client.get_asset('survey_uid_123')
questions = client.get_questions(asset)

# Desempaquetar preguntas de opción múltiple
questions_detailed = client.get_questions(asset, unpack_multiples=True)
```

#### `get_choices(asset)`

Extrae listas de opciones de un asset de encuesta.

```python
asset = client.get_asset('survey_uid_123')
choices = client.get_choices(asset)

# Acceder a lista de opciones específica
age_groups = choices['lista_grupos_edad']
for choice_name, choice_data in age_groups.items():
    print(f"{choice_name}: {choice_data['label']}")
```

### Métodos de Utilidad

#### `sort_results_by_time(responses, reverse=False)`

Ordena respuestas por tiempo de envío.

```python
data = client.get_data('survey_uid_123')
sorted_responses = client.sort_results_by_time(data['results'])
```

#### `label_result(response, choice_lists, questions, unpack_multiples)`

Etiqueta una respuesta individual con metadatos de preguntas.

```python
asset = client.get_asset('survey_uid_123')
questions = client.get_questions(asset)
choices = client.get_choices(asset)

# Etiquetar respuesta individual
labeled = client.label_result(
    response,
    choices,
    questions,
    unpack_multiples=False
)
```

## Desarrollo

### Configurar Entorno de Desarrollo

```bash
git clone https://github.com/morabdiego/koboapi.git
cd koboapi
make env
make install
```

### Construir Paquete

```bash
make build
```

## Contribuir

1. Haz fork del repositorio
2. Crea una rama de característica
3. Realiza tus cambios
4. Agrega pruebas si es aplicable
5. Envía un pull request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## Enlaces

- **Página principal**: https://github.com/morabdiego/koboapi
- **Reportar errores**: https://github.com/morabdiego/koboapi/issues

## Historial de Cambios

### v0.1.0
- Lanzamiento inicial
- Funcionalidad básica de la API de KoBo
- Soporte para gestión de assets y extracción de datos
- Manejo integral de errores
- Type hints y documentación

## Roadmap

* Exportar encuesta en formato xlsform
* FlattenDict: Procesar datos de los json para convertirlos en dataframes manejables, además de realizar un flatten de json con varios niveles anidados en surveys avanzados con groups o repeats
