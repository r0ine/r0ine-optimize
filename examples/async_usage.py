"""
Async kullanim: async LLM cagrilari icin optimize_async dekoratoru.

Modern Python LLM SDK'leri (openai, anthropic, litellm) cogunlukla async
arayuz sunar. optimize_async bu akisi destekler.
"""

import asyncio

from r0ine_optimize import optimize_async


@optimize_async(profile="code")
async def call_llm_async(messages: list[dict]) -> str:
    # Gercek kullanim:
    # resp = await openai.AsyncClient().chat.completions.create(model="gpt-4o", messages=messages)
    # return resp.choices[0].message.content
    await asyncio.sleep(0.01)
    return f"Async yanit ({len(messages)} mesaj)"


async def main():
    history = [
        {"role": "system", "content": "Sen bir kod asistanisin."},
        *[{"role": "user", "content": f"```python\nprint({i})\n```"} for i in range(12)],
        {"role": "user", "content": "Bu kodu acikla"},
    ]

    result = await call_llm_async(messages=history)
    print(f"Yanit: {result}")

    report = call_llm_async.optimization_report.as_dict()
    print(f"Istatistik: {report}")


asyncio.run(main())
