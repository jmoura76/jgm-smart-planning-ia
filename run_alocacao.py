from src.extractor.extracao_sap import carregar_planned_orders, carregar_work_centers
from src.optimizer.machine_scoring import calcular_score_maquinas
from src.optimizer.order_allocator import alocar_ordens_com_base_no_rank

def main():
    print("Carregando dados...")
    df_orders = carregar_planned_orders()
    df_machines = carregar_work_centers()

    print("Calculando score das máquinas...")
    df_scored = calcular_score_maquinas(df_machines)

    print("\nCalculando alocação automática de ordens...")
    df_alloc = alocar_ordens_com_base_no_rank(df_orders, df_scored)

    print("\nResultado:")
    print(df_alloc)

if __name__ == "__main__":
    main()
