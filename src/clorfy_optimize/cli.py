from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .cache import ResponseCache
from .counter import TokenCounter
from .pipeline import Pipeline
from .profiles import get_profile
from .pruner import prune_messages

console = Console()


@click.group()
def app() -> None:
    """clorfy-optimize: LLM token kullanimi azaltan kutuphane ve CLI."""


@app.command()
@click.argument("messages_file", type=click.Path(exists=True, path_type=Path))
@click.option("--profile", default="chat", show_default=True, help="code | chat | plan")
@click.option("--model", default="gpt-4o", show_default=True)
@click.option("--pipeline", "use_pipeline", is_flag=True, help="Pipeline modunda calistir (dedup + merge + prune)")
def analyze(messages_file: Path, profile: str, model: str, use_pipeline: bool) -> None:
    """MESSAGES_FILE (OpenAI-stili JSON mesaj listesi) icin tasarruf tahmini uretir."""
    messages = json.loads(messages_file.read_text(encoding="utf-8"))
    counter = TokenCounter(model)
    before = counter.count_messages(messages)

    if use_pipeline:
        pipe = Pipeline(profile, model=model)
        result = pipe.run(messages)
        pruned = result.messages
        after = result.tokens_after
        steps = result.steps_applied
    else:
        profile_config = get_profile(profile)
        pruned = prune_messages(
            messages,
            budget_tokens=profile_config.default_budget_tokens,
            model=model,
            keep_last=profile_config.keep_last,
            preserve_code=profile_config.preserve_code,
        )
        after = counter.count_messages(pruned)
        steps = ["prune"]

    saved = before - after
    percent = (saved / before * 100) if before else 0.0

    table = Table(title=f"clorfy-optimize · profil={profile}")
    table.add_column("Metrik")
    table.add_column("Deger", justify="right")
    table.add_row("Mesaj sayisi (once)", str(len(messages)))
    table.add_row("Mesaj sayisi (sonra)", str(len(pruned)))
    table.add_row("Token (once)", str(before))
    table.add_row("Token (sonra)", str(after))
    table.add_row("Tasarruf", f"{saved} token (%{percent:.1f})")
    if use_pipeline:
        table.add_row("Uygulanan adimlar", ", ".join(steps) if steps else "yok")
    console.print(table)


@app.command()
def profiles() -> None:
    """Kullanilabilir profilleri ve varsayilan ayarlarini listeler."""
    from .profiles import CHAT, CODE, PLAN

    table = Table(title="clorfy-optimize profilleri")
    table.add_column("Profil")
    table.add_column("keep_last", justify="right")
    table.add_column("preserve_code")
    table.add_column("cache_ttl (sn)", justify="right")
    table.add_column("butce (token)", justify="right")
    for p in (CODE, CHAT, PLAN):
        table.add_row(
            p.name, str(p.keep_last), str(p.preserve_code),
            str(p.cache_ttl_seconds), str(p.default_budget_tokens),
        )
    console.print(table)


@app.group()
def cache() -> None:
    """Cache yonetim komutlari."""


@cache.command(name="stats")
def cache_stats() -> None:
    """Cache boyutu ve giris sayisini gosterir."""
    rc = ResponseCache()
    info = rc.size()
    rc.close()

    table = Table(title="clorfy-optimize cache")
    table.add_column("Metrik")
    table.add_column("Deger", justify="right")
    table.add_row("Giris sayisi", str(info["entries"]))
    table.add_row("Yanit boyutu", _format_bytes(info["response_bytes"]))
    table.add_row("DB boyutu", _format_bytes(info["db_bytes"]))
    console.print(table)


@cache.command(name="clear")
@click.confirmation_option(prompt="Tum cache silinsin mi?")
def cache_clear() -> None:
    """Tum cache girislerini temizler."""
    rc = ResponseCache()
    count = rc.clear()
    rc.close()
    console.print(f"[green]{count}[/green] giris silindi.")


@cache.command(name="purge")
def cache_purge() -> None:
    """Suresi dolmus cache girislerini temizler."""
    rc = ResponseCache()
    count = rc.purge_expired()
    rc.close()
    console.print(f"[green]{count}[/green] suresi dolmus giris temizlendi.")


def _format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


if __name__ == "__main__":
    app()
