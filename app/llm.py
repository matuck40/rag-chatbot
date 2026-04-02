from openai import OpenAI

client = OpenAI()


def ask_llm(question: str, context: str, system_prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "system",
                "content": f"Contexto:\n{context}",
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    answer = response.choices[0].message.content
    return answer or "Não foi possível gerar uma resposta."