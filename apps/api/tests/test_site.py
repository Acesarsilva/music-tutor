from music_tutor.site import aulas_prontas, gerar_site

from conftest import RAIZ


def test_site_tem_indice_e_todas_as_aulas(tmp_path):
    saida = tmp_path / "dist"
    total = gerar_site(saida)
    prontas = aulas_prontas()
    assert total == len(prontas) == len(list((RAIZ / "aulas-exemplo").glob("*.json")))

    indice = (saida / "index.html").read_text(encoding="utf-8")
    for aula, nome in prontas:
        assert f'href="aulas/{nome}"' in indice
        pagina = (saida / "aulas" / nome).read_text(encoding="utf-8")
        assert 'class="voltar" href="../"' in pagina
        assert aula.titulo in pagina


def test_aulas_seguem_a_ordem_do_curriculo():
    codigos = [a.codigo for a, _ in aulas_prontas()]
    prefixos = ["I", "M", "A", "VI", "VM", "VA"]
    assert codigos == sorted(codigos, key=lambda c: (prefixos.index(c.rstrip("0123456789")), int(c[-2:])))
