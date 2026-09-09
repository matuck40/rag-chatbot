#!/bin/bash

# Run from the project root with the virtualenv in .venv
cd "$(dirname "$0")"

source .venv/bin/activate
uvicorn app.main:app --reload
