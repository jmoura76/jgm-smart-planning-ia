from src.extractor.extracao_sap import carregar_planned_orders, carregar_work_centers
from src.optimizer.machine_scoring import calcular_score_maquinas

def main():
    print("Carregando ordens planejadas...")
    df_orders = carregar_planned_orders()
    print(df_orders)

    print("\nCarregando centros de trabalho...")
    df_wcs = carregar_work_centers()
    print(df_wcs)

    print("\nCalculando score das máquinas...")
    df_scored = calcular_score_maquinas(df_wcs)
    print(df_scored[["work_center_sap", "descricao", "score"]])

if __name__ == "__main__":
    main()
