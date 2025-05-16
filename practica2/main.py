from colmena import Colmena
from agentes import Recolectora, Almacenadora, Nodriza, Defensora, Reina
from eventos import GestorEventos
from analisis import Analizador
import time


def main():
    # Duración corta pero simulación intensa
    duracion_simulacion = 30  # segundos reales

    # Más abejas activas
    abejas_iniciales = {
        "recolectora": 8,
        "almacenadora": 6,
        "nodriza": 4,
        "defensora": 3
    }

    # Inicializar colmena
    colmena = Colmena()
    print("[Main] Colmena inicializada.")

    # Crear reina
    reina = Reina(colmena)
    reina.start()
    print("[Main] Reina iniciada.")

    # Crear abejas obreras con tiempos reducidos
    abejas = []
    fabrica = {
        "recolectora": Recolectora,
        "almacenadora": Almacenadora,
        "nodriza": Nodriza,
        "defensora": Defensora
    }

    for rol, cantidad in abejas_iniciales.items():
        for _ in range(cantidad):
            abeja = fabrica[rol](colmena, tiempo_vida=20, tiempo_trabajo=0.1)
            abeja.start()
            abejas.append(abeja)
            reina.agregar_abeja(abeja)

    print(f"[Main] {sum(abejas_iniciales.values())} abejas lanzadas.")

    # Iniciar eventos ambientales intensos
    gestor_eventos = GestorEventos(colmena, tiempo_simulacion=duracion_simulacion)
    gestor_eventos.start()

    # Iniciar análisis frecuente
    analizador = Analizador(colmena, intervalo=2)
    analizador.iniciar()

    # Esperar a que termine
    while not colmena.event_fin_simulacion.is_set():
        time.sleep(1)

    print("[Main] Simulación finalizada. Generando informe...")
    analizador.imprimir_informe()
    analizador.guardar_informe()
    print("[Main] Programa terminado.")


if __name__ == "__main__":
    main()
