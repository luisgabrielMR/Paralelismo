import csv
import json
import platform
import random
import socket
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = PROJECT_ROOT / "src"
OUT_DIR = PROJECT_ROOT / "out"
RESULTS_DIR = PROJECT_ROOT / "results"

DATASET_PEQUENO_PATH = PROJECT_ROOT / "dataset_p"
DATASET_GRANDE_PATH = PROJECT_ROOT / "dataset_g"

JAVA_COMMAND = "java"
JAVAC_COMMAND = "javac"
JAVA_MAIN_CLASS = "Main"

NOMES_ALEATORIOS = 5
REPETICOES_POR_ESTRATEGIA = 5
MULTI_THREAD_VALUES = [2, 4, 8]
COMPILE_BEFORE_RUN = True
GENERATE_REPORT_AFTER_BENCHMARK = True

STRATEGY_CONFIGS = [
    {"strategy": "sequencial", "threads_per_file": 0},
    {"strategy": "singleThread", "threads_per_file": 0},
    {"strategy": "oneThreadPerFile", "threads_per_file": 0},
    *[
        {"strategy": "multiThreadPerFile", "threads_per_file": value}
        for value in MULTI_THREAD_VALUES
    ],
]

RAW_CSV_FIELDS = [
    "run_id",
    "timestamp",
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
    "process_cpu_time_supported",
    "process_cpu_time_ms",
    "cpu_usage_approx_percent",
    "heap_used_before_bytes",
    "heap_used_after_bytes",
    "heap_delta_bytes",
    "available_processors",
    "java_version",
    "os_name",
    "os_arch",
    "error_message",
]

