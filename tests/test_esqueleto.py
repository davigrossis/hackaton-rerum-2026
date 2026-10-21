"""Testes de fumaça: a base de conhecimento carrega e o app abre sem erro."""

from pathlib import Path

import yaml
from streamlit.testing.v1 import AppTest

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
    assert app.title[0].value == "EconoLeite"
