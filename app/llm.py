from openai import OpenAI

client = OpenAI()


def ask_llm(
    question: str,
    context: str,
    system_prompt: str,
    history_messages: list[dict[str, str]] | None = None,
) -> str:
    # The history comes before the new question so the model can use the previous turn(s) as context.
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

    if history_messages:
        messages.extend(history_messages)

    # The current question is always last, so the model answers based on the latest user input.
    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    answer = response.choices[0].message.content
    return answer or "Não foi possível gerar uma resposta."