AVERAGE_FIELDS = [
    "dataset",
    "nome_id",
    "nome_sorteado",
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

GENERAL_AVERAGE_FIELDS = [
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

SPEEDUP_FIELDS = [
    "machine_python",
    "dataset",
    "strategy",
    "threads_per_file",
    "media_wall_time_ms",
    "tempo_base_sequencial_ms",
    "speedup",
]


def main():
    print("=== Benchmark de Busca de Nomes ===")
    print()

    dataset_key, dataset_path, java_dataset = choose_dataset()
    txt_files = list_txt_files(dataset_path)
    validate_java_available()

    sampled_names = sample_random_names(txt_files, NOMES_ALEATORIOS)
    expected_runs = NOMES_ALEATORIOS * REPETICOES_POR_ESTRATEGIA * len(STRATEGY_CONFIGS)

    print()
    print(f"Dataset escolhido: {dataset_key}")
    print(f"Nomes aleatorios: {NOMES_ALEATORIOS}")
    print(f"Repeticoes por estrategia: {REPETICOES_POR_ESTRATEGIA}")
    print("Configuracoes testadas:")
    for config in STRATEGY_CONFIGS:
        print(f"- {strategy_label(config)}")
    print()
    input("Pressione ENTER para iniciar o benchmark...")

    if COMPILE_BEFORE_RUN:
        compile_java()

    started_at = datetime.now().isoformat(timespec="seconds")
    run_dir = create_output_dir()
    data_dir = run_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    metadata = build_metadata(dataset_key, dataset_path, sampled_names, expected_runs, started_at)
    runs = execute_benchmark(dataset_key, dataset_path, java_dataset, sampled_names)

    paths = {
        "resultados_brutos_json": data_dir / "resultados_brutos.json",
        "resultados_brutos_csv": data_dir / "resultados_brutos.csv",
        "medias_por_nome_csv": data_dir / "medias_por_nome.csv",
        "medias_gerais_csv": data_dir / "medias_gerais.csv",
        "speedup_csv": data_dir / "speedup.csv",
        "resumo_benchmark_json": data_dir / "resumo_benchmark.json",
    }

    save_raw_json(paths["resultados_brutos_json"], metadata, runs)
    save_raw_csv(paths["resultados_brutos_csv"], runs)

    averages_by_name = calculate_group_stats(
        runs,
        ["dataset", "nome_id", "nome_sorteado", "strategy", "threads_per_file"],
        include_name=True,
    )
    save_average_by_name_csv(paths["medias_por_nome_csv"], averages_by_name)

    general_averages = calculate_group_stats(
        runs,
        ["dataset", "strategy", "threads_per_file"],
        include_name=False,
    )
    save_general_average_csv(paths["medias_gerais_csv"], general_averages)

    speedups = calculate_speedup(general_averages, machine_python())
    save_speedup_csv(paths["speedup_csv"], speedups)

    report_path = run_dir / "relatorio.html"
    generated_files = {name: str(path) for name, path in paths.items()}
    generated_files["relatorio_html"] = str(report_path)

    save_summary_json(
        paths["resumo_benchmark_json"],
        metadata,
        runs,
        general_averages,
        speedups,
        generated_files,
    )

    report_generated = False
    if GENERATE_REPORT_AFTER_BENCHMARK:
        report_generated = generate_report_safely(run_dir)

    print()
    print("Benchmark finalizado.")
    print("Dados salvos em:")
    print(data_dir)
    if report_generated:
        print()
        print("Relatorio gerado em:")
        print(report_path)


def choose_dataset():
    custom_datasets = discover_custom_datasets()

    print("Escolha o dataset:")
    print("1 - Dataset pequeno (dataset_p)")
    print("2 - Dataset grande (dataset_g)")

    for index, dataset_path in enumerate(custom_datasets, start=3):
        print(f"{index} - {dataset_path.name}")

    print()

    choice = input("Opcao: ").strip()

    if choice == "1":
        return "pequeno", DATASET_PEQUENO_PATH, "pequeno"

    if choice == "2":
        return "grande", DATASET_GRANDE_PATH, "grande"

    try:
        option = int(choice)
    except ValueError:
        option = -1

    custom_index = option - 3
    if 0 <= custom_index < len(custom_datasets):
        dataset_path = custom_datasets[custom_index]
        return dataset_path.name, dataset_path, "custom"

    raise SystemExit("Erro: opcao de dataset invalida. Escolha uma das opcoes listadas.")


def discover_custom_datasets():
    fixed_names = {DATASET_PEQUENO_PATH.name, DATASET_GRANDE_PATH.name}
    datasets = []

    for path in PROJECT_ROOT.iterdir():
        if not path.is_dir():
            continue
        if not path.name.startswith("dataset_"):
            continue
        if path.name in fixed_names:
            continue
        datasets.append(path)

    return sorted(datasets, key=lambda path: path.name.lower())


def compile_java():
    java_files = sorted(SRC_DIR.glob("*.java"))

    if not java_files:
        raise SystemExit(f"Erro: nenhum arquivo .java encontrado em {SRC_DIR}.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        completed = subprocess.run(
            [JAVAC_COMMAND, "-d", str(OUT_DIR), *[str(path) for path in java_files]],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise SystemExit(
            f"Erro: comando '{JAVAC_COMMAND}' nao encontrado. "
            "Instale/configure o JDK ou altere JAVAC_COMMAND no topo do benchmark.py."
        )

    if completed.returncode != 0:
        print("Erro: falha ao compilar o Java.", file=sys.stderr)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)
        raise SystemExit(1)


def validate_java_available():
    try:
        completed = subprocess.run(
            [JAVA_COMMAND, "-version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise SystemExit(
            f"Erro: comando '{JAVA_COMMAND}' nao encontrado. "
            "Instale/configure o Java ou altere JAVA_COMMAND no topo do benchmark.py."
        )

    if completed.returncode != 0:
        raise SystemExit(f"Erro: comando '{JAVA_COMMAND}' retornou codigo {completed.returncode}.")


def list_txt_files(dataset_path):
    if not dataset_path.exists():
        raise SystemExit(f"Erro: dataset nao encontrado: {dataset_path}")

    if not dataset_path.is_dir():
        raise SystemExit(f"Erro: caminho do dataset nao e uma pasta: {dataset_path}")

    txt_files = sorted(path for path in dataset_path.iterdir() if path.is_file() and path.suffix.lower() == ".txt")

    if not txt_files:
        raise SystemExit(f"Erro: nenhum arquivo .txt encontrado em: {dataset_path}")

    valid_names = count_valid_names(txt_files)
    if valid_names < NOMES_ALEATORIOS:
        raise SystemExit(
            f"Erro: dataset possui apenas {valid_names} nomes nao vazios. "
            f"Sao necessarios pelo menos {NOMES_ALEATORIOS}."
        )

    return txt_files


def count_valid_names(txt_files):
    count = 0
    for file_path in txt_files:
        for line in read_lines(file_path):
            if line.strip():
                count += 1
    return count


def sample_random_names(txt_files, amount):
    lines_by_file = {}
    sampled_by_name = {}
    attempts = 0
    max_attempts = max(1000, amount * len(txt_files) * 20)

    while len(sampled_by_name) < amount and attempts < max_attempts:
        attempts += 1
        file_path = random.choice(txt_files)

        if file_path not in lines_by_file:
            lines_by_file[file_path] = non_empty_lines_with_numbers(file_path)

        valid_lines = lines_by_file[file_path]
        if not valid_lines:
            continue

        line_number, name = random.choice(valid_lines)
        normalized_name = name.strip().lower()

        if normalized_name in sampled_by_name:
            continue

        sampled_by_name[normalized_name] = {
            "nome_id": len(sampled_by_name) + 1,
            "nome": name.strip(),
            "arquivo": file_path.name,
            "linha": line_number,
        }

    if len(sampled_by_name) == amount:
        return list(sampled_by_name.values())

    unique_names = {}
    for item in collect_all_non_empty_names(txt_files):
        unique_names.setdefault(item["nome"].strip().lower(), item)

    if len(unique_names) < amount:
        raise SystemExit(
            f"Erro: dataset possui apenas {len(unique_names)} nomes diferentes. "
            f"Sao necessarios {amount}."
        )

    return assign_nome_ids(random.sample(list(unique_names.values()), amount))


def collect_all_non_empty_names(txt_files):
    names = []
    for file_path in txt_files:
        for line_number, name in non_empty_lines_with_numbers(file_path):
            names.append({"nome": name.strip(), "arquivo": file_path.name, "linha": line_number})
    return names


def assign_nome_ids(sampled):
    result = []
    for index, item in enumerate(sampled, start=1):
        copied = dict(item)
        copied["nome_id"] = index
        result.append(copied)
    return result


def non_empty_lines_with_numbers(file_path):
    result = []
    for index, line in enumerate(read_lines(file_path), start=1):
        name = line.strip()
        if name:
            result.append((index, name))
    return result


def read_lines(file_path):
    try:
        with file_path.open("r", encoding="utf-8", errors="replace") as file:
            return file.readlines()
    except OSError as exc:
        raise SystemExit(f"Erro ao ler arquivo {file_path}: {exc}")


def execute_benchmark(dataset_key, dataset_path, java_dataset, sampled_names):
    runs = []
    run_id = 1

    for sampled_name in sampled_names:
        print()
        print(f"Nome {sampled_name['nome_id']}/{NOMES_ALEATORIOS}: {sampled_name['nome']}")

        for config in STRATEGY_CONFIGS:
            for repetition in range(1, REPETICOES_POR_ESTRATEGIA + 1):
                print(f"  {strategy_label(config)} - repeticao {repetition}/{REPETICOES_POR_ESTRATEGIA}")
                runs.append(run_java_benchmark(run_id, dataset_key, dataset_path, java_dataset, sampled_name, config, repetition))
                run_id += 1

    return runs


def run_java_benchmark(run_id, dataset_key, dataset_path, java_dataset, sampled_name, config, repetition):
    timestamp = datetime.now().isoformat(timespec="seconds")
    command = build_java_command(java_dataset, dataset_path, sampled_name["nome"], config)
    record = base_run_record(run_id, timestamp, dataset_key, sampled_name, config, repetition)

    try:
        completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True)
    except FileNotFoundError:
        record["errorMessage"] = f"Comando Java nao encontrado: {JAVA_COMMAND}"
        return record
    except OSError as exc:
        record["errorMessage"] = f"Erro ao executar Java: {exc}"
        return record

    if completed.returncode != 0:
        record["errorMessage"] = completed.stderr.strip() or f"Java retornou codigo {completed.returncode}."
        record["stdoutRaw"] = completed.stdout
        record["stderrRaw"] = completed.stderr
        return record

    java_result, parse_error = parse_java_json(completed.stdout)
    if parse_error:
        record["errorMessage"] = parse_error
        record["stdoutRaw"] = completed.stdout
        record["stderrRaw"] = completed.stderr
        return record

    record["success"] = True
    record["javaResult"] = java_result
    record.update(flatten_java_result(java_result))
    return record


def build_java_command(java_dataset, dataset_path, name, config):
    command = [
        JAVA_COMMAND,
        "-cp",
        str(OUT_DIR),
        JAVA_MAIN_CLASS,
        "--benchmark",
        "--dataset",
        java_dataset,
    ]

    if java_dataset == "custom":
        command.extend(["--dataset-path", str(dataset_path)])

    command.extend([
        "--strategy",
        config["strategy"],
        "--name",
        name,
    ])

    if config["strategy"] == "multiThreadPerFile":
        command.extend(["--threads-per-file", str(config["threads_per_file"])])

    command.extend(["--format", "json"])
    return command


def parse_java_json(stdout):
    try:
        return json.loads(stdout), None
    except json.JSONDecodeError as exc:
        return None, f"stdout do Java nao e JSON valido: {exc}"


def base_run_record(run_id, timestamp, dataset_key, sampled_name, config, repetition):
    return {
        "runId": run_id,
        "timestamp": timestamp,
        "machineNamePython": machine_python(),
        "dataset": dataset_key,
        "nomeId": sampled_name["nome_id"],
        "nomeSorteado": sampled_name["nome"],
        "arquivoSorteado": sampled_name["arquivo"],
        "linhaSorteada": sampled_name["linha"],
        "strategy": config["strategy"],
        "threadsPerFile": config["threads_per_file"],
        "repeticao": repetition,
        "success": False,
        "errorMessage": "",
        "javaResult": None,
        "found": None,
        "fileName": None,
        "lineNumber": None,
        "lineContent": None,
        "wallTimeMs": None,
        "wallTimeNs": None,
        "processCpuTimeSupported": None,
        "processCpuTimeMs": None,
        "cpuUsageApproxPercent": None,
        "heapUsedBeforeBytes": None,
        "heapUsedAfterBytes": None,
        "heapDeltaBytes": None,
        "availableProcessors": None,
        "javaVersion": None,
        "osName": None,
        "osArch": None,
        "machineNameJava": None,
    }


def flatten_java_result(java_result):
    return {
        "found": java_result.get("found"),
        "fileName": java_result.get("fileName"),
        "lineNumber": java_result.get("lineNumber"),
        "lineContent": java_result.get("lineContent"),
        "wallTimeMs": java_result.get("wallTimeMs"),
        "wallTimeNs": java_result.get("wallTimeNs"),
        "processCpuTimeSupported": java_result.get("processCpuTimeSupported"),
        "processCpuTimeMs": java_result.get("processCpuTimeMs"),
        "cpuUsageApproxPercent": java_result.get("cpuUsageApproxPercent"),
        "heapUsedBeforeBytes": java_result.get("heapUsedBeforeBytes"),
        "heapUsedAfterBytes": java_result.get("heapUsedAfterBytes"),
        "heapDeltaBytes": java_result.get("heapDeltaBytes"),
        "availableProcessors": java_result.get("availableProcessors"),
        "javaVersion": java_result.get("javaVersion"),
        "osName": java_result.get("osName"),
        "osArch": java_result.get("osArch"),
        "machineNameJava": java_result.get("machineName"),
    }


def create_output_dir():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_machine = safe_path_part(machine_python())
    base_dir = RESULTS_DIR / f"{timestamp}_{safe_machine}"
    output_dir = base_dir
    counter = 2

    while output_dir.exists():
        output_dir = Path(f"{base_dir}_{counter}")
        counter += 1

    output_dir.mkdir(parents=True, exist_ok=False)
    return output_dir


def save_raw_json(path, metadata, runs):
    with path.open("w", encoding="utf-8", newline="") as file:
        json.dump({"metadata": metadata, "runs": runs}, file, ensure_ascii=False, indent=2)


def save_raw_csv(path, runs):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_CSV_FIELDS)
        writer.writeheader()
        for run in runs:
            writer.writerow(raw_csv_row(run))


def raw_csv_row(run):
    return {
        "run_id": run["runId"],
        "timestamp": run["timestamp"],
        "machine_python": run["machineNamePython"],
        "machine_java": run["machineNameJava"],
        "dataset": run["dataset"],
        "nome_id": run["nomeId"],
        "nome_sorteado": run["nomeSorteado"],
        "arquivo_sorteado": run["arquivoSorteado"],
        "linha_sorteada": run["linhaSorteada"],
        "strategy": run["strategy"],
        "threads_per_file": run["threadsPerFile"],
        "repeticao": run["repeticao"],
        "success": run["success"],
        "found": run["found"],
        "file_name": run["fileName"],
        "line_number": run["lineNumber"],
        "line_content": run["lineContent"],
        "wall_time_ms": run["wallTimeMs"],
        "wall_time_ns": run["wallTimeNs"],
        "process_cpu_time_supported": run["processCpuTimeSupported"],
        "process_cpu_time_ms": run["processCpuTimeMs"],
        "cpu_usage_approx_percent": run["cpuUsageApproxPercent"],
        "heap_used_before_bytes": run["heapUsedBeforeBytes"],
        "heap_used_after_bytes": run["heapUsedAfterBytes"],
        "heap_delta_bytes": run["heapDeltaBytes"],
        "available_processors": run["availableProcessors"],
        "java_version": run["javaVersion"],
        "os_name": run["osName"],
        "os_arch": run["osArch"],
        "error_message": run["errorMessage"],
    }


def calculate_group_stats(runs, group_keys, include_name):
    groups = defaultdict(list)

    for run in runs:
        if not run["success"] or as_float(run["wallTimeMs"]) is None:
            continue
        key = tuple(run[to_record_key(field)] for field in group_keys)
        groups[key].append(run)

    results = []
    for key, grouped_runs in groups.items():
        base = {field: value for field, value in zip(group_keys, key)}
        wall_times = numeric_values(grouped_runs, "wallTimeMs")
        row = {
            "dataset": base["dataset"],
            "strategy": base["strategy"],
            "threads_per_file": base["threads_per_file"],
            "quantidade_execucoes": len(grouped_runs),
            "media_wall_time_ms": average(wall_times),
            "menor_wall_time_ms": min(wall_times) if wall_times else None,
            "maior_wall_time_ms": max(wall_times) if wall_times else None,
            "media_process_cpu_time_ms": average(numeric_values(grouped_runs, "processCpuTimeMs")),
            "media_cpu_usage_approx_percent": average(numeric_values(grouped_runs, "cpuUsageApproxPercent")),
            "media_heap_delta_bytes": average(numeric_values(grouped_runs, "heapDeltaBytes")),
        }

        if include_name:
            row["nome_id"] = base["nome_id"]
            row["nome_sorteado"] = base["nome_sorteado"]

        results.append(row)

    return sorted(
        results,
        key=lambda row: (row["dataset"], row.get("nome_id", 0), row["strategy"], row["threads_per_file"]),
    )


def save_average_by_name_csv(path, rows):
    save_csv(path, AVERAGE_FIELDS, rows)


def save_general_average_csv(path, rows):
    save_csv(path, GENERAL_AVERAGE_FIELDS, rows)


def calculate_speedup(general_averages, machine_name):
    base_times = {}
    for row in general_averages:
        if row["strategy"] == "sequencial" and int(row["threads_per_file"]) == 0:
            base_times[row["dataset"]] = row["media_wall_time_ms"]

    speedups = []
    for row in general_averages:
        base_time = base_times.get(row["dataset"])
        average_time = row["media_wall_time_ms"]
        speedup = None

        if base_time is not None and average_time not in (None, 0):
            speedup = base_time / average_time

        speedups.append({
            "machine_python": machine_name,
            "dataset": row["dataset"],
            "strategy": row["strategy"],
            "threads_per_file": row["threads_per_file"],
            "media_wall_time_ms": average_time,
            "tempo_base_sequencial_ms": base_time,
            "speedup": speedup,
        })

    return sorted(speedups, key=lambda row: (row["dataset"], row["strategy"], row["threads_per_file"]))


def save_speedup_csv(path, rows):
    save_csv(path, SPEEDUP_FIELDS, rows)


def save_summary_json(path, metadata, runs, general_averages, speedups, generated_files):
    successful_runs = [run for run in runs if run["success"]]
    failed_runs = [run for run in runs if not run["success"]]
    summary = {
        "machinePython": machine_python(),
        "platform": platform.platform(),
        "dataset": metadata["dataset"],
        "startedAt": metadata["startedAt"],
        "finishedAt": datetime.now().isoformat(timespec="seconds"),
        "totalExecucoesEsperadas": metadata["expectedRuns"],
        "totalExecucoesComSucesso": len(successful_runs),
        "totalExecucoesComErro": len(failed_runs),
        "melhorEstrategiaPorTempoMedio": find_best_strategy(general_averages),
        "maiorSpeedup": find_best_speedup(speedups),
        "arquivosGerados": generated_files,
    }

    with path.open("w", encoding="utf-8", newline="") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)


