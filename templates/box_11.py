# templates/box_11.py
from typing import Callable, Dict
from models import VisitaTecnica, ProjetoResposta, Peca

def projeto_box_11(visita: VisitaTecnica) -> ProjetoResposta:
    # === CONFIGURAÇÕES DO SEU ENG. DE VIDRAÇARIA ===
    folga_lateral = 0.03            # 3 cm TOTAL
    folga_altura = 0.05             # 5 cm TOTAL
    sobreposicao_folhas = 0.05      # 5 cm de sobreposição

    largura_vao = visita.largura
    altura_vao = visita.altura

    # Altura final do vidro
    altura_peca = round(altura_vao - folga_altura, 3)

    # Larguras
    largura_fixo = round((largura_vao - folga_lateral - sobreposicao_folhas) / 2, 3)
    largura_porta = round(largura_fixo + sobreposicao_folhas, 3)

    pecas = [
        Peca(
            codigo="P01",
            tipo="painel",
            posicao="fixo",
            largura=largura_fixo,
            altura=altura_peca,
        ),
        Peca(
            codigo="P02",
            tipo="porta",
            posicao="correr",
            largura=largura_porta,
            altura=altura_peca,
        ),
    ]

    return ProjetoResposta(
        templateId="BOX_11_RETO",
        descricaoModelo="Modelo BOX-11 (reto, 1 folha + 1 fixo)",
        pecas=pecas,
    )

# dicionário de templates
TEMPLATES: Dict[str, Callable[[VisitaTecnica], ProjetoResposta]] = {
    "BOX_11_RETO": projeto_box_11,
}
