from src.extractor.extracao_sap import carregar_planned_orders, carregar_work_centers
from src.optimizer.machine_scoring import calcular_score_maquinas
from src.optimizer.order_allocator import alocar_ordens_com_base_no_rank
from src.simulator.simulador_manut import simular_lote_ordens

def main():
    print("Carregando dados...")
    df_orders = carregar_planned_orders()
    df_machines = carregar_work_centers()

    print("Calculando score...")
    df_scored = calcular_score_maquinas(df_machines)

    print("Alocando ordens...")
    df_alloc = alocar_ordens_com_base_no_rank(df_orders, df_scored)

    print("\nIniciando simulação MES (Manit)...")
    df_sim = simular_lote_ordens(df_alloc, df_machines)
    
    print("\nResultado da simulação:")
    print(df_sim)

if __name__ == "__main__":
    main()
