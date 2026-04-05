#!/bin/bash

# garante que está na raiz do projeto
cd "$(dirname "$0")"

# Este projeto usa o PostgreSQL do Homebrew, então subimos o serviço antes do Uvicorn.
# Se o serviço já estiver rodando, o comando do Homebrew apenas mantém o processo ativo.
PG_SERVICE="postgresql@18"
PG_STARTED_BY_SCRIPT=0

stop_postgres() {
  if [ "${PG_STARTED_BY_SCRIPT}" -eq 1 ] && command -v brew >/dev/null 2>&1; then
    # Só paramos o serviço se este script o iniciou, para não interromper um banco já em uso.
    brew services stop "${PG_SERVICE}" >/dev/null 2>&1 || true
  fi
}

trap stop_postgres EXIT

if command -v brew >/dev/null 2>&1; then
  if ! brew services list | grep -q "^${PG_SERVICE} .* started"; then
    brew services start "${PG_SERVICE}"
    PG_STARTED_BY_SCRIPT=1
  fi
else
  echo "brew não encontrado. Inicie o PostgreSQL manualmente antes de rodar a API."
fi

source .venv/bin/activate
uvicorn app.main:app --reload
