from openai import OpenAI
from typing import List, Dict

client = OpenAI()


def ask_llm(question: str, context: str, system_prompt: str, history: List[Dict[str, str]] = None) -> str:
    if history is None:
        history = []
    
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "system",
            "content": f"Contexto:\n{context}",
        },
    ]
    
    # Add history messages
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current question
    messages.append({
        "role": "user",
        "content": question,
    })
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    answer = response.choices[0].message.content
    return answer or "Não foi possível gerar uma resposta."