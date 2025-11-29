from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional

app = FastAPI(
    title="IA Projetos Vidraçaria",
    version="0.1.0",
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

    return "generico"


# 🔥 NOVO: cálculo “perfeito” do BOX-11 (duas portas + dois fixos)
def gerar_pecas_box_11(visita: VisitaTecnica) -> List[Peca]:
    """
    Cálculo determinístico estilo Casas Mansur.
    Ajuste as folgas/sobreposição aqui de acordo com o seu padrão real.
    """
    folga_lateral = 0.03            # 3 cm TOTAL do vão
    folga_altura = 0.05             # 5 cm TOTAL na altura
    sobreposicao_folhas = 0.05      # 5 cm de sobreposição da porta no fixo

    largura_vao = visita.largura
    altura_vao = visita.altura

    # Altura útil do vidro (mesma para portas e fixos)
    altura_peca = round(altura_vao - folga_altura, 3)

    # Larguras:
    # (vão - folga total - sobreposição) dividido em 2 blocos: um fixo + uma porta
    largura_fixo = round((largura_vao - folga_lateral - sobreposicao_folhas) / 2, 3)
    largura_porta = round(largura_fixo + sobreposicao_folhas, 3)

    pecas: List[Peca] = []

    # Fixo esquerdo
    pecas.append(Peca(
        codigo="F01",
        tipo="fixo",
        posicao="fixo esquerdo",
        largura=largura_fixo,
        altura=altura_peca,
    ))

    # Porta 1
    pecas.append(Peca(
        codigo="P01",
        tipo="porta",
        posicao="porta correr 1",
        largura=largura_porta,
        altura=altura_peca,
    ))

    # Porta 2
    pecas.append(Peca(
        codigo="P02",
        tipo="porta",
        posicao="porta correr 2",
        largura=largura_porta,
        altura=altura_peca,
    ))

    # Fixo direito
    pecas.append(Peca(
        codigo="F02",
        tipo="fixo",
        posicao="fixo direito",
        largura=largura_fixo,
        altura=altura_peca,
    ))

    return pecas


def gerar_pecas_basicas(visita: VisitaTecnica, template_id: str) -> List[Peca]:
    pecas: List[Peca] = []

    # 🔥 AGORA: quando for BOX-11, usamos o cálculo “perfeito”
    if template_id == "box_11":
        return gerar_pecas_box_11(visita)

    # Demais modelos (genérico por enquanto)
    pecas.append(Peca(
        codigo="P01",
        tipo="painel",
        posicao="principal",
        largura=visita.largura,
        altura=visita.altura,
    ))

    return pecas


def gerar_laudo(visita: VisitaTecnica, template_id: str) -> tuple[str, List[str]]:
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

    if template_id == "box_11":
        linhas.append(
            "O modelo definido foi BOX-11 (duas portas de correr com dois fixos), "
            "com distribuição de peças calculada para melhor circulação e vedação."
        )

    laudo = " ".join(linhas)
    return laudo, alertas


# ────────────────────── ENDPOINTS ──────────────────────
@app.get("/")
def raiz():
    return {"status": "ok", "mensagem": "API IA Projetos Vidraçaria rodando"}


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
