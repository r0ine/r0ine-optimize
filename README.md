# clorfy-optimize

[![CI](https://github.com/clorfy/clorfy-optimize/actions/workflows/ci.yml/badge.svg)](https://github.com/clorfy/clorfy-optimize/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

LLM'lere gonderdigin token miktarini azaltan kutuphane + CLI. `clorfy-prompt`'un
kardesi — clorfy ailesinin token tasarrufu tarafi.

## Ne yapiyor?

Uc temel mekanizma:

- **Onbellekleme** — ayni mesaj listesi + ayni model tekrar geldiginde modele hic gitmeden diskten
  cevap doner (SQLite tabanli, TTL'li).
- **Gecmis budama** — sohbet gecmisini bir token butcesine sigdirir: sistem mesajini ve son N turu
  korur, gerekirse eskiden yeniye dogru kirpar.
- **Profil motoru** — kod asistani, sohbet ve planlama senaryolarinin token profili farkli;
  `code` / `chat` / `plan` profilleri bunun icin hazir varsayilanlar tasiyor.

Bunlarin ustune uc ek yetenek:

- **Pipeline** — optimizasyon adimlarini zincir halinde birlestiren composable arayuz
  (dedup → system-merge → prune → truncate).
- **Strateji modulleri** — mesaj tekillesitirme (dedup), uzun mesaj kirpma (truncate), coklu system
  mesajlarini birlestirme (merge).
- **Async destek** — `optimize_async` dekoratoru ile async LLM cagrilerina tam uyum.


## Kurulum

```bash
pip install clorfy-optimize
```

Gercek tokenizer icin (`tiktoken` kurulu degilse karakter/4 yaklasik sayima dusulur):

```bash
pip install "clorfy-optimize[tiktoken]"
```


## Tek satir entegrasyon

Var olan bir LLM cagri fonksiyonunun ustune dekorator ekliyorsun, gerisini o hallediyor:

```python
from clorfy_optimize import optimize

@optimize(profile="chat")
def call_llm(messages: list[dict]) -> str:
    return my_llm_client.chat(messages)
```

`messages` argumani cagrilmadan once profile gore budanir, ayni istek daha once yapildiysa
onbellekten donulur — fonksiyonun icine hic dokunmadin.

Async versiyonu:

```python
from clorfy_optimize import optimize_async

@optimize_async(profile="code")
async def call_llm(messages: list[dict]) -> str:
    return await my_async_client.chat(messages)
```

Tasarrufu gormek icin:

```python
call_llm(messages=history)
print(call_llm.optimization_report.as_dict())
# {'calls': 1, 'cache_hits': 0, 'tokens_before': 812, 'tokens_after': 340, 'tokens_saved': 472}
```


## Pipeline (composable optimizasyon)

Profil tabanli hazir zincir:

```python
from clorfy_optimize import Pipeline

pipe = Pipeline("chat")  # merge_system -> deduplicate -> prune
result = pipe.run(messages)

print(result.tokens_before, "->", result.tokens_after)
print(f"Tasarruf: %{result.savings_percent:.1f}")
print(f"Adimlar: {result.steps_applied}")
```

Tamamen ozel zincir:

```python
pipe = (
    Pipeline()
    .merge_system()              # coklu system mesajlarini birlestir
    .deduplicate(threshold=1.0)  # tekrar eden mesajlari at
    .truncate(max_tokens_per_message=500)  # uzun mesajlari kirp
    .prune(keep_last=5, preserve_code=True, budget_tokens=4_000)
)
result = pipe.run(messages)
```

Kendi optimizasyon adimini ekle:

```python
pipe = Pipeline().add_step("redact", lambda msgs: [
    {**m, "content": m["content"].replace("API_KEY", "***")} for m in msgs
]).prune(keep_last=8, budget_tokens=6_000)
```


## Stratejiler

Bagimsiz olarak da kullanilabilir:

```python
from clorfy_optimize import deduplicate, merge_system_messages, truncate_messages

# Tekrar eden mesajlari cikar
clean = deduplicate(messages, threshold=1.0)

# Coklu system mesajlarini tek bir mesaja birlestir
merged = merge_system_messages(messages)

# Uzun mesajlari kirp
truncated = truncate_messages(messages, max_tokens_per_message=300)
```


## Profiller

| Profil | keep_last | preserve_code | cache_ttl | varsayilan butce |
|---|---|---|---|---|
| `code` | 6 | evet | 6 saat | 12.000 token |
| `chat` | 8 | hayir | 15 dakika | 6.000 token |
| `plan` | 3 | evet | 24 saat | 20.000 token |

`code` profili kod bloklarini budamadan korur, `chat` sohbeti agresifce kisaltir,
`plan` uzun planlama dokumanlarini uzun TTL ile onbellekte tutar.

Kendi profilini de kurabilirsin:

```python
from clorfy_optimize import Profile

my_profile = Profile(
    name="custom",
    keep_last=10,
    preserve_code=True,
    cache_ttl_seconds=3600,
    default_budget_tokens=8_000,
)
pipe = Pipeline(my_profile)
```


## CLI

Konusma gecmisini analiz et:

```bash
clorfy-optimize analyze conversation.json --profile chat
```

Pipeline moduyla analiz:

```bash
clorfy-optimize analyze conversation.json --profile code --pipeline
```

Profilleri listele:

```bash
clorfy-optimize profiles
```

Cache yonetimi:

```bash
clorfy-optimize cache stats    # boyut ve giris sayisi
clorfy-optimize cache purge    # suresi dolmuslari temizle
clorfy-optimize cache clear    # tum cache'i sil
```


## Mimari

```
clorfy-optimize/
├── src/clorfy_optimize/
│   ├── __init__.py          # public API
│   ├── counter.py           # TokenCounter (tiktoken veya fallback)
│   ├── cache.py             # ResponseCache (SQLite, TTL, stats)
│   ├── pruner.py            # mesaj budama (budget + keep_last)
│   ├── profiles.py          # CODE / CHAT / PLAN profilleri
│   ├── strategies.py        # dedup, truncate, merge_system
│   ├── pipeline.py          # Pipeline (composable zincir)
│   ├── decorator.py         # @optimize (sync)
│   ├── async_support.py     # @optimize_async
│   └── cli.py               # Click CLI
├── tests/                   # 30+ test
├── examples/                # kullanim ornekleri
└── .github/workflows/       # CI (Python 3.10-3.13, lint, typecheck)
```


## Sinirlar (v0.1)

- `optimize()` dekoratoru, sarmaladigi fonksiyonun duz metin (`str`) dondurdugunu varsayar —
  streaming veya yapilandirilmis (tool-call) yanitlar icin onbellekleme devre disi birakilmali.
- Budama deterministik bir kural motoru; gercek bir ozetleme LLM'i cagirmiyor (bu bilincli bir
  tercih — token tasarrufu yapan bir arac kendisi token harcayip modele bagimli olmamali).
- `tiktoken` kurulu degilse token sayimi yaklasik (karakter/4).


## Gelistirme

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src/clorfy_optimize --ignore-missing-imports
```


## clorfy ailesi

| Proje | Amac |
|---|---|
| **clorfy-prompt** | Prompt muhendisligi ve optimizasyonu |
| **clorfy-optimize** | Token tasarrufu (budama, onbellek, pipeline) |
| *clorfy-memory* | Uzun sureli LLM hafiza yonetimi (planlaniyor) |
| *clorfy-router* | Coklu model yonlendirme (planlaniyor) |
| *clorfy-guard* | LLM cikti guvenlik filtreleri (planlaniyor) |


## Lisans

MIT
