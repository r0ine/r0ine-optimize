"""
Pipeline kullanimi: optimizasyon adimlarini zincir halinde birlestir.

Pipeline, dedup -> system-merge -> prune -> truncate adimlarini istedigin
siraya dizmen icin composable bir arayuz sunar. Profile ile hazir zincirleme
de kullanabilirsin, adim adim kendini de kurabilirsin.
"""

from clorfy_optimize import Pipeline


# --- 1) Profile-tabanli pipeline (tek satirda) ---

pipe_chat = Pipeline("chat")
messages = [
    {"role": "system", "content": "Sen bir destek asistanisin."},
    {"role": "system", "content": "Kullanicilara kibarca yanit ver."},
    *[{"role": "user", "content": f"Mesaj {i}"} for i in range(20)],
    {"role": "user", "content": "Mesaj 3"},  # tekrar eden
    {"role": "user", "content": "Son sorum"},
]

result = pipe_chat.run(messages)
print(f"[Profil pipeline] {result.tokens_before} -> {result.tokens_after} token")
print(f"  Tasarruf: %{result.savings_percent:.1f}")
print(f"  Adimlar: {result.steps_applied}")


# --- 2) Manuel pipeline (tamamen kontrol sende) ---

pipe_custom = (
    Pipeline()
    .merge_system()
    .deduplicate(threshold=1.0)
    .truncate(max_tokens_per_message=200)
    .prune(keep_last=5, preserve_code=True, budget_tokens=4_000)
)

result2 = pipe_custom.run(messages)
print(f"\n[Manuel pipeline] {result2.tokens_before} -> {result2.tokens_after} token")
print(f"  Tasarruf: %{result2.savings_percent:.1f}")
print(f"  Adimlar: {result2.steps_applied}")
