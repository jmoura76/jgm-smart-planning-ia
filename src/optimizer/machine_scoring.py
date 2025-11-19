"""
Módulo de cálculo de score das máquinas/centros de trabalho
para o JGM Smart Planning_IA.

Ideia:
- Combinar indicadores como OEE, velocidade média e confiabilidade
  em um único "score" que será usado para sugerir a melhor máquina
  para cada ordem de produção.

Depois poderemos sofisticar com modelos de ML.
"""

import pandas as pd
import numpy as np


def calcular_score_maquinas(df_maquinas: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe um DataFrame com dados de máquinas/centros de trabalho e
    devolve o mesmo DataFrame com uma coluna 'score' calculada.

    Colunas esperadas no df_maquinas:
    - oee_historico       (0 a 1 ou 0 a 100)
    - velocidade_media    (unidades/hora, por exemplo)
    - confiabilidade      (0 a 1 ou 0 a 100)

    Regras V1 (POC):
    - Normalizamos as métricas para 0–1.
    - Aplicamos pesos para cada métrica.
    """

    df = df_maquinas.copy()

    # Garantir que não teremos problemas com valores faltantes
    for col in ["oee_historico", "velocidade_media", "confiabilidade"]:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente no DataFrame: {col}")
        df[col] = df[col].astype(float).fillna(0.0)

    # Normalização simples min-max 0–1
    def min_max(series: pd.Series) -> pd.Series:
        if series.max() == series.min():
            # evita divisão por zero
            return pd.Series(1.0, index=series.index)
        return (series - series.min()) / (series.max() - series.min())

    df_norm = pd.DataFrame(index=df.index)
    df_norm["oee_norm"] = min_max(df["oee_historico"])
    df_norm["vel_norm"] = min_max(df["velocidade_media"])
    df_norm["conf_norm"] = min_max(df["confiabilidade"])

    # Pesos (podemos ajustar depois conforme Joyson):
    peso_oee = 0.5
    peso_vel = 0.3
    peso_conf = 0.2

    df["score"] = (
        peso_oee * df_norm["oee_norm"] +
        peso_vel * df_norm["vel_norm"] +
        peso_conf * df_norm["conf_norm"]
    )

    # Ordenar da melhor para a pior máquina
    df_ordenado = df.sort_values("score", ascending=False)

    return df_ordenado


if __name__ == "__main__":
    # Teste rápido com dados fictícios
    dados_teste = {
        "work_center_sap": ["CT01", "CT02", "CT03"],
        "oee_historico": [0.85, 0.92, 0.78],
        "velocidade_media": [100, 95, 110],
        "confiabilidade": [0.9, 0.8, 0.95],
    }
    df_test = pd.DataFrame(dados_teste)
    res = calcular_score_maquinas(df_test)
    print(res[["work_center_sap", "score"]])
