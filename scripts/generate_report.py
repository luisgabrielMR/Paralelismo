import csv
import json
import sys
from pathlib import Path


REPORT_FILE = "relatorio.html"
DATA_DIR = "data"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/generate_report.py results/PASTA_DA_EXECUCAO")

    report_path = generate_report(Path(sys.argv[1]))
    print(f"Relatorio gerado em: {report_path}")


def generate_report(run_dir):
    run_dir = Path(run_dir).resolve()
    data_dir = run_dir / DATA_DIR

    if not data_dir.exists() or not data_dir.is_dir():
        raise FileNotFoundError(f"Pasta de dados nao encontrada: {data_dir}")

    raw_json = read_json(data_dir / "resultados_brutos.json")
    summary = read_json(data_dir / "resumo_benchmark.json")
    raw_rows = read_csv(data_dir / "resultados_brutos.csv")
    general_rows = read_csv(data_dir / "medias_gerais.csv")
    speedup_rows = read_csv(data_dir / "speedup.csv")
    by_name_rows = read_csv(data_dir / "medias_por_nome.csv")

    metadata = raw_json.get("metadata", {})
    sampled_names = metadata.get("sampledNames", [])
    environment = extract_environment(raw_rows)
    conclusion = build_conclusion(general_rows, speedup_rows)

    html = build_html(
        summary=summary,
        metadata=metadata,
        sampled_names=sampled_names,
        environment=environment,
        general_rows=general_rows,
        speedup_rows=speedup_rows,
        by_name_rows=by_name_rows,
        conclusion=conclusion,
    )

    report_path = run_dir / REPORT_FILE
    with report_path.open("w", encoding="utf-8", newline="") as file:
        file.write(html)

    return report_path


