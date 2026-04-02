from openai import OpenAI

client = OpenAI()


def ask_llm(question: str, context: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um assistente que responde apenas com base no contexto fornecido. "
                    "Se a resposta não estiver no contexto, diga claramente que não encontrou essa informação."
                ),
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