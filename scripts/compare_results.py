import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"
MAIN_DATASETS = {"pequeno", "grande"}

REQUIRED_FILES = [
    "data/resultados_brutos.csv",
    "data/medias_gerais.csv",
    "data/speedup.csv",
    "data/resumo_benchmark.json",
]

RAW_OUTPUT_FIELDS = [
    "source_run_folder",
    "source_machine",
    "source_dataset",
    "source_timestamp",
    "machine_python",
    "machine_java",
    "dataset",
    "nome_id",
    "nome_sorteado",
    "arquivo_sorteado",
    "linha_sorteada",
    "strategy",
    "threads_per_file",
    "repeticao",
    "success",
    "found",
    "file_name",
    "line_number",
    "line_content",
    "wall_time_ms",
    "wall_time_ns",
    "process_cpu_time_ms",
    "cpu_usage_approx_percent",
    "heap_delta_bytes",
    "available_processors",
    "java_version",
    "os_name",
    "os_arch",
    "error_message",
]

MACHINE_AVERAGE_FIELDS = [
    "machine",
    "dataset",
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

GROUP_AVERAGE_FIELDS = [
    "dataset",
    "strategy",
    "threads_per_file",
    "quantidade_maquinas",
    "quantidade_execucoes",
    "media_wall_time_ms",
    "menor_wall_time_ms",
    "maior_wall_time_ms",
    "media_process_cpu_time_ms",
    "media_cpu_usage_approx_percent",
    "media_heap_delta_bytes",
]

SPEEDUP_MACHINE_FIELDS = [
    "machine",
    "dataset",
    "strategy",
    "threads_per_file",
    "media_wall_time_ms",
    "tempo_base_sequencial_ms",
    "speedup",
]

SPEEDUP_GROUP_FIELDS = [
    "dataset",
    "strategy",
    "threads_per_file",
    "media_wall_time_ms",
    "tempo_base_sequencial_ms",
    "speedup",
]


def main():
    args = parse_args()
    results_dir = resolve_results_dir(args.results_dir)
    complete_runs, ignored_runs = discover_run_folders(results_dir)

    if not complete_runs:
        raise SystemExit(f"Erro: nenhuma execucao completa encontrada em {results_dir}.")

    consolidated_rows = []
    for run_dir in complete_runs:
        consolidated_rows.extend(load_raw_rows(run_dir))

    machine_averages = calculate_machine_averages(consolidated_rows)
    group_averages = calculate_group_averages(machine_averages)
    speedup_by_machine = calculate_speedup_by_machine(machine_averages)
    speedup_group = calculate_speedup_group(group_averages)

    output_dir = create_output_dir(results_dir)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "resultados_consolidados": data_dir / "resultados_consolidados.csv",
        "medias_por_maquina": data_dir / "medias_por_maquina.csv",
        "medias_gerais_grupo": data_dir / "medias_gerais_grupo.csv",
        "speedup_por_maquina": data_dir / "speedup_por_maquina.csv",
        "speedup_geral_grupo": data_dir / "speedup_geral_grupo.csv",
        "resumo_grupo": data_dir / "resumo_grupo.json",
        "group_report": output_dir / "group_report.html",
    }

    write_csv(paths["resultados_consolidados"], RAW_OUTPUT_FIELDS, consolidated_rows)
    write_csv(paths["medias_por_maquina"], MACHINE_AVERAGE_FIELDS, machine_averages)
    write_csv(paths["medias_gerais_grupo"], GROUP_AVERAGE_FIELDS, group_averages)
    write_csv(paths["speedup_por_maquina"], SPEEDUP_MACHINE_FIELDS, speedup_by_machine)
    write_csv(paths["speedup_geral_grupo"], SPEEDUP_GROUP_FIELDS, speedup_group)

    summary = build_summary(
        complete_runs,
        ignored_runs,
        consolidated_rows,
        group_averages,
        speedup_group,
        paths,
    )
    write_json(paths["resumo_grupo"], summary)
    write_html(paths["group_report"], build_html(summary, machine_averages, group_averages, speedup_by_machine, speedup_group))

    print("Relatorio consolidado gerado com sucesso.")
    print()
    print("Pasta:")
    print(display_path(output_dir))
    print()
    print("Abra:")
    print(display_path(paths["group_report"]))


def parse_args():
    parser = argparse.ArgumentParser(description="Consolida resultados de benchmark de varias maquinas.")
    parser.add_argument("--results-dir", default=str(DEFAULT_RESULTS_DIR), help="Pasta results/ com execucoes individuais.")
    return parser.parse_args()


