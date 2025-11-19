"""
Módulo de extração de dados para o JGM Smart Planning_IA.

Versão V1 (POC):
- Lê arquivos CSV exportados do SAP e armazena em dataframes.
- Depois poderemos substituir/estender para leitura via OData / APIs do SAP.

Estrutura esperada de arquivos (em C:\JMOURA\PROJETOS_IA\JGM_SMART_PLANNING_IA\data_raw):
- planned_orders.csv          -> Ordens planejadas / ordens de produção
- work_centers.csv            -> Centros de trabalho / máquinas
"""

import pandas as pd
from pathlib import Path

# Diretório base do projeto (2 níveis acima deste arquivo)
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = BASE_DIR / "data_raw"


def carregar_planned_orders(nome_arquivo: str = "planned_orders.csv") -> pd.DataFrame:
    """
    Carrega a lista de ordens planejadas / ordens de produção a partir de um CSV.

    Espera colunas como (podemos ajustar depois):
    - order_id
    - material
    - material_desc
    - qty
    - work_center_sap
    - mrp_controller
    - due_date
    """
    caminho = DATA_RAW_DIR / nome_arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    df = pd.read_csv(caminho)
    return df


def carregar_work_centers(nome_arquivo: str = "work_centers.csv") -> pd.DataFrame:
    """
    Carrega a lista de centros de trabalho / máquinas a partir de um CSV.

    Exemplo de colunas esperadas:
    - work_center_sap
    - descricao
    - capacidade_teorica
    - oee_historico
    - velocidade_media
    - confiabilidade
    """
    caminho = DATA_RAW_DIR / nome_arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    df = pd.read_csv(caminho)
    return df


if __name__ == "__main__":
    # Teste rápido de sanidade (opcional)
    try:
        po = carregar_planned_orders()
        wc = carregar_work_centers()
        print("Ordens carregadas:", len(po))
        print("Centros de trabalho carregados:", len(wc))
    except Exception as e:
        print("Erro ao carregar dados:", e)
