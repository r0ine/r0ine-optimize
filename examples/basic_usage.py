"""
Temel kullanim: @optimize dekoratoru ile tek satirda entegrasyon.

LLM cagri fonksiyonunun ustune eklenen dekorator, mesaj gecmisini profile gore
budar ve tekrar edenleri onbellekten doner.
"""

from clorfy_optimize import optimize


@optimize(profile="chat")
def call_llm(messages: list[dict]) -> str:
    # Burada kendi LLM client'ini cagirirsin:
    # return openai.chat.completions.create(model="gpt-4o", messages=messages).choices[0].message.content
    return f"Yanit ({len(messages)} mesaj islendi)"


conversation = [
    {"role": "system", "content": "Sen yardimci bir asistansin."},
    *[{"role": "user", "content": f"Soru {i}: Python hakkinda bilgi ver"} for i in range(15)],
    {"role": "user", "content": "Son sorum: decoratorler nasil calisir?"},
]

result = call_llm(messages=conversation)
print(f"Yanit: {result}")

report = call_llm.optimization_report.as_dict()
print(f"Istatistik: {report}")
print(f"Tasarruf: {report['tokens_saved']} token (%{report['tokens_saved']/max(1,report['tokens_before'])*100:.1f})")