def read_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def build_html(summary, metadata, sampled_names, environment, general_rows, speedup_rows, by_name_rows, conclusion):
    best_strategy = summary.get("melhorEstrategiaPorTempoMedio") or {}
    best_speedup = summary.get("maiorSpeedup") or {}
    cpu_rows = rows_with_number(general_rows, "media_cpu_usage_approx_percent")
    show_cpu_warning = not cpu_rows or all(as_float(row.get("media_cpu_usage_approx_percent")) == 0 for row in cpu_rows)

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Relatorio de Benchmark - Busca de Nomes</title>
  <style>
    :root {{
      --bg: #f5f7fb;
      --panel: #ffffff;
      --text: #1d2733;
      --muted: #667085;
      --line: #d9e0ea;
      --accent: #1264a3;
      --accent-2: #16845f;
      --warn: #9a6700;
      --shadow: 0 10px 30px rgba(31, 42, 55, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.5 Arial, Helvetica, sans-serif;
    }}
    main {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 56px;
    }}
    header {{
      margin-bottom: 24px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 30px;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 20px;
    }}
    .subtitle {{ color: var(--muted); margin: 0; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
    }}
    .card, section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}
    .card {{ padding: 16px; }}
    .card .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .04em;
      margin-bottom: 6px;
    }}
    .card .value {{
      font-size: 18px;
      font-weight: 700;
      word-break: break-word;
    }}
    section {{
      padding: 20px;
      margin: 18px 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #eef3f8;
      font-weight: 700;
      color: #263442;
    }}
    tr.highlight-best td {{ background: #edf8f2; }}
    .table-wrap {{ overflow-x: auto; }}
    .chart {{
      width: 100%;
      min-height: 280px;
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfdff;
      padding: 10px;
    }}
    .note {{
      color: var(--warn);
      background: #fff7dd;
      border: 1px solid #f0d98c;
      padding: 10px 12px;
      border-radius: 8px;
      margin: 10px 0 0;
    }}
    .conclusion {{
      font-size: 16px;
      background: #f8fbff;
      border-left: 4px solid var(--accent);
      padding: 14px 16px;
      border-radius: 6px;
    }}
    .pill {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      background: #e8f2fb;
      color: #0f5487;
      font-weight: 700;
      white-space: nowrap;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Relatório de Benchmark - Busca de Nomes</h1>
    <p class="subtitle">Comparação de estratégias sequenciais e paralelas usando os tempos medidos pelo Java.</p>
  </header>

  <div class="grid">
    {summary_cards(summary, metadata, best_strategy, best_speedup)}
  </div>

  <section>
    <h2>Ambiente</h2>
    {environment_table(environment)}
  </section>

  <section>
    <h2>Nomes Sorteados</h2>
    {sampled_names_table(sampled_names)}
  </section>

  <section>
    <h2>Médias Gerais</h2>
    {general_table(general_rows)}
  </section>

  <section>
    <h2>Speedup</h2>
    {speedup_table(speedup_rows)}
  </section>

  <section>
    <h2>Tempo Médio por Estratégia</h2>
    <div class="chart">{bar_chart(general_rows, "media_wall_time_ms", "Média wallTimeMs", "#1264a3")}</div>
  </section>

  <section>
    <h2>Speedup por Estratégia</h2>
    <div class="chart">{bar_chart(speedup_rows, "speedup", "Speedup", "#16845f")}</div>
  </section>

  <section>
    <h2>CPU Média Aproximada</h2>
    <div class="chart">{bar_chart(general_rows, "media_cpu_usage_approx_percent", "CPU média aproximada (%)", "#8a4fbd")}</div>
    {cpu_warning(show_cpu_warning)}
  </section>

  <section>
    <h2>Variação por Nome</h2>
    {by_name_table(by_name_rows)}
  </section>

  <section>
    <h2>Conclusão Automática</h2>
    <div class="conclusion">{escape(conclusion)}</div>
  </section>
</main>
</body>
</html>
"""


def summary_cards(summary, metadata, best_strategy, best_speedup):
    cards = [
        ("Máquina", summary.get("machinePython") or metadata.get("machinePython")),
        ("Dataset", summary.get("dataset") or metadata.get("dataset")),
        ("Data/hora", summary.get("startedAt") or metadata.get("startedAt")),
        ("Execuções esperadas", summary.get("totalExecucoesEsperadas")),
        ("Execuções com sucesso", summary.get("totalExecucoesComSucesso")),
        ("Execuções com erro", summary.get("totalExecucoesComErro")),
        ("Melhor estratégia", strategy_display(best_strategy)),
        ("Maior Speedup", speedup_display(best_speedup)),
    ]
    return "\n".join(card(label, value) for label, value in cards)


def card(label, value):
    return f"""
    <div class="card">
      <div class="label">{escape(label)}</div>
      <div class="value">{escape(format_value(value))}</div>
    </div>"""


def environment_table(environment):
    rows = [
        ("Versão do Java", environment.get("java_version")),
        ("Sistema operacional", environment.get("os_name")),
        ("Arquitetura", environment.get("os_arch")),
        ("Processadores disponíveis", environment.get("available_processors")),
        ("Máquina Java", environment.get("machine_java")),
    ]
    return simple_table(["Item", "Valor"], rows)


def sampled_names_table(sampled_names):
    rows = []
    for item in sampled_names:
        rows.append([
            item.get("nome_id"),
            item.get("nome"),
            item.get("arquivo"),
            item.get("linha"),
        ])
    return simple_table(["nome_id", "nome sorteado", "arquivo sorteado", "linha sorteada"], rows)


def general_table(rows):
    fields = [
        "strategy",
        "threads_per_file",
        "quantidade_execucoes",
        "media_wall_time_ms",
        "menor_wall_time_ms",
        "maior_wall_time_ms",
        "media_process_cpu_time_ms",
        "media_cpu_usage_approx_percent",
        "media_heap_delta_bytes",
    ]
    best = min_numeric_row(rows, "media_wall_time_ms")
    return dict_table(fields, rows, highlight_row=best)


def speedup_table(rows):
    fields = [
        "strategy",
        "threads_per_file",
        "media_wall_time_ms",
        "tempo_base_sequencial_ms",
        "speedup",
    ]
    best = max_numeric_row(rows, "speedup")
    return dict_table(fields, rows, highlight_row=best)


def by_name_table(rows):
    fields = [
        "nome_id",
        "nome_sorteado",
        "strategy",
        "threads_per_file",
        "quantidade_execucoes",
        "media_wall_time_ms",
        "menor_wall_time_ms",
        "maior_wall_time_ms",
    ]
    return dict_table(fields, rows)


def simple_table(headers, rows):
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{escape(format_value(value))}</td>" for value in row) + "</tr>")
    return f"""
    <div class="table-wrap">
      <table>
        <thead><tr>{''.join(f'<th>{escape(header)}</th>' for header in headers)}</tr></thead>
        <tbody>{''.join(body)}</tbody>
      </table>
    </div>"""


def dict_table(fields, rows, highlight_row=None):
    body = []
    for row in rows:
        css = " class=\"highlight-best\"" if highlight_row is row else ""
        body.append(
            f"<tr{css}>"
            + "".join(f"<td>{escape(format_cell(row.get(field)))}</td>" for field in fields)
            + "</tr>"
        )
    return f"""
    <div class="table-wrap">
      <table>
        <thead><tr>{''.join(f'<th>{escape(field)}</th>' for field in fields)}</tr></thead>
        <tbody>{''.join(body)}</tbody>
      </table>
    </div>"""


def bar_chart(rows, value_field, title, color):
    chart_rows = rows_with_number(rows, value_field)
    if not chart_rows:
        return f"<p>Nao ha dados numericos suficientes para gerar o grafico de {escape(title)}.</p>"

    max_value = max(as_float(row.get(value_field)) for row in chart_rows)
    if not max_value or max_value <= 0:
        return f"<p>Os valores de {escape(title)} estao zerados ou ausentes.</p>"

    bar_width = 54
    gap = 28
    left = 58
    top = 28
    chart_height = 190
    label_height = 70
    width = max(680, left + len(chart_rows) * (bar_width + gap) + 20)
    height = top + chart_height + label_height
    axis_y = top + chart_height

    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{axis_y}" stroke="#9aa7b4" />',
        f'<line x1="{left}" y1="{axis_y}" x2="{width - 16}" y2="{axis_y}" stroke="#9aa7b4" />',
        f'<text x="{left}" y="16" fill="#475467" font-size="12">{escape(title)}</text>',
    ]

    for index, row in enumerate(chart_rows):
        value = as_float(row.get(value_field))
        bar_height = max(1, (value / max_value) * (chart_height - 20))
        x = left + 18 + index * (bar_width + gap)
        y = axis_y - bar_height
        label = compact_strategy(row)
        parts.extend([
            f'<rect x="{x}" y="{y:.2f}" width="{bar_width}" height="{bar_height:.2f}" rx="4" fill="{color}" />',
            f'<text x="{x + bar_width / 2}" y="{y - 6:.2f}" text-anchor="middle" fill="#263442" font-size="11">{escape(format_number(value))}</text>',
            f'<text x="{x + bar_width / 2}" y="{axis_y + 18}" text-anchor="middle" fill="#475467" font-size="10">{escape(label)}</text>',
        ])

    parts.append("</svg>")
    return "".join(parts)


def cpu_warning(show):
    if not show:
        return ""
    return '<div class="note">A métrica de CPU pode ser pouco representativa em execuções muito rápidas.</div>'


def build_conclusion(general_rows, speedup_rows):
    fastest = min_numeric_row(general_rows, "media_wall_time_ms")
    best_speedup = max_numeric_row(speedup_rows, "speedup")
    slower_parallel = parallel_slower_than_sequential(speedup_rows)

    if not fastest:
        return "Nao houve dados suficientes para gerar uma conclusao automatica."

    text = (
        f"Neste benchmark, a estratégia com menor tempo médio foi {strategy_name(fastest)}, "
        f"com média de {format_number(as_float(fastest.get('media_wall_time_ms')))} ms."
    )

    if best_speedup:
        text += (
            f" O maior Speedup observado foi {format_number(as_float(best_speedup.get('speedup')))} "
            f"em relação à busca sequencial, usando {strategy_name(best_speedup)}."
        )

    if slower_parallel:
        text += (
            " Pelo menos uma configuração paralela ficou mais lenta que a sequencial, "
            "o que indica overhead de criação, agendamento e coordenação de Threads."
        )

    text += (
        " Estratégias com muitas Threads podem apresentar overhead, especialmente quando a busca termina "
        "rapidamente ou quando o volume de dados não é grande o suficiente."
    )
    return text


def parallel_slower_than_sequential(speedup_rows):
    for row in speedup_rows:
        if row.get("strategy") != "sequencial":
            value = as_float(row.get("speedup"))
            if value is not None and value < 1:
                return True
    return False


def extract_environment(raw_rows):
    for row in raw_rows:
        if row.get("success") == "True" or row.get("success") == "true":
            return {
                "java_version": row.get("java_version"),
                "os_name": row.get("os_name"),
                "os_arch": row.get("os_arch"),
                "available_processors": row.get("available_processors"),
                "machine_java": row.get("machine_java"),
            }
    return {}


def rows_with_number(rows, field):
    return [row for row in rows if as_float(row.get(field)) is not None]


def min_numeric_row(rows, field):
    candidates = rows_with_number(rows, field)
    if not candidates:
        return None
    return min(candidates, key=lambda row: as_float(row.get(field)))


def max_numeric_row(rows, field):
    candidates = rows_with_number(rows, field)
    if not candidates:
        return None
    return max(candidates, key=lambda row: as_float(row.get(field)))


def compact_strategy(row):
    strategy = row.get("strategy", "")
    threads = row.get("threads_per_file", "0")
    if strategy == "multiThreadPerFile":
        return f"multi N={threads}"
    if strategy == "oneThreadPerFile":
        return "one/file"
    if strategy == "singleThread":
        return "single"
    return strategy


def strategy_name(row):
    strategy = row.get("strategy", "")
    threads = row.get("threads_per_file") or row.get("threadsPerFile") or 0
    if strategy == "multiThreadPerFile":
        return f"multiThreadPerFile N={threads}"
    return strategy


def strategy_display(row):
    if not row:
        return "n/a"
    value = strategy_name(row)
    average = row.get("mediaWallTimeMs")
    if average is not None:
        value += f" ({format_number(as_float(average))} ms)"
    return value


def speedup_display(row):
    if not row:
        return "n/a"
    value = strategy_name(row)
    speedup = row.get("speedup")
    if speedup is not None:
        value += f" ({format_number(as_float(speedup))}x)"
    return value


def format_cell(value):
    number = as_float(value)
    if number is not None and not is_int_like_text(value):
        return format_number(number)
    return format_value(value)


def format_value(value):
    if value is None or value == "":
        return "n/a"
    return str(value)


def format_number(value):
    if value is None:
        return "n/a"
    return f"{value:.4f}".rstrip("0").rstrip(".")


def is_int_like_text(value):
    if value is None:
        return False
    text = str(value)
    return text.isdigit() or (text.startswith("-") and text[1:].isdigit())


def as_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def escape(value):
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


if __name__ == "__main__":
    main()
