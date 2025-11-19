"""
Simulador do MES Manit - Versão POC
JGM Smart Planning_IA

Objetivo:
- Simular o tempo de execução de uma OP enviada ao chão de fábrica.
- Gerar atrasos aleatórios e performance variável (como acontece no mundo real).
- Permitir que o dashboard mostre o "andamento" da OP.

Interpretação:
- tempo_estimado_horas: calculado com base em qty / velocidade_media (histórico)
- tempo_real_horas: tempo ajustado com uma variação aleatória (-20% a +20%)
- desvio_percentual: (tempo_real - tempo_estimado) / tempo_estimado * 100
    < 0  -> Ganho de performance (real mais rápido que estimado)
    > 0  -> Perda de performance (real mais lento que estimado)
"""

import random
import pandas as pd


def simular_execucao_ordem(ordem: pd.Series, df_machines: pd.DataFrame) -> dict:
    """
    Simula o tempo de execução de uma ordem em uma máquina específica.
    """

    machine = ordem["machine_sugerida"]
    row = df_machines[df_machines["work_center_sap"] == machine].iloc[0]

    velocidade = row["velocidade_media"]  # unidades/hora

    # tempo base em horas
    tempo_base_horas = ordem["qty"] / velocidade

    # inserir variabilidade (-20% a +20%)
    variacao = random.uniform(-0.20, 0.20)
    tempo_final_horas = tempo_base_horas * (1 + variacao)

    desvio_percentual = variacao * 100
    status = "Ganho" if desvio_percentual < 0 else "Perda" if desvio_percentual > 0 else "Neutro"

    return {
        "order_id": ordem["order_id"],
        "machine": machine,
        "qty": ordem["qty"],
        "tempo_estimado_horas": round(tempo_base_horas, 2),
        "tempo_real_horas": round(tempo_final_horas, 2),
        "desvio_percentual": round(desvio_percentual, 1),
        "status": status,
    }


def simular_lote_ordens(df_ordens: pd.DataFrame, df_machines: pd.DataFrame) -> pd.DataFrame:
    """
    Simula todas as ordens alocadas.
    Retorna um DataFrame com estimativas e tempos simulados.
    """
    resultados = []
    for _, ordem in df_ordens.iterrows():
        sim = simular_execucao_ordem(ordem, df_machines)
        resultados.append(sim)
    return pd.DataFrame(resultados)


if __name__ == "__main__":
    print("Simulador Manit carregado.")
