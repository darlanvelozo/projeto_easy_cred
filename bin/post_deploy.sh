#!/bin/bash
# Script executado apos deploy para popular banco de demonstracao
# Uso: railway run bash bin/post_deploy.sh

echo "=== Populando banco de demonstracao ==="
python manage.py popular_banco --limpar
python manage.py atualizar_parcelas
echo "=== Pronto! ==="
