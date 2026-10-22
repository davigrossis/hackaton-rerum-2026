"""Testes de fumaça: base de conhecimento, app e fonte única das regras (AGENTS.md)."""

from pathlib import Path

import yaml
from streamlit.testing.v1 import AppTest

from interface.estilo import NOME_APP

RAIZ = Path(__file__).resolve().parent.parent


def test_base_de_conhecimento_carrega():
    base = yaml.safe_load(
        (RAIZ / "conhecimento" / "regras.yaml").read_text(encoding="utf-8")
    )
    assert base["versao"]
    assert isinstance(base["regras"], list)


def test_app_abre_sem_erro():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert any(NOME_APP in m.value for m in app.markdown)


def test_claude_md_so_importa_agents_md():
    # Fonte única: Claude, Gemini e GPT precisam ler as mesmas regras.
    claude_md = (RAIZ / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude_md.strip() == "@AGENTS.md"
