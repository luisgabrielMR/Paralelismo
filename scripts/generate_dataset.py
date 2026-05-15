import argparse
import json
import math
import platform
import random
import shutil
import socket
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FIRST_NAMES = [
    "Ana", "Bruno", "Carla", "Daniel", "Eduarda", "Felipe", "Gabriela", "Henrique", "Isabela", "Joao",
    "Karina", "Lucas", "Mariana", "Nicolas", "Olivia", "Paulo", "Quiteria", "Rafael", "Sofia", "Tiago",
    "Ursula", "Victor", "Wesley", "Xavier", "Yasmin", "Zeca", "Amanda", "Bianca", "Caio", "Diana",
    "Enzo", "Fernanda", "Gustavo", "Helena", "Igor", "Julia", "Kevin", "Larissa", "Mateus", "Natalia",
    "Otavio", "Priscila", "Raquel", "Samuel", "Tatiane", "Valeria", "William", "Alice", "Bernardo", "Cecilia",
    "Diego", "Emanuel", "Flavia", "Giovanna", "Heitor", "Ingrid", "Jorge", "Laura", "Marcelo", "Nicole",
    "Oscar", "Patricia", "Renata", "Sandro", "Talita", "Vinicius", "Adriana", "Breno", "Camila", "Douglas",
    "Estela", "Fabio", "Gilberto", "Heloisa", "Ivana", "Jonas", "Katia", "Leandro", "Monica", "Norberto",
    "Odete", "Pedro", "Rita", "Sergio", "Tania", "Vera", "Andre", "Beatriz", "Claudio", "Denise",
    "Elaine", "Fernando", "Gloria", "Hugo", "Irene", "Jean", "Livia", "Murilo", "Noemi", "Patricio",
    "Roberta", "Silvio", "Teresa", "Valdemar", "Aline", "Cristina", "Edson", "Francisco", "Graziella", "Luana",
]

LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Pereira", "Lima", "Carvalho", "Ferreira", "Rodrigues", "Almeida",
    "Costa", "Gomes", "Martins", "Araujo", "Barbosa", "Ribeiro", "Alves", "Monteiro", "Mendes", "Cardoso",
    "Teixeira", "Correia", "Moreira", "Nunes", "Vieira", "Cavalcanti", "Dias", "Castro", "Campos", "Moura",
    "Freitas", "Pinto", "Rocha", "Machado", "Fonseca", "Andrade", "Batista", "Neves", "Moraes", "Cunha",
    "Reis", "Sales", "Medeiros", "Farias", "Duarte", "Tavares", "Melo", "Borges", "Ramos", "Pires",
    "Assis", "Macedo", "Peixoto", "Queiroz", "Matos", "Amaral", "Coelho", "Figueiredo", "Xavier", "Aguiar",
    "Rezende", "Brito", "Guimaraes", "Antunes", "Valente", "Siqueira", "Prado", "Lopes", "Cordeiro", "Menezes",
    "Vasconcelos", "Miranda", "Azevedo", "Bueno", "Camargo", "Domingues", "Esteves", "Furtado", "Garcia", "Leite",
    "Marques", "Novaes", "Ortega", "Porto", "Quintana", "Rangel", "Seixas", "Toledo", "Uchoa", "Vargas",
    "Werneck", "Zanetti", "Abreu", "Bandeira", "Chaves", "Dantas", "Escobar", "Franco", "Galvao", "Henriques",
    "Jardim", "Klein", "Lacerda", "Magalhaes", "Nascimento", "Otero", "Passos", "Romero", "Saraiva", "Torres",
]

FORMATS = [
    {
        "type": "FIRST_LAST",
        "description": "Nome + Sobrenome",
        "parts": ("F", "L"),
        "max_total": 10_000,
    },
    {
        "type": "FIRST_LAST_LAST",
        "description": "Nome + Sobrenome + Sobrenome",
        "parts": ("F", "L", "L"),
        "max_total": 1_000_000,
    },
    {
        "type": "FIRST_FIRST_LAST_LAST",
        "description": "Nome + Nome + Sobrenome + Sobrenome",
        "parts": ("F", "F", "L", "L"),
        "max_total": 100_000_000,
    },
    {
        "type": "FIRST_FIRST_LAST_LAST_LAST",
        "description": "Nome + Nome + Sobrenome + Sobrenome + Sobrenome",
        "parts": ("F", "F", "L", "L", "L"),
        "max_total": 10_000_000_000,
    },
]


def main():
    args = parse_args()
    config = validate_args(args)
    safe_prepare_output_dir(config["output_dir"], config["force"])

    print(f"Total solicitado: {config['total_names']} nomes")
    print(f"Formato escolhido: {config['format']['description']}")
    print(f"Capacidade do formato: {config['format_capacity']} nomes")
    print("Gerando dataset...")

    indices = generate_indices(
        config["total_names"],
        config["format_capacity"],
        shuffle=not config["no_shuffle"],
        seed=config["seed"],
    )
    write_dataset(
        config["output_dir"],
        indices,
        config["files"],
        config["names_per_file"],
        config["format"],
    )
    manifest_path = write_manifest(config["output_dir"], build_manifest(config))

    print("Dataset gerado com sucesso:")
    print(f"Pasta: {display_path(config['output_dir'])}")
    print(f"Arquivos: {config['files']}")
    print(f"Nomes por arquivo: {config['names_per_file']}")
    print(f"Total de nomes: {config['total_names']}")
    print(f"Formato usado: {config['format']['description']}")
    print(f"Capacidade do formato: {config['format_capacity']}")
    print(f"Manifesto: {display_path(manifest_path)}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gera datasets sinteticos de nomes completos unicos para benchmark Java."
    )
    parser.add_argument("--output", required=True, help="Pasta de saida do dataset.")
    parser.add_argument("--files", required=True, type=int, help="Quantidade de arquivos .txt.")
    parser.add_argument("--names-per-file", required=True, type=int, help="Quantidade de nomes por arquivo.")
    parser.add_argument("--seed", type=int, default=None, help="Seed opcional para embaralhamento reprodutivel.")
    parser.add_argument("--force", action="store_true", help="Apaga e recria a pasta de saida se ela ja existir.")
    parser.add_argument("--no-shuffle", action="store_true", help="Gera nomes em ordem deterministica.")
    return parser.parse_args()


