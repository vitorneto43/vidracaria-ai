# models.py
from pydantic import BaseModel
from typing import List, Literal, Optional

class Cliente(BaseModel):
    nome: str
    cidade: Optional[str] = None

class VisitaTecnica(BaseModel):
    largura: float
    altura: float
    tipoVidro: str
    espessura: int
    perfil: str
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
    laudo: Optional[str] = None
