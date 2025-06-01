.PHONY: clean uninstall build install all env test

PACKAGE_NAME=koboapi

env:
	echo "🐍 Creando entorno virtual..."
	python -m venv venv
	echo "📦 Actualizando pip..."
	./venv/bin/pip install --upgrade pip
	echo "📋 Instalando requirements..."
	./venv/bin/pip install -r requirements.txt

clean:
	echo "🧹 Limpiando dist/, egg-info, __pycache__, pytest_cache..."
	rm -rf dist/ *.egg-info src/koboapi.egg-info .pytest_cache
	find . -type d -name "__pycache__" -exec rm -r {} + || true

uninstall:
	echo "❌ Desinstalando paquete si está instalado..."
	. ./venv/bin/activate
	pip uninstall -y $(PACKAGE_NAME) || true

build: clean
	echo "📦 Construyendo paquete..."
	. ./venv/bin/activate
	python -m build

install: uninstall build
	echo "📥 Instalando paquete desde dist/*.whl..."
	. ./venv/bin/activate
	pip install dist/*.whl

all: install
	echo "🏁 Proceso completo (build, install) terminado."

test:
	echo "🧪 Ejecutando smoke tests..."
	. ./venv/bin/activate
	python tests/url.py