def resolve_results_dir(value):
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists() or not path.is_dir():
        raise SystemExit(f"Erro: pasta de resultados nao encontrada: {path}")
    return path


def discover_run_folders(results_dir):
    complete = []
    ignored = []

    for child in sorted(results_dir.iterdir(), key=lambda path: path.name.lower()):
        if not child.is_dir():
            continue
        if child.name.startswith("group_report_"):
            continue

        missing = [relative for relative in REQUIRED_FILES if not (child / relative).exists()]
        if missing:
            ignored.append({"folder": child.name, "reason": "arquivos ausentes: " + ", ".join(missing)})
            print(f"Aviso: ignorando {child.name}; arquivos ausentes: {', '.join(missing)}", file=sys.stderr)
            continue

        complete.append(child)

    return complete, ignored


def load_raw_rows(run_dir):
    summary = read_json(run_dir / "data" / "resumo_benchmark.json")
    rows = read_csv(run_dir / "data" / "resultados_brutos.csv")
    loaded = []

    fallback_machine = first_non_empty(
        summary.get("machinePython"),
        machine_from_folder(run_dir.name),
        "unknown",
    )
    source_dataset = summary.get("dataset", "")
    source_timestamp = first_non_empty(summary.get("startedAt"), summary.get("finishedAt"), "")

    for row in rows:
        normalized = normalize_raw_row(row)
        machine = choose_machine(normalized, fallback_machine)
        dataset = first_non_empty(normalized.get("dataset"), source_dataset)
        normalized.update({
            "source_run_folder": run_dir.name,
            "source_machine": machine,
            "source_dataset": dataset,
            "source_timestamp": source_timestamp,
            "machine": machine,
            "dataset": dataset,
        })
        loaded.append(normalized)

    return loaded


def normalize_raw_row(row):
    return {
        "machine_python": get_value(row, "machine_python", "machineNamePython", "machine"),
        "machine_java": get_value(row, "machine_java", "machineNameJava"),
        "dataset": get_value(row, "dataset"),
        "nome_id": get_value(row, "nome_id", "nomeId"),
        "nome_sorteado": get_value(row, "nome_sorteado", "nomeSorteado"),
        "arquivo_sorteado": get_value(row, "arquivo_sorteado", "arquivoSorteado"),
        "linha_sorteada": get_value(row, "linha_sorteada", "linhaSorteada"),
        "strategy": get_value(row, "strategy"),
        "threads_per_file": normalize_threads(get_value(row, "threads_per_file", "threadsPerFile")),
        "repeticao": get_value(row, "repeticao"),
        "success": get_value(row, "success"),
        "found": get_value(row, "found"),
        "file_name": get_value(row, "file_name", "fileName"),
        "line_number": get_value(row, "line_number", "lineNumber"),
        "line_content": get_value(row, "line_content", "lineContent"),
        "wall_time_ms": get_value(row, "wall_time_ms", "wallTimeMs"),
        "wall_time_ns": get_value(row, "wall_time_ns", "wallTimeNs"),
        "process_cpu_time_ms": get_value(row, "process_cpu_time_ms", "processCpuTimeMs"),
        "cpu_usage_approx_percent": get_value(row, "cpu_usage_approx_percent", "cpuUsageApproxPercent"),
        "heap_delta_bytes": get_value(row, "heap_delta_bytes", "heapDeltaBytes"),
        "available_processors": get_value(row, "available_processors", "availableProcessors"),
        "java_version": get_value(row, "java_version", "javaVersion"),
        "os_name": get_value(row, "os_name", "osName"),
        "os_arch": get_value(row, "os_arch", "osArch"),
        "error_message": get_value(row, "error_message", "errorMessage"),
    }


def calculate_machine_averages(rows):
    groups = defaultdict(list)

    for row in rows:
        wall_time = to_float(row.get("wall_time_ms"))
        if wall_time is None:
            continue
        key = (
            row.get("machine") or "unknown",
            row.get("dataset") or "unknown",
            row.get("strategy") or "unknown",
            normalize_threads(row.get("threads_per_file")),
        )
        groups[key].append(row)

    result = []
    for (machine, dataset, strategy, threads), grouped_rows in groups.items():
        wall_times = numeric_values(grouped_rows, "wall_time_ms")
        result.append({
            "machine": machine,
            "dataset": dataset,
            "strategy": strategy,
            "threads_per_file": threads,
            "quantidade_execucoes": len(grouped_rows),
            "media_wall_time_ms": average(wall_times),
            "menor_wall_time_ms": min(wall_times) if wall_times else None,
            "maior_wall_time_ms": max(wall_times) if wall_times else None,
            "media_process_cpu_time_ms": average(numeric_values(grouped_rows, "process_cpu_time_ms")),
            "media_cpu_usage_approx_percent": average(numeric_values(grouped_rows, "cpu_usage_approx_percent")),
            "media_heap_delta_bytes": average(numeric_values(grouped_rows, "heap_delta_bytes")),
        })

    return sorted(result, key=lambda row: (row["dataset"], row["machine"], strategy_sort_key(row)))


