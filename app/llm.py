from functools import lru_cache

from openai import OpenAI

CHAT_MODEL = "gpt-4o-mini"


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    # Created on first use, so importing the app does not require an API key.
    return OpenAI()


def ask_llm(
    question: str,
    context: str,
    system_prompt: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Contexto:\n{context}"},
    ]
    for msg in history or []:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    response = get_client().chat.completions.create(model=CHAT_MODEL, messages=messages)

    answer = response.choices[0].message.content
    return answer or "Não foi possível gerar uma resposta."
