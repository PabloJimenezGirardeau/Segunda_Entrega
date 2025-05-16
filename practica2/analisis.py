import time
from collections import defaultdict
import threading
import json
import os


class Analizador:
    def __init__(self, colmena, intervalo=5):
        self.colmena = colmena
        self.intervalo = intervalo
        self.historial_metricas = []
        self.historial_roles = []
        self.hora_inicio = time.time()
        self.eficiencia_roles = defaultdict(float)
        self.thread_recopilacion = threading.Thread(
            target=self._recopilar_periodicamente,
            daemon=True
        )

    def iniciar(self):
        self.thread_recopilacion.start()
        print("[Análisis] Iniciado sistema de monitoreo de la colmena")

    def _recopilar_periodicamente(self):
        while not self.colmena.event_fin_simulacion.is_set():
            metricas = self.colmena.obtener_metricas()
            distribucion = self.colmena.obtener_distribucion_roles()
            tiempo_actual = time.time() - self.hora_inicio
            metricas["tiempo"] = tiempo_actual
            self.historial_metricas.append(metricas.copy())
            self.historial_roles.append({
                "tiempo": tiempo_actual,
                "roles": distribucion.copy()
            })
            time.sleep(self.intervalo)

    def calcular_estadisticas(self):
        if not self.historial_metricas:
            return {"error": "No hay datos suficientes para análisis"}

        inicio = self.historial_metricas[0]
        final = self.historial_metricas[-1]
        tiempo_total = final["tiempo"] / 60

        if tiempo_total > 0:
            nectar_por_minuto = final["nectar_recolectado"] / tiempo_total
            ataques_por_minuto = final["ataques_detectados"] / tiempo_total
            larvas_por_minuto = final["larvas_alimentadas"] / tiempo_total
        else:
            nectar_por_minuto = 0
            ataques_por_minuto = 0
            larvas_por_minuto = 0

        if final["ataques_detectados"] > 0:
            eficiencia_defensa = (final["ataques_neutralizados"] / 
                                 final["ataques_detectados"]) * 100
        else:
            eficiencia_defensa = 100

        if final["nectar_recolectado"] > 0:
            eficiencia_almacenamiento = (final["nectar_almacenado"] / 
                                        final["nectar_recolectado"]) * 100
        else:
            eficiencia_almacenamiento = 0

        roles_promedio = {}
        if self.historial_roles:
            conteo_roles = defaultdict(int)
            total_registros = len(self.historial_roles)

            for registro in self.historial_roles:
                for rol, cantidad in registro["roles"].items():
                    conteo_roles[rol] += cantidad

            roles_promedio = {
                rol: cantidad / total_registros 
                for rol, cantidad in conteo_roles.items()
            }

        estadisticas = {
            "tiempo_total_segundos": final["tiempo"],
            "tiempo_total_minutos": tiempo_total,
            "nectar": {
                "total_recolectado": final["nectar_recolectado"],
                "total_almacenado": final["nectar_almacenado"],
                "tasa_recoleccion": nectar_por_minuto,
                "eficiencia_almacenamiento": eficiencia_almacenamiento
            },
            "seguridad": {
                "ataques_detectados": final["ataques_detectados"],
                "ataques_neutralizados": final["ataques_neutralizados"],
                "tasa_ataques": ataques_por_minuto,
                "eficiencia_defensa": eficiencia_defensa
            },
            "reproduccion": {
                "larvas_alimentadas": final["larvas_alimentadas"],
                "tasa_alimentacion": larvas_por_minuto
            },
            "adaptabilidad": {
                "cambios_rol": final["cambios_rol"]
            },
            "estado_final": {
                "celdas_ocupadas": final["celdas_ocupadas"],
                "celdas_libres": final["celdas_libres"]
            },
            "roles_promedio": roles_promedio
        }

        return estadisticas

    def generar_informe(self):
        estadisticas = self.calcular_estadisticas()
        return {
            "estadisticas_globales": estadisticas,
            "momento_informe": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def imprimir_informe(self):
        informe = self.generar_informe()

        print("\n" + "="*50)
        print(" INFORME DE RENDIMIENTO DE LA COLMENA ")
        print("="*50)

        est = informe["estadisticas_globales"]
        print(f"\nTiempo total de simulación: {est['tiempo_total_segundos']:.2f} segundos "
              f"({est['tiempo_total_minutos']:.2f} minutos)")

        print("\n--- PRODUCCIÓN DE MIEL ---")
        print(f"Néctar recolectado: {est['nectar']['total_recolectado']} unidades")
        print(f"Néctar almacenado: {est['nectar']['total_almacenado']} unidades")
        print(f"Tasa de recolección: {est['nectar']['tasa_recoleccion']:.2f} unidades/minuto")
        print(f"Eficiencia de almacenamiento: {est['nectar']['eficiencia_almacenamiento']:.2f}%")

        print("\n--- SEGURIDAD DE LA COLMENA ---")
        print(f"Ataques detectados: {est['seguridad']['ataques_detectados']}")
        print(f"Ataques neutralizados: {est['seguridad']['ataques_neutralizados']}")
        print(f"Eficiencia de defensa: {est['seguridad']['eficiencia_defensa']:.2f}%")

        print("\n--- REPRODUCCIÓN ---")
        print(f"Larvas alimentadas: {est['reproduccion']['larvas_alimentadas']}")
        print(f"Tasa de alimentación: {est['reproduccion']['tasa_alimentacion']:.2f} larvas/minuto")

        print("\n--- ADAPTABILIDAD ---")
        print(f"Cambios de rol: {est['adaptabilidad']['cambios_rol']}")

        print("\n--- ESTADO FINAL ---")
        print(f"Celdas ocupadas: {est['estado_final']['celdas_ocupadas']}")
        print(f"Celdas libres: {est['estado_final']['celdas_libres']}")

        print("\n--- ROLES PROMEDIO ---")
        for rol, cantidad in est['roles_promedio'].items():
            print(f"{rol}: {cantidad:.2f}")

        print("\n" + "="*50 + "\n")

    def guardar_informe(self, archivo="informe_colmena.json"):
        informe = self.generar_informe()
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(informe, f, indent=2, ensure_ascii=False)
            print(f"[Análisis] Informe guardado en {archivo}")
        except Exception as e:
            print(f"[Análisis] Error al guardar informe: {e}")