def validate_args(args):
    if args.files <= 0:
        raise SystemExit("Erro: --files deve ser maior que zero.")

    if args.names_per_file <= 0:
        raise SystemExit("Erro: --names-per-file deve ser maior que zero.")

    total_names = args.files * args.names_per_file
    selected_format = select_name_format(total_names)
    format_capacity = calculate_format_capacity(selected_format)
    output_dir = resolve_output_path(args.output)

    return {
        "output_arg": args.output,
        "output_dir": output_dir,
        "files": args.files,
        "names_per_file": args.names_per_file,
        "total_names": total_names,
        "format": selected_format,
        "format_capacity": format_capacity,
        "seed": args.seed,
        "force": args.force,
        "no_shuffle": args.no_shuffle,
    }


def select_name_format(total_names):
    for name_format in FORMATS:
        if total_names <= name_format["max_total"] and total_names <= calculate_format_capacity(name_format):
            return name_format

    max_capacity = min(FORMATS[-1]["max_total"], calculate_format_capacity(FORMATS[-1]))
    raise SystemExit(
        "Erro: o volume solicitado excede a capacidade configurada. "
        f"Total solicitado: {total_names}. Capacidade maxima: {max_capacity}."
    )


def calculate_format_capacity(name_format):
    capacity = 1
    for part in name_format["parts"]:
        capacity *= len(FIRST_NAMES) if part == "F" else len(LAST_NAMES)
    return capacity


def build_name_from_index(index, name_format):
    parts = []
    divisors = [len(FIRST_NAMES) if part == "F" else len(LAST_NAMES) for part in name_format["parts"]]
    positions = []

    for base in reversed(divisors):
        positions.append(index % base)
        index //= base

    positions.reverse()

    for part, position in zip(name_format["parts"], positions):
        if part == "F":
            parts.append(FIRST_NAMES[position])
        else:
            parts.append(LAST_NAMES[position])

    return " ".join(parts)


def generate_indices(total_names, capacity, shuffle, seed):
    if not shuffle:
        for index in range(total_names):
            yield index
        return

    random_generator = random.Random(seed)
    offset = random_generator.randrange(capacity)
    step = random_generator.randrange(1, capacity)

    while math.gcd(step, capacity) != 1:
        step = random_generator.randrange(1, capacity)

    for ordinal in range(total_names):
        yield (offset + ordinal * step) % capacity


def safe_prepare_output_dir(path, force):
    assert_safe_output_path(path)

    if path.exists():
        if not force:
            raise SystemExit(f"Erro: a pasta de saida ja existe: {display_path(path)}. Use --force para sobrescrever.")

        shutil.rmtree(path)

    path.mkdir(parents=True, exist_ok=False)


def assert_safe_output_path(path):
    resolved = path.resolve()
    raw_text = str(path).strip()

    if raw_text in (".", ".."):
        raise SystemExit("Erro: pasta de saida critica nao permitida.")

    if resolved.anchor and resolved == Path(resolved.anchor):
        raise SystemExit("Erro: nao e permitido usar a raiz do disco como pasta de saida.")

    critical_paths = {
        PROJECT_ROOT.resolve(),
        (PROJECT_ROOT / "src").resolve(),
        (PROJECT_ROOT / "scripts").resolve(),
        (PROJECT_ROOT / "results").resolve(),
        (PROJECT_ROOT / "out").resolve(),
        (PROJECT_ROOT / "dataset_p").resolve(),
        (PROJECT_ROOT / "dataset_g").resolve(),
    }

    if resolved in critical_paths:
        raise SystemExit(f"Erro: pasta de saida protegida nao permitida: {display_path(path)}")


def write_dataset(output_dir, indices, files, names_per_file, name_format):
    for file_number in range(1, files + 1):
        file_path = output_dir / f"arq_{file_number}.txt"
        print(f"Escrevendo {file_path.name}...")

        with file_path.open("w", encoding="utf-8", newline="\n") as file:
            for _ in range(names_per_file):
                name_index = next(indices)
                file.write(build_name_from_index(name_index, name_format))
                file.write("\n")


def write_manifest(output_dir, metadata):
    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8", newline="") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)
    return manifest_path


def build_manifest(config):
    return {
        "output": display_path(config["output_dir"]),
        "files": config["files"],
        "namesPerFile": config["names_per_file"],
        "totalNames": config["total_names"],
        "uniqueFullNames": True,
        "firstNamesCount": len(FIRST_NAMES),
        "lastNamesCount": len(LAST_NAMES),
        "selectedFormat": config["format"]["type"],
        "formatDescription": config["format"]["description"],
        "formatCapacity": config["format_capacity"],
        "allowRepeatedLastNames": True,
        "allowRepeatedFirstNames": True,
        "seed": config["seed"],
        "shuffle": not config["no_shuffle"],
        "encoding": "UTF-8",
        "filePattern": "arq_N.txt",
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "pythonVersion": platform.python_version(),
        "osName": platform.system(),
        "osVersion": platform.version(),
        "machineName": socket.gethostname() or "unknown",
    }


def resolve_output_path(output):
    path = Path(output)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def display_path(path):
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    main()
