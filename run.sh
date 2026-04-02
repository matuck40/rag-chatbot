#!/bin/bash

# garante que está na raiz do projeto
cd "$(dirname "$0")"

source .venv/bin/activate
uvicorn app.main:app --reload