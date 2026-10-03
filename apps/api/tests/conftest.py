from pathlib import Path

import pytest

from music_tutor.esquema import Aula

RAIZ = Path(__file__).resolve().parents[3]


@pytest.fixture
def aula_piloto() -> Aula:
    return Aula.model_validate_json((RAIZ / "aulas-exemplo" / "I08-intervalos-simples.json").read_text(encoding="utf-8"))
