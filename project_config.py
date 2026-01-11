import os
import re
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import snapshot_download

if os.getenv("HF_HUB_ENABLE_HF_TRANSFER") == "1":
    try:
        import hf_transfer  # noqa: F401
    except Exception:
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

try:
    from django.core.management.utils import get_random_secret_key
except Exception:
    get_random_secret_key = None


DEFAULT_REPO_ID = "PauloHPCerqueira/distillbert-requirements-classifier-mtl"
DEFAULT_SUBFOLDER = "distilbert"
DEFAULT_DEST = Path("requirements_classifier") / "distilbert"


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _is_nonempty_dir(p: Path) -> bool:
    return p.exists() and p.is_dir() and any(p.iterdir())


def _generate_secret_key() -> str:
    if get_random_secret_key:
        return get_random_secret_key()
    import secrets
    return secrets.token_urlsafe(50)


def _set_env_var(env_path: Path, key: str, value: str, force: bool = False) -> None:
    env_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*)\s*$")
    found = False
    new_lines: list[str] = []

    for line in lines:
        m = pattern.match(line)
        if not m:
            new_lines.append(line)
            continue

        found = True
        current = m.group(1).strip()
        unquoted = current.strip().strip('"').strip("'")

        if (unquoted and not force):
            new_lines.append(line)
        else:
            new_lines.append(f'{key}="{value}"')

    if not found:
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append(f'{key}="{value}"')

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main() -> int:
    repo_id = os.getenv("HF_REPO_ID", DEFAULT_REPO_ID)
    subfolder = os.getenv("HF_SUBFOLDER", DEFAULT_SUBFOLDER)

    project_root = _project_root()
    dest_dir = project_root / os.getenv("MODEL_DEST", str(DEFAULT_DEST))

    if _is_nonempty_dir(dest_dir):
        print(f"[OK] Modelo já existe em: {dest_dir}")
    else:
        print(f"[INFO] Baixando do Hugging Face: {repo_id} (subpasta: {subfolder})")
        dest_dir.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            snapshot_download(
                repo_id=repo_id,
                repo_type="model",
                allow_patterns=[f"{subfolder}/*"],
                local_dir=str(tmp_path),
                local_dir_use_symlinks=False,
            )

            src_dir = tmp_path / subfolder
            if not src_dir.exists():
                print(f"[ERRO] Não achei a pasta '{subfolder}' dentro do download.")
                return 2

            if dest_dir.exists():
                shutil.rmtree(dest_dir)

            shutil.copytree(src_dir, dest_dir)
            print(f"[OK] Modelo copiado para: {dest_dir}")

    env_path = project_root / ".env"
    force_secret = os.getenv("FORCE_SECRET_KEY", "0") == "1"
    secret = _generate_secret_key()
    _set_env_var(env_path, "SECRET_KEY", secret, force=force_secret)
    print(f"[OK] SECRET_KEY garantida em: {env_path} (force={force_secret})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())