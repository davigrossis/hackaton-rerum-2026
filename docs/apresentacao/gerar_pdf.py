"""Gera o PDF da apresentação oficial do Hackathon UFJF 2026 a partir do index.html.

Utiliza o Microsoft Edge headless (nativo no Windows) sem instalar dependências extras.
"""

import subprocess
import sys
from pathlib import Path

PASTA_ATUAL = Path(__file__).resolve().parent
ARQUIVO_HTML = PASTA_ATUAL / "index.html"
ARQUIVO_PDF = PASTA_ATUAL / "apresentacao.pdf"

EDGE_WINDOWS = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
EDGE_WINDOWS_64 = Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")


def encontrar_navegador() -> str:
    if EDGE_WINDOWS.exists():
        return str(EDGE_WINDOWS)
    if EDGE_WINDOWS_64.exists():
        return str(EDGE_WINDOWS_64)
    # Tenta edge ou chrome no PATH
    for cmd in ("msedge", "google-chrome", "chromium", "chrome"):
        try:
            res = subprocess.run(
                ["where" if sys.platform == "win32" else "which", cmd],
                check=False,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip().split("\n")[0].strip()
        except OSError:
            continue
    raise FileNotFoundError("Nenhum navegador Chromium encontrado para conversão.")


def main() -> None:
    navegador = encontrar_navegador()
    print(f"Gerando PDF usando: {navegador}")
    cmd = [
        navegador,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={ARQUIVO_PDF}",
        "--no-pdf-header-footer",
        str(ARQUIVO_HTML),
    ]
    subprocess.run(cmd, check=True)
    if ARQUIVO_PDF.exists() and ARQUIVO_PDF.stat().st_size > 0:
        print(
            f"Sucesso! PDF gerado em: {ARQUIVO_PDF} ({ARQUIVO_PDF.stat().st_size:,} bytes)"
        )
    else:
        sys.exit("Falha na geração do arquivo PDF.")


if __name__ == "__main__":
    main()