def calculate_group_averages(machine_averages):
    groups = defaultdict(list)

    for row in machine_averages:
        key = (row["dataset"], row["strategy"], normalize_threads(row["threads_per_file"]))
        groups[key].append(row)

    result = []
    for (dataset, strategy, threads), rows in groups.items():
        wall_times = numeric_values(rows, "media_wall_time_ms")
        result.append({
            "dataset": dataset,
            "strategy": strategy,
            "threads_per_file": threads,
            "quantidade_maquinas": len({row["machine"] for row in rows}),
            "quantidade_execucoes": sum_int(rows, "quantidade_execucoes"),
            "media_wall_time_ms": average(wall_times),
            "menor_wall_time_ms": min(numeric_values(rows, "menor_wall_time_ms")) if numeric_values(rows, "menor_wall_time_ms") else None,
            "maior_wall_time_ms": max(numeric_values(rows, "maior_wall_time_ms")) if numeric_values(rows, "maior_wall_time_ms") else None,
            "media_process_cpu_time_ms": average(numeric_values(rows, "media_process_cpu_time_ms")),
            "media_cpu_usage_approx_percent": average(numeric_values(rows, "media_cpu_usage_approx_percent")),
            "media_heap_delta_bytes": average(numeric_values(rows, "media_heap_delta_bytes")),
        })

    return sorted(result, key=lambda row: (row["dataset"], strategy_sort_key(row)))


def calculate_speedup_by_machine(machine_averages):
    base_times = {}
    for row in machine_averages:
        if row["strategy"] == "sequencial" and normalize_threads(row["threads_per_file"]) == "0":
            base_times[(row["machine"], row["dataset"])] = to_float(row["media_wall_time_ms"])

    result = []
    for row in machine_averages:
        base = base_times.get((row["machine"], row["dataset"]))
        current = to_float(row["media_wall_time_ms"])
        speedup = None
        if base is not None and current not in (None, 0):
            speedup = base / current
        result.append({
            "machine": row["machine"],
            "dataset": row["dataset"],
            "strategy": row["strategy"],
            "threads_per_file": normalize_threads(row["threads_per_file"]),
            "media_wall_time_ms": current,
            "tempo_base_sequencial_ms": base,
            "speedup": speedup,
        })

    return sorted(result, key=lambda row: (row["dataset"], row["machine"], strategy_sort_key(row)))


def calculate_speedup_group(group_averages):
    base_times = {}
    for row in group_averages:
        if row["strategy"] == "sequencial" and normalize_threads(row["threads_per_file"]) == "0":
            base_times[row["dataset"]] = to_float(row["media_wall_time_ms"])

    result = []
    for row in group_averages:
        base = base_times.get(row["dataset"])
        current = to_float(row["media_wall_time_ms"])
        speedup = None
        if base is not None and current not in (None, 0):
            speedup = base / current
        result.append({
            "dataset": row["dataset"],
            "strategy": row["strategy"],
            "threads_per_file": normalize_threads(row["threads_per_file"]),
            "media_wall_time_ms": current,
            "tempo_base_sequencial_ms": base,
            "speedup": speedup,
        })

    return sorted(result, key=lambda row: (row["dataset"], strategy_sort_key(row)))


def build_summary(complete_runs, ignored_runs, consolidated_rows, group_averages, speedup_group, paths):
    datasets = sorted({row["dataset"] for row in consolidated_rows if row.get("dataset")})
    main_datasets = [dataset for dataset in datasets if dataset in MAIN_DATASETS]
    extra_datasets = [dataset for dataset in datasets if dataset not in MAIN_DATASETS]
    machines = sorted({row["source_machine"] for row in consolidated_rows if row.get("source_machine")})

    return {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "totalPastasAnalisadas": len(complete_runs),
        "totalPastasIgnoradas": len(ignored_runs),
        "pastasIgnoradas": ignored_runs,
        "totalMaquinasIdentificadas": len(machines),
        "maquinas": machines,
        "datasetsEncontrados": datasets,
        "datasetsPrincipaisEncontrados": main_datasets,
        "datasetsComplementaresEncontrados": extra_datasets,
        "totalExecucoesConsolidadas": len(consolidated_rows),
        "melhorEstrategiaPorDataset": best_strategy_by_dataset(group_averages),
        "maiorSpeedupPorDataset": best_speedup_by_dataset(speedup_group),
        "arquivosGerados": {name: str(path) for name, path in paths.items()},
    }


