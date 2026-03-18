from pathlib import Path
import re
import os
import sys


def load_env_file(path: Path):
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        env[key] = value
    return env


def resolve_interpolations(value: str, base_env: dict):
    if value is None:
        return None

    def replace(match):
        var = match.group(1)
        default = match.group(2)
        if var in base_env:
            return base_env[var]
        if default is not None:
            return default
        return ""

    # ${VAR:-default} or ${VAR}
    value = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)[:-]?([^}]*)\}", replace, value)
    # $VAR
    value = re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", lambda m: base_env.get(m.group(1), ""), value)
    return value


def parse_compose_env(compose_path: Path, root_env: dict):
    compose_envs = {}
    if not compose_path.exists():
        return compose_envs

    try:
        import yaml
    except ImportError:
        print("ERRO: PyYAML não está instalado. Instale via 'pip install pyyaml' e rode novamente.")
        return compose_envs

    raw = compose_path.read_text(encoding="utf-8")
    # Interpolate env vars already known from root .env for YAML parser
    interpolated = raw
    for k, v in root_env.items():
        interpolated = interpolated.replace(f"${{{k}}}", v)
        interpolated = interpolated.replace(f"${k}", v)

    data = yaml.safe_load(interpolated)
    if not data:
        return compose_envs

    services = data.get("services", {})
    for service_name, service_cfg in services.items():
        env_map = {}
        if not isinstance(service_cfg, dict):
            continue
        env_section = service_cfg.get("environment")
        if isinstance(env_section, dict):
            env_map.update({k: str(v) for k, v in env_section.items() if v is not None})
        elif isinstance(env_section, list):
            for item in env_section:
                if isinstance(item, str) and "=" in item:
                    k, v = item.split("=", 1)
                    env_map[k] = v
        env_files = service_cfg.get("env_file")
        if env_files:
            if isinstance(env_files, str):
                env_files = [env_files]
            for env_file in env_files:
                env_file_path = (compose_path.parent / env_file).resolve()
                env_map.update(load_env_file(env_file_path))
        compose_envs[service_name] = env_map

    return compose_envs


def collect_service_envs(root_env: dict):
    services = {}
    # Airflow
    airflow_compose = Path("airflow/docker-compose.yml")
    services["airflow"] = {}
    airflow_envs = parse_compose_env(airflow_compose, root_env)
    for s, kv in airflow_envs.items():
        services["airflow"].update(kv)

    # MinIO
    minio_compose = Path("minio/docker-compose.yml")
    services["minio"] = {}
    minio_envs = parse_compose_env(minio_compose, root_env)
    for s, kv in minio_envs.items():
        services["minio"].update(kv)

    # Trino
    trino_compose = Path("trino/docker-compose.yml")
    services["trino"] = {}
    trino_envs = parse_compose_env(trino_compose, root_env)
    for s, kv in trino_envs.items():
        services["trino"].update(kv)

    return services


def report(root_env: dict, services_env: dict):
    print("Verificando variáveis em .env contra Trino, MinIO e Airflow...\n")
    if not root_env:
        print("Nenhuma variável encontrada no .env da raiz.")
        return

    any_found = False
    for service_name, env_vars in services_env.items():
        found = []
        different = []
        for key, root_val in root_env.items():
            if key in env_vars:
                any_found = True
                svc_val = resolve_interpolations(str(env_vars[key]), root_env)
                found.append(key)
                if root_val != svc_val:
                    different.append((key, root_val, svc_val))

        print(f"[{service_name.upper()}] Variáveis encontradas: {len(found)}")
        if found:
            print("  chaves:")
            for k in found:
                print(f"    - {k}")
        else:
            print("  nenhuma variável de .env foi encontrada nas definições desse serviço.")

        if different:
            print("  com valores diferentes:")
            for key, root_val, svc_val in different:
                print(f"    - {key}: .env='{root_val}'  vs serviço='{svc_val}'")
        else:
            print("  sem diferenças de valor para as variáveis encontradas.")
        print("")

    if not any_found:
        print("Nenhuma das variáveis do .env da raiz existe nas variáveis de ambiente definidas nos compose de trino, minio ou airflow.")


def main():
    root_env_path = Path(".env")
    if not root_env_path.exists():
        print("Arquivo .env não encontrado na raiz do projeto.")
        return 1

    root_env = load_env_file(root_env_path)
    services_env = collect_service_envs(root_env)
    report(root_env, services_env)
    return 0


if __name__ == "__main__":
    sys.exit(main())
