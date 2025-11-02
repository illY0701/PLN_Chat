#!/bin/bash

# Instalar coverage se ainda não estiver instalado
pip install coverage

# Executar testes com cobertura
coverage run --source=app manage.py test

# Gerar relatório em HTML
coverage html

# Mostrar relatório no terminal
coverage report

echo "Relatório de cobertura gerado em htmlcov/index.html"