def build_html(summary, machine_averages, group_averages, speedup_by_machine, speedup_group):
    main_group = [row for row in group_averages if row["dataset"] in MAIN_DATASETS]
    main_speedup = [row for row in speedup_group if row["dataset"] in MAIN_DATASETS]
    main_machine_speedup = [row for row in speedup_by_machine if row["dataset"] in MAIN_DATASETS]
    extra_group = [row for row in group_averages if row["dataset"] not in MAIN_DATASETS]
    extra_speedup = [row for row in speedup_group if row["dataset"] not in MAIN_DATASETS]
    best_speedup = max_row(speedup_group, "speedup")

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Relatório Consolidado do Grupo - Benchmark de Busca de Nomes</title>
  <style>
    :root {{
      --bg: #f5f7fb;
      --panel: #ffffff;
      --text: #1e2936;
      --muted: #667085;
      --line: #d8e0ea;
      --blue: #1264a3;
      --green: #16845f;
      --purple: #7653b7;
      --amber: #9a6700;
      --shadow: 0 10px 28px rgba(31, 42, 55, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--text); font: 15px/1.5 Arial, Helvetica, sans-serif; }}
    main {{ width: min(1220px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 56px; }}
    header {{ margin-bottom: 24px; border-bottom: 1px solid var(--line); padding-bottom: 18px; }}
    h1 {{ margin: 0 0 6px; font-size: 30px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 10px; font-size: 22px; }}
    h3 {{ margin: 22px 0 10px; font-size: 17px; }}
    p {{ margin: 0 0 12px; }}
    .subtitle, .muted {{ color: var(--muted); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-bottom: 22px; }}
    .card, section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; box-shadow: var(--shadow); }}
    .card {{ padding: 16px; }}
    .card .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; margin-bottom: 6px; }}
    .card .value {{ font-size: 18px; font-weight: 700; word-break: break-word; }}
    section {{ padding: 20px; margin: 18px 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 9px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ background: #eef3f8; font-weight: 700; color: #263442; }}
    tbody tr:nth-child(even) td {{ background: #fafcff; }}
    tr.best td {{ background: #edf8f2 !important; }}
    .table-wrap {{ overflow-x: auto; }}
    .chart {{ width: 100%; overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: #fbfdff; padding: 10px; margin-bottom: 14px; }}
    .note {{ color: var(--amber); background: #fff7dd; border: 1px solid #f0d98c; padding: 10px 12px; border-radius: 8px; margin: 10px 0; }}
    .conclusion {{ background: #f8fbff; border-left: 4px solid var(--blue); padding: 14px 16px; border-radius: 6px; font-size: 16px; }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Relatório Consolidado do Grupo - Benchmark de Busca de Nomes</h1>
    <p class="subtitle">Consolidação automática de execuções individuais salvas em <code>results/</code>.</p>
  </header>

  <div class="grid">
    {summary_cards(summary, best_speedup)}
  </div>

  <section>
    <h2>1. Análise Principal da Atividade</h2>
    <p>Esta seção apresenta apenas os resultados relacionados aos datasets principais da atividade, isto é, os datasets pequeno e grande. O foco é comparar a busca sequencial com as estratégias que utilizam Threads, analisando o tempo médio e o Speedup.</p>
    {main_part_html(main_group, main_speedup, main_machine_speedup)}
  </section>

  <section>
    <h2>2. Análises Complementares</h2>
    <p>Esta seção apresenta análises adicionais que vão além do escopo mínimo da atividade, incluindo datasets sintéticos maiores, métricas de CPU, memória e impacto da quantidade de Threads.</p>
    {complementary_part_html(extra_group, extra_speedup, group_averages, speedup_group)}
  </section>
</main>
</body>
</html>
"""


def main_part_html(group_rows, speedup_rows, machine_speedup_rows):
    chunks = [
        "<h3>Médias gerais do grupo</h3>",
        table(group_rows, [
            ("dataset", "dataset"),
            ("estratégia", "strategy"),
            ("threads por arquivo", "threads_per_file"),
            ("quantidade de máquinas", "quantidade_maquinas"),
            ("quantidade de execuções", "quantidade_execucoes"),
            ("tempo médio", "media_wall_time_ms"),
            ("menor tempo", "menor_wall_time_ms"),
            ("maior tempo", "maior_wall_time_ms"),
        ], best=min_row(group_rows, "media_wall_time_ms")),
        "<h3>Speedup geral do grupo</h3>",
        table(speedup_rows, [
            ("dataset", "dataset"),
            ("estratégia", "strategy"),
            ("threads por arquivo", "threads_per_file"),
            ("tempo médio", "media_wall_time_ms"),
            ("tempo base sequencial", "tempo_base_sequencial_ms"),
            ("Speedup", "speedup"),
        ], best=max_row(speedup_rows, "speedup")),
    ]

    for dataset in ("pequeno", "grande"):
        dataset_group = [row for row in group_rows if row["dataset"] == dataset]
        dataset_speedup = [row for row in speedup_rows if row["dataset"] == dataset]
        if not dataset_group:
            chunks.append(f'<div class="note">Nao ha dados consolidados para o dataset {escape(dataset)}.</div>')
            continue
        chunks.append(f"<h3>Tempo médio por estratégia - dataset {escape(dataset)}</h3>")
        chunks.append(f'<div class="chart">{bar_chart(dataset_group, "media_wall_time_ms", "ms", "#1264a3")}</div>')
        chunks.append(f"<h3>Speedup por estratégia - dataset {escape(dataset)}</h3>")
        chunks.append(f'<div class="chart">{bar_chart(dataset_speedup, "speedup", "x", "#16845f")}</div>')

    chunks.extend([
        "<h3>Comparação por máquina</h3>",
        table(machine_speedup_rows, [
            ("máquina", "machine"),
            ("dataset", "dataset"),
            ("estratégia", "strategy"),
            ("threads por arquivo", "threads_per_file"),
            ("tempo médio", "media_wall_time_ms"),
            ("Speedup", "speedup"),
        ], best=max_row(machine_speedup_rows, "speedup")),
        "<h3>Conclusão da Parte 1</h3>",
        f'<div class="conclusion">{escape(main_conclusion(group_rows, speedup_rows))}</div>',
    ])
    return "\n".join(chunks)


def complementary_part_html(extra_group, extra_speedup, all_group, all_speedup):
    chunks = []
    if extra_group:
        chunks.extend([
            "<h3>Datasets sintéticos encontrados</h3>",
            synthetic_summary_table(extra_group, extra_speedup),
        ])
        for dataset in sorted({row["dataset"] for row in extra_group}):
            dataset_group = [row for row in extra_group if row["dataset"] == dataset]
            dataset_speedup = [row for row in extra_speedup if row["dataset"] == dataset]
            chunks.append(f"<h3>Tempo médio por estratégia - {escape(dataset)}</h3>")
            chunks.append(f'<div class="chart">{bar_chart(dataset_group, "media_wall_time_ms", "ms", "#1264a3")}</div>')
            chunks.append(f"<h3>Speedup por estratégia - {escape(dataset)}</h3>")
            chunks.append(f'<div class="chart">{bar_chart(dataset_speedup, "speedup", "x", "#16845f")}</div>')
    else:
        chunks.append('<div class="note">Nao foram encontrados datasets complementares nesta consolidacao.</div>')

    chunks.extend(cpu_section(all_group),)
    chunks.extend(memory_section(all_group),)
    chunks.extend(thread_impact_section(all_group, all_speedup),)
    chunks.extend([
        "<h3>Conclusão da Parte 2</h3>",
        f'<div class="conclusion">{escape(complementary_conclusion(extra_group, extra_speedup, all_group))}</div>',
    ])
    return "\n".join(chunks)


def cpu_section(group_rows):
    cpu_rows = [row for row in group_rows if to_float(row.get("media_cpu_usage_approx_percent")) is not None or to_float(row.get("media_process_cpu_time_ms")) is not None]
    if not cpu_rows or all((to_float(row.get("media_cpu_usage_approx_percent")) or 0) == 0 for row in cpu_rows):
        return ['<h3>CPU</h3><div class="note">A métrica de CPU pode ser pouco representativa em execuções muito rápidas ou quando o sistema operacional/JVM retorna valores muito baixos.</div>']
    return [
        "<h3>CPU</h3>",
        table(cpu_rows, [
            ("dataset", "dataset"),
            ("estratégia", "strategy"),
            ("threads", "threads_per_file"),
            ("tempo CPU médio (ms)", "media_process_cpu_time_ms"),
            ("CPU média aproximada (%)", "media_cpu_usage_approx_percent"),
        ]),
        f'<div class="chart">{bar_chart(cpu_rows, "media_cpu_usage_approx_percent", "%", "#7653b7")}</div>',
    ]


def memory_section(group_rows):
    memory_rows = [row for row in group_rows if to_float(row.get("media_heap_delta_bytes")) is not None]
    if not memory_rows:
        return ['<h3>Memória</h3><div class="note">Nao ha dados de heapDelta disponíveis para esta consolidacao.</div>']
    rows = []
    for row in memory_rows:
        copied = dict(row)
        value = to_float(row.get("media_heap_delta_bytes"))
        copied["media_heap_delta_mb"] = value / (1024 * 1024) if value is not None else None
        rows.append(copied)
    return [
        "<h3>Memória</h3>",
        table(rows, [
            ("dataset", "dataset"),
            ("estratégia", "strategy"),
            ("threads", "threads_per_file"),
            ("heapDelta médio (MB)", "media_heap_delta_mb"),
        ]),
    ]


def thread_impact_section(group_rows, speedup_rows):
    multi_rows = [row for row in group_rows if row["strategy"] == "multiThreadPerFile" and normalize_threads(row["threads_per_file"]) in {"2", "4", "8"}]
    speedup_index = {(row["dataset"], normalize_threads(row["threads_per_file"])): row for row in speedup_rows if row["strategy"] == "multiThreadPerFile"}
    rows = []
    for row in multi_rows:
        copied = dict(row)
        speedup = speedup_index.get((row["dataset"], normalize_threads(row["threads_per_file"])), {})
        copied["speedup"] = speedup.get("speedup")
        rows.append(copied)
    if not rows:
        return ['<h3>Impacto da quantidade de Threads</h3><div class="note">Nao ha dados suficientes para comparar N=2, N=4 e N=8.</div>']
    return [
        "<h3>Impacto da quantidade de Threads</h3>",
        table(rows, [
            ("dataset", "dataset"),
            ("threads", "threads_per_file"),
            ("tempo médio", "media_wall_time_ms"),
            ("Speedup", "speedup"),
            ("CPU média (%)", "media_cpu_usage_approx_percent"),
            ("heapDelta médio (bytes)", "media_heap_delta_bytes"),
        ]),
    ]


def synthetic_summary_table(group_rows, speedup_rows):
    rows = []
    for dataset in sorted({row["dataset"] for row in group_rows}):
        dataset_rows = [row for row in group_rows if row["dataset"] == dataset]
        dataset_speedups = [row for row in speedup_rows if row["dataset"] == dataset]
        best_time = min_row(dataset_rows, "media_wall_time_ms") or {}
        best_speed = max_row(dataset_speedups, "speedup") or {}
        rows.append({
            "dataset": dataset,
            "quantidade_maquinas": max([int(to_float(row.get("quantidade_maquinas")) or 0) for row in dataset_rows] or [0]),
            "quantidade_execucoes": sum_int(dataset_rows, "quantidade_execucoes"),
            "melhor_estrategia": strategy_label(best_time),
            "maior_speedup": best_speed.get("speedup"),
        })
    return table(rows, [
        ("dataset", "dataset"),
        ("quantidade de máquinas", "quantidade_maquinas"),
        ("quantidade de execuções", "quantidade_execucoes"),
        ("melhor estratégia", "melhor_estrategia"),
        ("maior Speedup", "maior_speedup"),
    ], best=max_row(rows, "maior_speedup"))


def summary_cards(summary, best_speedup):
    cards = [
        ("Total de máquinas", summary.get("totalMaquinasIdentificadas")),
        ("Total de execuções", summary.get("totalExecucoesConsolidadas")),
        ("Datasets analisados", len(summary.get("datasetsEncontrados", []))),
        ("Pastas analisadas", summary.get("totalPastasAnalisadas")),
        ("Pastas ignoradas", summary.get("totalPastasIgnoradas")),
        ("Melhor Speedup geral", speedup_display(best_speedup)),
    ]
    return "\n".join(card(label, value) for label, value in cards)


def card(label, value):
    return f'<div class="card"><div class="label">{escape(str(label))}</div><div class="value">{escape(format_value(value))}</div></div>'


def table(rows, columns, best=None):
    if not rows:
        return '<div class="note">Nao ha dados disponiveis para esta tabela.</div>'
    header = "".join(f"<th>{escape(label)}</th>" for label, _ in columns)
    body = []
    for row in rows:
        cls = ' class="best"' if best is row else ""
        cells = "".join(f"<td>{escape(format_value(row.get(field)))}</td>" for _, field in columns)
        body.append(f"<tr{cls}>{cells}</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def bar_chart(rows, value_field, unit, color):
    chart_rows = [row for row in rows if to_float(row.get(value_field)) is not None]
    if not chart_rows:
        return "<p>Dados insuficientes para gerar grafico.</p>"
    max_value = max(to_float(row.get(value_field)) for row in chart_rows)
    if not max_value or max_value <= 0:
        return "<p>Valores zerados ou ausentes.</p>"

    bar_width = 54
    gap = 28
    left = 58
    top = 28
    chart_height = 190
    label_height = 74
    width = max(720, left + len(chart_rows) * (bar_width + gap) + 22)
    axis_y = top + chart_height
    height = axis_y + label_height
    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{axis_y}" stroke="#9aa7b4" />',
        f'<line x1="{left}" y1="{axis_y}" x2="{width - 16}" y2="{axis_y}" stroke="#9aa7b4" />',
    ]
    for index, row in enumerate(chart_rows):
        value = to_float(row.get(value_field))
        bar_height = max(1, (value / max_value) * (chart_height - 20))
        x = left + 18 + index * (bar_width + gap)
        y = axis_y - bar_height
        label = compact_strategy(row)
        parts.extend([
            f'<rect x="{x}" y="{y:.2f}" width="{bar_width}" height="{bar_height:.2f}" rx="4" fill="{color}" />',
            f'<text x="{x + bar_width / 2}" y="{y - 6:.2f}" text-anchor="middle" fill="#263442" font-size="11">{escape(format_number(value))}{escape(unit)}</text>',
            f'<text x="{x + bar_width / 2}" y="{axis_y + 18}" text-anchor="middle" fill="#475467" font-size="10">{escape(label)}</text>',
        ])
    parts.append("</svg>")
    return "".join(parts)


def main_conclusion(group_rows, speedup_rows):
    pieces = []
    for dataset in ("pequeno", "grande"):
        rows = [row for row in group_rows if row["dataset"] == dataset]
        if not rows:
            pieces.append(f"Nao houve dados para o dataset {dataset}.")
            continue
        fastest = min_row(rows, "media_wall_time_ms")
        pieces.append(f"No dataset {dataset}, a estrategia mais rapida foi {strategy_label(fastest)} com media de {format_number(to_float(fastest.get('media_wall_time_ms')))} ms.")
    parallel_won = any(row["strategy"] != "sequencial" and (to_float(row.get("speedup")) or 0) > 1 for row in speedup_rows)
    sequential_best = any((min_row([row for row in group_rows if row["dataset"] == dataset], "media_wall_time_ms") or {}).get("strategy") == "sequencial" for dataset in MAIN_DATASETS)
    if parallel_won:
        pieces.append("Ao menos uma estrategia paralela superou a sequencial em algum dataset principal.")
    if sequential_best:
        pieces.append("A sequencial continuou melhor em parte dos cenarios, sugerindo que o overhead de criacao, sincronizacao e coordenacao de Threads pode superar o ganho de paralelismo em volumes menores.")
    return " ".join(pieces)


def complementary_conclusion(extra_group, extra_speedup, all_group):
    if not extra_group:
        return "Nao houve datasets complementares nesta consolidacao. As analises extras ficam limitadas a CPU, memoria e impacto de Threads disponiveis nos datasets principais."
    best = max_row(extra_speedup, "speedup")
    fastest = min_row(extra_group, "media_wall_time_ms")
    text = f"Nos datasets complementares, a menor media foi de {strategy_label(fastest)} no dataset {fastest.get('dataset')}."
    if best:
        text += f" O maior Speedup complementar foi {format_number(to_float(best.get('speedup')))} em {strategy_label(best)} no dataset {best.get('dataset')}."
    multi_rows = [row for row in all_group if row["strategy"] == "multiThreadPerFile"]
    if multi_rows:
        best_multi = min_row(multi_rows, "media_wall_time_ms")
        text += f" Entre as configuracoes multiThreadPerFile, o melhor tempo medio observado foi com N={best_multi.get('threads_per_file')}."
    text += " Quando aumentar Threads nao reduz o tempo, isso e um sinal de overhead de agendamento, sincronizacao, leitura de arquivos ou volume insuficiente para compensar o paralelismo."
    return text


def best_strategy_by_dataset(group_averages):
    result = {}
    for dataset in sorted({row["dataset"] for row in group_averages}):
        best = min_row([row for row in group_averages if row["dataset"] == dataset], "media_wall_time_ms")
        if best:
            result[dataset] = {
                "strategy": best["strategy"],
                "threadsPerFile": best["threads_per_file"],
                "mediaWallTimeMs": best["media_wall_time_ms"],
            }
    return result


def best_speedup_by_dataset(speedup_rows):
    result = {}
    for dataset in sorted({row["dataset"] for row in speedup_rows}):
        best = max_row([row for row in speedup_rows if row["dataset"] == dataset], "speedup")
        if best:
            result[dataset] = {
                "strategy": best["strategy"],
                "threadsPerFile": best["threads_per_file"],
                "speedup": best["speedup"],
            }
    return result


def read_csv(path):
    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))
    except UnicodeDecodeError:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))


def read_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field)) for field in fields})


def write_json(path, payload):
    with path.open("w", encoding="utf-8", newline="") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def write_html(path, html):
    with path.open("w", encoding="utf-8", newline="") as file:
        file.write(html)


def create_output_dir(results_dir):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base = results_dir / f"group_report_{timestamp}"
    output = base
    counter = 2
    while output.exists():
        output = Path(f"{base}_{counter}")
        counter += 1
    output.mkdir(parents=True, exist_ok=False)
    return output


def get_value(row, *names):
    lower_map = {key.lower(): value for key, value in row.items()}
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
        value = lower_map.get(name.lower())
        if value not in (None, ""):
            return value
    return ""


def choose_machine(row, fallback):
    return first_non_empty(row.get("machine_python"), row.get("machine_java"), row.get("machineNameJava"), fallback, "unknown")


def first_non_empty(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return ""


def machine_from_folder(folder_name):
    parts = folder_name.split("_")
    if len(parts) >= 3:
        return "_".join(parts[2:])
    return folder_name


def normalize_threads(value):
    number = to_float(value)
    if number is None:
        return "0" if value in (None, "") else str(value)
    return str(int(number))


def numeric_values(rows, field):
    values = []
    for row in rows:
        value = to_float(row.get(field))
        if value is not None:
            values.append(value)
    return values


def average(values):
    if not values:
        return None
    return sum(values) / len(values)


def sum_int(rows, field):
    total = 0
    for row in rows:
        value = to_float(row.get(field))
        if value is not None:
            total += int(value)
    return total


def to_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def min_row(rows, field):
    candidates = [row for row in rows if to_float(row.get(field)) is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda row: to_float(row.get(field)))


def max_row(rows, field):
    candidates = [row for row in rows if to_float(row.get(field)) is not None]
    if not candidates:
        return None
    return max(candidates, key=lambda row: to_float(row.get(field)))


def strategy_sort_key(row):
    order = {
        "sequencial": 0,
        "singleThread": 1,
        "oneThreadPerFile": 2,
        "multiThreadPerFile": 3,
    }
    return (order.get(row.get("strategy"), 99), int(normalize_threads(row.get("threads_per_file")) or 0))


def compact_strategy(row):
    strategy = row.get("strategy", "")
    threads = normalize_threads(row.get("threads_per_file"))
    if strategy == "multiThreadPerFile":
        return f"multi N={threads}"
    if strategy == "oneThreadPerFile":
        return "one/file"
    if strategy == "singleThread":
        return "single"
    return strategy


def strategy_label(row):
    if not row:
        return "-"
    strategy = row.get("strategy", "")
    threads = normalize_threads(row.get("threads_per_file"))
    if strategy == "multiThreadPerFile":
        return f"multiThreadPerFile N={threads}"
    return strategy or "-"


def speedup_display(row):
    if not row:
        return "-"
    return f"{strategy_label(row)} ({format_number(to_float(row.get('speedup')))}x)"


def format_value(value):
    if value in (None, ""):
        return "-"
    number = to_float(value)
    if number is not None and not is_int_text(value):
        return format_number(number)
    return str(value)


def format_number(value):
    if value is None:
        return "-"
    return f"{value:.3f}".rstrip("0").rstrip(".")


def is_int_text(value):
    text = str(value)
    return text.isdigit() or (text.startswith("-") and text[1:].isdigit())


def csv_value(value):
    if value is None:
        return ""
    return value


def display_path(path):
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    main()
