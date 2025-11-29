from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional, Tuple
import math

app = FastAPI(
    title="IA Projetos Vidraçaria",
    version="0.2.0",
)

# ───────────────────────── CORS ─────────────────────────
origins = [
    "http://127.0.0.1:63342",
    "http://localhost:63342",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────── MODELOS Pydantic ──────────────────────
class Cliente(BaseModel):
    nome: str
    cidade: Optional[str] = None


class VisitaTecnica(BaseModel):
    tipoServico: str
    ambiente: str
    largura: float
    altura: float
    temCanto: bool = False
    numPortas: Optional[int] = None
    numFixos: Optional[int] = None
    tipoVidro: str
    espessura: int
    perfil: str
    desnivel: float = 0.0  # em centímetros
    observacoes: Optional[str] = None
    cliente: Cliente


class Peca(BaseModel):
    codigo: str
    tipo: Literal["fixo", "porta", "folha", "painel"]
    posicao: str
    largura: float
    altura: float


class ProjetoResposta(BaseModel):
    templateId: str
    descricaoModelo: str
    pecas: List[Peca]
    vidro: str
    perfil: str
    laudoTecnico: str
    alertas: List[str]


# Só para PDF da visita (sem peças)
class LaudoResposta(BaseModel):
    templateId: str
    laudoTecnico: str
    alertas: List[str]


# ────────────────────── LÓGICA DE NEGÓCIO ──────────────────────
def escolher_template(visita: VisitaTecnica) -> str:
    ts = visita.tipoServico.lower()

    if "box" in ts:
        if visita.temCanto:
            return "box_canto"
        if visita.numPortas == 2 and visita.numFixos == 2:
            return "box_11"
        if visita.numPortas == 1 and visita.numFixos == 1:
            return "box_13"
        return "box_06"

    if "sacada" in ts:
        return "sacada_L" if visita.temCanto else "sacada_reta"

    if "espelho" in ts:
        return "espelho_ret"

    # qualquer outro tipo → genérico
    return "generico"


# ───── BOXES ─────
def gerar_pecas_box_11(visita: VisitaTecnica) -> List[Peca]:
    """BOX-11: 2 portas de correr + 2 fixos laterais."""
    folga_lateral = 0.03
    folga_altura = 0.05
    sobreposicao_folhas = 0.05

    largura_vao = visita.largura
    altura_vao = visita.altura

    altura_peca = round(altura_vao - folga_altura, 3)
    largura_fixo = round((largura_vao - folga_lateral - sobreposicao_folhas) / 2, 3)
    largura_porta = round(largura_fixo + sobreposicao_folhas, 3)

    pecas: List[Peca] = []

    pecas.append(Peca(
        codigo="F01",
        tipo="fixo",
        posicao="fixo esquerdo",
        largura=largura_fixo,
        altura=altura_peca,
    ))
    pecas.append(Peca(
        codigo="P01",
        tipo="porta",
        posicao="porta correr 1",
        largura=largura_porta,
        altura=altura_peca,
    ))
    pecas.append(Peca(
        codigo="P02",
        tipo="porta",
        posicao="porta correr 2",
        largura=largura_porta,
        altura=altura_peca,
    ))
    pecas.append(Peca(
        codigo="F02",
        tipo="fixo",
        posicao="fixo direito",
        largura=largura_fixo,
        altura=altura_peca,
    ))
    return pecas


def gerar_pecas_box_06(visita: VisitaTecnica) -> List[Peca]:
    """BOX-06: 1 porta de correr + 1 fixo (modelo comum)."""
    folga_lateral = 0.03
    folga_altura = 0.05
    sobreposicao = 0.05

    largura_vao = visita.largura
    altura_peca = round(visita.altura - folga_altura, 3)

    largura_fixo = round((largura_vao - folga_lateral - sobreposicao) / 2, 3)
    largura_porta = round(largura_fixo + sobreposicao, 3)

    return [
        Peca(
            codigo="F01",
            tipo="fixo",
            posicao="fixo lateral",
            largura=largura_fixo,
            altura=altura_peca,
        ),
        Peca(
            codigo="P01",
            tipo="porta",
            posicao="porta correr",
            largura=largura_porta,
            altura=altura_peca,
        ),
    ]


def gerar_pecas_box_13(visita: VisitaTecnica) -> List[Peca]:
    """BOX-13: porta pivotante + fixo lateral."""
    folga_lateral = 0.03
    folga_altura = 0.05
    largura_vao = visita.largura
    altura_peca = round(visita.altura - folga_altura, 3)

    largura_porta = round(largura_vao * 0.4, 3)
    largura_fixo = round(largura_vao - folga_lateral - largura_porta, 3)

    return [
        Peca(
            codigo="P01",
            tipo="porta",
            posicao="porta pivotante",
            largura=largura_porta,
            altura=altura_peca,
        ),
        Peca(
            codigo="F01",
            tipo="fixo",
            posicao="fixo lateral",
            largura=largura_fixo,
            altura=altura_peca,
        ),
    ]


def gerar_pecas_box_canto(visita: VisitaTecnica) -> List[Peca]:
    """BOX de canto 90º: divide vão em 2 lados iguais, cada um com porta + fixo."""
    folga_altura = 0.05
    altura_peca = round(visita.altura - folga_altura, 3)

    largura_total = visita.largura
    largura_face = round(largura_total / 2, 3)

    largura_fixo = round(largura_face * 0.4, 3)
    largura_porta = round(largura_face - largura_fixo, 3)

    pecas: List[Peca] = []

    # face 1
    pecas.append(Peca(
        codigo="F01",
        tipo="fixo",
        posicao="fixo face 1",
        largura=largura_fixo,
        altura=altura_peca,
    ))
    pecas.append(Peca(
        codigo="P01",
        tipo="porta",
        posicao="porta correr face 1",
        largura=largura_porta,
        altura=altura_peca,
    ))

    # face 2
    pecas.append(Peca(
        codigo="F02",
        tipo="fixo",
        posicao="fixo face 2",
        largura=largura_fixo,
        altura=altura_peca,
    ))
    pecas.append(Peca(
        codigo="P02",
        tipo="porta",
        posicao="porta correr face 2",
        largura=largura_porta,
        altura=altura_peca,
    ))

    return pecas


# ───── SACADAS ─────
def gerar_pecas_sacada_reta(visita: VisitaTecnica) -> List[Peca]:
    """Sacada reta: inventa módulos de até 1.50m."""
    largura_vao = visita.largura
    altura_peca = round(visita.altura, 3)

    modulo_max = 1.5
    n_modulos = max(1, math.ceil(largura_vao / modulo_max))
    largura_modulo = round(largura_vao / n_modulos, 3)

    pecas: List[Peca] = []
    for i in range(n_modulos):
        pecas.append(Peca(
            codigo=f"S{i+1:02d}",
            tipo="painel",
            posicao=f"painel {i+1}",
            largura=largura_modulo,
            altura=altura_peca,
        ))
    return pecas


def gerar_pecas_sacada_L(visita: VisitaTecnica) -> List[Peca]:
    """Sacada em L: divide vão em 2 faces iguais, cada uma com módulos."""
    largura_total = visita.largura
    altura_peca = round(visita.altura, 3)

    face = round(largura_total / 2, 3)
    modulo_max = 1.5

    n_mod_face = max(1, math.ceil(face / modulo_max))
    largura_modulo = round(face / n_mod_face, 3)

    pecas: List[Peca] = []
    # face 1
    for i in range(n_mod_face):
        pecas.append(Peca(
            codigo=f"L1_{i+1:02d}",
            tipo="painel",
            posicao=f"face 1 painel {i+1}",
            largura=largura_modulo,
            altura=altura_peca,
        ))
    # face 2
    for i in range(n_mod_face):
        pecas.append(Peca(
            codigo=f"L2_{i+1:02d}",
            tipo="painel",
            posicao=f"face 2 painel {i+1}",
            largura=largura_modulo,
            altura=altura_peca,
        ))
    return pecas


# ───── ESPELHO ─────
def gerar_pecas_espelho_ret(visita: VisitaTecnica) -> List[Peca]:
    """Espelho retangular simples."""
    return [
        Peca(
            codigo="E01",
            tipo="painel",
            posicao="espelho",
            largura=visita.largura,
            altura=visita.altura,
        )
    ]


# ───── GENÉRICO ─────
def gerar_pecas_generico(visita: VisitaTecnica) -> List[Peca]:
    """
    Caso não reconheça o tipo, inventa um projeto fatiando o vão
    em 1, 2 ou 3 painéis, dependendo da largura.
    """
    largura_vao = visita.largura
    altura_peca = round(visita.altura, 3)

    if largura_vao <= 1.6:
        n = 1
    elif largura_vao <= 3.0:
        n = 2
    else:
        n = 3

    largura_modulo = round(largura_vao / n, 3)

    pecas: List[Peca] = []
    for i in range(n):
        pecas.append(Peca(
            codigo=f"G{i+1:02d}",
            tipo="painel",
            posicao=f"painel {i+1}",
            largura=largura_modulo,
            altura=altura_peca,
        ))
    return pecas


def gerar_pecas_basicas(visita: VisitaTecnica, template_id: str) -> List[Peca]:
    if template_id == "box_11":
        return gerar_pecas_box_11(visita)
    if template_id == "box_06":
        return gerar_pecas_box_06(visita)
    if template_id == "box_13":
        return gerar_pecas_box_13(visita)
    if template_id == "box_canto":
        return gerar_pecas_box_canto(visita)
    if template_id == "sacada_reta":
        return gerar_pecas_sacada_reta(visita)
    if template_id == "sacada_L":
        return gerar_pecas_sacada_L(visita)
    if template_id == "espelho_ret":
        return gerar_pecas_espelho_ret(visita)

    # fallback
    return gerar_pecas_generico(visita)


def gerar_laudo(visita: VisitaTecnica, template_id: str) -> Tuple[str, List[str]]:
    alertas: List[str] = []
    linhas: List[str] = []

    linhas.append(
        f"Foi realizada visita técnica no ambiente {visita.ambiente} "
        f"para {visita.tipoServico.lower()}."
    )
    linhas.append(
        f"O vão possui aproximadamente {visita.largura:.2f}m de largura "
        f"por {visita.altura:.2f}m de altura."
    )
    linhas.append(
        f"Será utilizado vidro {visita.tipoVidro} com espessura de "
        f"{visita.espessura}mm e perfis na cor {visita.perfil}."
    )

    if visita.desnivel > 0.5:
        alertas.append(
            f"Parede com desnível de {visita.desnivel:.1f} cm: necessário uso de calços "
            "e conferência do prumo antes da instalação."
        )

    if visita.observacoes:
        linhas.append(f"Observações do técnico: {visita.observacoes}")

    # complementos por template
    if template_id == "box_11":
        linhas.append(
            "O modelo definido foi BOX-11 (duas portas de correr com dois fixos), "
            "com distribuição de peças calculada para melhor circulação e vedação."
        )
    elif template_id == "box_06":
        linhas.append(
            "O modelo definido foi BOX-06 (uma porta de correr e um fixo lateral), "
            "voltado para otimizar a passagem em espaços compactos."
        )
    elif template_id == "box_13":
        linhas.append(
            "O modelo definido foi BOX-13 (porta pivotante com fixo lateral), "
            "proporcionando maior área livre de acesso."
        )
    elif template_id == "box_canto":
        linhas.append(
            "Foi considerado box de canto em duas faces, com combinação de portas de correr "
            "e fixos, respeitando o vão disponível em cada lado."
        )
    elif template_id == "sacada_reta":
        linhas.append(
            "A sacada reta foi fracionada em módulos de vidro para facilitar o manuseio, "
            "a instalação e a manutenção preventiva."
        )
    elif template_id == "sacada_L":
        linhas.append(
            "A sacada em L foi dividida em duas faces, cada uma fracionada em painéis, "
            "respeitando o encontro em 90° e a estabilidade do conjunto."
        )
    elif template_id == "espelho_ret":
        linhas.append(
            "O projeto considera espelho retangular dimensionado para o vão informado, "
            "com atenção ao tipo de fixação e preparo do substrato."
        )
    elif template_id == "generico":
        linhas.append(
            "O projeto foi definido de forma modular, fracionando o vão em painéis para "
            "garantir melhor transporte, instalação e segurança."
        )

    laudo = " ".join(linhas)
    return laudo, alertas


# ────────────────────── ENDPOINTS ──────────────────────
@app.get("/")
def raiz():
    return {"status": "ok", "mensagem": "API IA Projetos Vidraçaria rodando"}


# Só laudo (para PDF da visita)
@app.post("/ia/gerar-relatorio-visita", response_model=LaudoResposta)
def gerar_relatorio_visita(visita: VisitaTecnica) -> LaudoResposta:
    template_id = escolher_template(visita)
    laudo, alertas = gerar_laudo(visita, template_id)
    return LaudoResposta(
        templateId=template_id,
        laudoTecnico=laudo,
        alertas=alertas,
    )


# Projeto completo (peças + laudo)
@app.post("/ia/gerar-projeto", response_model=ProjetoResposta)
def gerar_projeto(visita: VisitaTecnica) -> ProjetoResposta:
    template_id = escolher_template(visita)
    pecas = gerar_pecas_basicas(visita, template_id)
    laudo, alertas = gerar_laudo(visita, template_id)

    return ProjetoResposta(
        templateId=template_id,
        descricaoModelo=f"Modelo {template_id.upper()}",
        pecas=pecas,
        vidro=f"{visita.tipoVidro} {visita.espessura}mm",
        perfil=visita.perfil,
        laudoTecnico=laudo,
        alertas=alertas,
    )

