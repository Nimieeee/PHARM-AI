from IPython.display import Markdown, display, update_display
from openai_client import openai
from prompts import system_prompt

def stream_brochure(model: str, question: str):
    """Stream response tokens in real time."""
    stream = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        stream=True,
    )

    response = ""
    display_handle = display(Markdown(""), display_id=True)

    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
        response = response.replace("```", "").replace("markdown", "")
        update_display(Markdown(response), display_id=display_handle.display_id)

    return response
