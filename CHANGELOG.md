# Changelog

## 0.1.0 (2026-07-27)

Ilk surum.

### Ozellikler
- `@optimize` dekoratoru ile tek satirda LLM cagri optimizasyonu
- `@optimize_async` ile async LLM cagrisi destegi
- `Pipeline` ile composable optimizasyon zincirleri
- Uc hazir profil: `code`, `chat`, `plan`
- Strateji modulleri: `deduplicate`, `truncate_messages`, `merge_system_messages`
- SQLite tabanli yanit onbellegi (TTL destekli)
- Token sayimi (tiktoken veya fallback)
- Mesaj gecmisi budama (budget + keep_last + preserve_code)
- CLI: `analyze`, `profiles`, `cache stats/clear/purge`
- PEP 561 typed paketi
- GitHub Actions CI (Python 3.10-3.13)
