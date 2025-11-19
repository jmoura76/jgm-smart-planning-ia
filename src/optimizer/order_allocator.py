"""
Módulo de alocação inteligente de ordens de produção para máquinas
JGM Smart Planning_IA - Versão POC.

Lógica V1:
- Para cada ordem, escolhemos a máquina com maior score
  (calculado em machine_scoring.py)

V2:
- Penalizar máquinas sobrecarregadas
- Usar capacidade residual
- Usar otimização (ORTools)
- Previsão de throughput via IA
"""

import pandas as pd


def alocar_ordens_por_score(df_orders: pd.DataFrame, df_machines_scored: pd.DataFrame) -> pd.DataFrame:
    """
    Faz uma alocação simples:
    - Para cada ordem, atribui a máquina com melhor score geral.

    Retorna um DataFrame com uma nova coluna: 'machine_sugerida'
    """

    melhor_maquina = df_machines_scored.iloc[0]["work_center_sap"]

    df_resultado = df_orders.copy()
    df_resultado["machine_sugerida"] = melhor_maquina

    return df_resultado


def alocar_ordens_com_base_no_rank(df_orders: pd.DataFrame, df_machines_scored: pd.DataFrame) -> pd.DataFrame:
    """
    V1 mais inteligente:
    - Distribui ordens nas máquinas seguindo a ordem do score.
    - Exemplo: 
        1ª ordem → máquina top 1
        2ª ordem → máquina top 2
        3ª ordem → máquina top 3
        4ª ordem → máquina top 1 (reinicia ciclo)
    """

    df_resultado = df_orders.copy()
    maquinas = df_machines_scored["work_center_sap"].tolist()

    alocacoes = []
    for i, _ in df_orders.iterrows():
        maquina = maquinas[i % len(maquinas)]
        alocacoes.append(maquina)

    df_resultado["machine_sugerida"] = alocacoes

    return df_resultado


if __name__ == "__main__":
    print("Módulo de alocação carregado com sucesso.")
