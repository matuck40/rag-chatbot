# rag-chatbot

API simples em FastAPI conectada a um modelo da OpenAI.

## O que faz

A aplicação expõe endpoints HTTP para:

- verificar se o servidor está no ar
- enviar uma pergunta
- receber uma resposta gerada por IA

## Requisitos

- macOS, Linux ou Windows
- Python 3.11+
- VS Code opcional
- uma chave da OpenAI

## Estrutura esperada

```text
rag-chatbot/
  app/
    main.py
  .venv/
  .env
  .gitignore
  requirements.txt
  run.sh
```

## Instalação

### 1. Entrar na pasta do projeto

```bash
cd ~/projects/rag-chatbot
```

### 2. Criar o ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

## Configurar a chave da OpenAI

Crie um arquivo chamado `.env` na raiz do projeto com este formato:

```env
OPENAI_API_KEY=sk-sua-chave-aqui
```

## Configurar PostgreSQL

Adicione também a URL do banco no `.env`:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/rag_chatbot
```

O app cria a tabela `chat_interactions` automaticamente ao iniciar.
Quando o PostgreSQL estiver fora do ar, o endpoint `/ask` ainda funciona, mas o campo `historic`
volta vazio e o modelo não recebe histórico anterior.


## Exemplo de `run.sh`

Crie um arquivo `run.sh` na raiz:

```bash
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
uvicorn app.main:app --reload
```

Deixe executável:

```bash
chmod +x run.sh
```

## Exemplo de `app/main.py`

```python
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
client = OpenAI()


class QuestionRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(req: QuestionRequest):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": req.question}
        ]
    )

    answer = response.choices[0].message.content
    return {"answer": answer}
```

## Rodar o servidor

Na raiz do projeto:

```bash
./run.sh
```

Ou, sem script:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

## Como testar

Com o servidor rodando, abra no navegador:

```text
http://127.0.0.1:8000/docs
```

### Endpoint de saúde

Abra:

```text
http://127.0.0.1:8000/health
```

Resposta esperada:

```json
{"status":"ok"}
```

### Endpoint de pergunta

Na página `/docs`:

1. Abra `POST /ask`
2. Clique em `Try it out`
3. Envie um JSON como este:

```json
{
  "question": "Explique o que é uma API de forma simples"
}
```

Resposta esperada:

```json
{
  "answer": "..."
}
```

## Teste da chave

Para verificar se o `.env` está sendo lido:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"
```

Se aparecer `None`, o `.env` está incorreto ou não está sendo encontrado.

## Problemas comuns

### `python-dotenv could not parse statement`

O arquivo `.env` está mal formatado.

Formato certo:

```env
OPENAI_API_KEY=sk-sua-chave-aqui
```

### `No module named 'app'`

Você provavelmente rodou o servidor de dentro da pasta `app`.

Rode sempre na raiz do projeto:

```bash
cd ~/projects/rag-chatbot
./run.sh
```

### `No API key provided`

A chave não foi carregada. Verifique:

- se o `.env` existe
- se `load_dotenv()` está no código
- se a variável está escrita como `OPENAI_API_KEY`

### `invalid_api_key`

A chave foi lida, mas está errada, incompleta ou expirada.

## Segurança

Não suba sua chave para o GitHub.

Use um `.gitignore` assim:

```gitignore
.venv
.env
__pycache__/
```

## Próximos passos

Sugestões de evolução:

- adicionar prompt `system`
- salvar histórico de perguntas e respostas
- criar uma base simples para RAG
- dockerizar a aplicação
- fazer deploy
