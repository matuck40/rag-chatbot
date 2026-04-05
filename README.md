# RAG Chatbot com Histórico de Conversas

API em FastAPI conectada a um modelo da OpenAI com armazenamento de histórico em PostgreSQL.

## ✨ Funcionalidades

- **RAG (Retrieval-Augmented Generation)**: Busca informações relevantes na base de conhecimento
- **Histórico de Conversas**: Armazena e recupera conversas completas usando PostgreSQL
- **Sessões de Chat**: Suporte a múltiplas sessões de conversa independentes
- **API REST**: Endpoints para perguntas, histórico e saúde do sistema

## 📋 Requisitos

- macOS, Linux ou Windows
- Python 3.11+
- PostgreSQL 12+
- VS Code opcional
- Chave da OpenAI

## 🚀 Instalação Rápida

### 1. Clonar/Configurar Ambiente

```bash
cd ~/projects/rag-chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar PostgreSQL

**macOS:**
```bash
brew install postgresql
brew services start postgresql
createdb rag_chatbot
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb rag_chatbot
```

### 3. Configurar Variáveis de Ambiente

Edite o arquivo `.env`:

```env
OPENAI_API_KEY=sk-sua-chave-aqui
DATABASE_URL=postgresql://localhost/rag_chatbot
```

### 4. Inicializar Banco de Dados

```bash
python init_db.py
```

### 5. Executar

```bash
./run.sh
```

Ou diretamente:
```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

## Requisitos

- macOS, Linux ou Windows
- Python 3.11+
- PostgreSQL database
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
DATABASE_URL=postgresql://user:password@localhost/rag_chatbot
```

## 📡 API Endpoints

### GET `/health`
Verifica se o servidor está funcionando.

**Resposta:**
```json
{"status": "ok"}
```

### POST `/ask`
Envia uma pergunta e recebe resposta com contexto.

**Request Body:**
```json
{
  "question": "Qual é a capital do Brasil?",
  "session_id": "abc-123-def",
  "history": [
    {"role": "user", "content": "Olá"},
    {"role": "assistant", "content": "Olá! Como posso ajudar?"}
  ]
}
```

**Resposta:**
```json
{
  "answer": "A capital do Brasil é Brasília.",
  "sources": ["fonte1", "fonte2"],
  "session_id": "abc-123-def"
}
```

### GET `/conversations/{session_id}`
Recupera histórico completo de uma conversa.

**Resposta:**
```json
{
  "session_id": "abc-123-def",
  "messages": [
    {"role": "user", "content": "Olá"},
    {"role": "assistant", "content": "Olá! Como posso ajudar?"},
    {"role": "user", "content": "Qual é a capital do Brasil?"},
    {"role": "assistant", "content": "A capital do Brasil é Brasília."}
  ]
}
```


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
    history: Optional[List[Message]] = None
    session_id: Optional[str] = None


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


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

## 🧪 Como Testar

Com o servidor rodando, acesse a documentação interativa:

```text
http://127.0.0.1:8000/docs
```

### Teste Básico

1. **Health Check:**
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. **Fazer uma pergunta:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/ask" \
        -H "Content-Type: application/json" \
        -d '{"question": "Olá, como você funciona?"}'
   ```

3. **Ver histórico:**
   ```bash
   curl "http://127.0.0.1:8000/conversations/$(uuidgen)"
   ```

## 🔧 Troubleshooting

### Erro de conexão com PostgreSQL
- Verifique se PostgreSQL está rodando: `brew services list` (macOS) ou `sudo systemctl status postgresql` (Linux)
- Confirme que o banco `rag_chatbot` existe: `psql -l`
- Verifique a variável `DATABASE_URL` no `.env`

### Erro de chave OpenAI
- Confirme que `OPENAI_API_KEY` está definida no `.env`
- Verifique se a chave é válida no [dashboard da OpenAI](https://platform.openai.com/api-keys)

### ImportError ou ModuleNotFoundError
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 📁 Estrutura do Projeto

```
rag-chatbot/
├── app/
│   ├── main.py              # API FastAPI
│   ├── models.py            # Modelos Pydantic e SQLAlchemy
│   ├── services/
│   │   ├── database_service.py  # Serviço de banco de dados
│   │   └── rag_service.py   # Serviço RAG
│   ├── embedding.py         # Geração de embeddings
│   ├── knowledge.py         # Processamento da base de conhecimento
│   └── llm.py              # Integração com OpenAI
├── data/
│   ├── knowledge_base.txt  # Base de conhecimento
│   └── chunk_embeddings.json  # Embeddings em cache
├── alembic/                # Migrações do banco
├── prompts/
│   └── system_prompt.txt   # Prompt do sistema
├── .env                    # Variáveis de ambiente
├── requirements.txt        # Dependências Python
├── init_db.py             # Script de inicialização do banco
└── run.sh                 # Script de execução
```

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