def generate_report_safely(run_dir):
    try:
        from generate_report import generate_report

        report_path = generate_report(run_dir)
        return report_path.exists()
    except Exception as exc:
        print()
        print(f"Aviso: nao foi possivel gerar o relatorio HTML: {exc}", file=sys.stderr)
        print("Os arquivos de dados foram preservados.", file=sys.stderr)
        return False


def find_best_strategy(general_averages):
    candidates = [row for row in general_averages if row["media_wall_time_ms"] is not None]
    if not candidates:
        return None
    best = min(candidates, key=lambda row: row["media_wall_time_ms"])
    return {
        "strategy": best["strategy"],
        "threadsPerFile": best["threads_per_file"],
        "mediaWallTimeMs": best["media_wall_time_ms"],
    }


def find_best_speedup(speedups):
    candidates = [row for row in speedups if row["speedup"] is not None]
    if not candidates:
        return None
    best = max(candidates, key=lambda row: row["speedup"])
    return {
        "strategy": best["strategy"],
        "threadsPerFile": best["threads_per_file"],
        "speedup": best["speedup"],
    }


def save_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_csv_value(row.get(field)) for field in fields})


def build_metadata(dataset_key, dataset_path, sampled_names, expected_runs, started_at):
    return {
        "startedAt": started_at,
        "machinePython": machine_python(),
        "platform": platform.platform(),
        "dataset": dataset_key,
        "datasetPath": str(dataset_path),
        "nomesAleatorios": NOMES_ALEATORIOS,
        "repeticoesPorEstrategia": REPETICOES_POR_ESTRATEGIA,
        "multiThreadValues": MULTI_THREAD_VALUES,
        "strategyConfigs": STRATEGY_CONFIGS,
        "expectedRuns": expected_runs,
        "sampledNames": sampled_names,
        "compileBeforeRun": COMPILE_BEFORE_RUN,
        "generateReportAfterBenchmark": GENERATE_REPORT_AFTER_BENCHMARK,
        "javaCommand": JAVA_COMMAND,
        "javacCommand": JAVAC_COMMAND,
        "javaMainClass": JAVA_MAIN_CLASS,
        "srcDir": str(SRC_DIR),
        "outDir": str(OUT_DIR),
    }


def strategy_label(config):
    if config["strategy"] == "multiThreadPerFile":
        return f"multiThreadPerFile N={config['threads_per_file']}"
    return config["strategy"]


def numeric_values(runs, field):
    values = []
    for run in runs:
        value = as_float(run.get(field))
        if value is not None:
            values.append(value)
    return values


def average(values):
    if not values:
        return None
    return sum(values) / len(values)


def as_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_record_key(field):
    mapping = {
        "dataset": "dataset",
        "nome_id": "nomeId",
        "nome_sorteado": "nomeSorteado",
        "strategy": "strategy",
        "threads_per_file": "threadsPerFile",
    }
    return mapping[field]


def format_csv_value(value):
    if value is None:
        return ""
    return value


def machine_python():
    return socket.gethostname() or "unknown"


def safe_path_part(value):
    safe_chars = []
    for char in value:
        if char.isalnum() or char in ("-", "_"):
            safe_chars.append(char)
        else:
            safe_chars.append("_")
    return "".join(safe_chars) or "unknown"


if __name__ == "__main__":
    main()
