"""
eventos.py - Simulador de eventos ambientales que afectan a la colmena
Implementa hilos para generar eventos como clima, ataques y ciclos de día/noche
"""

import threading
import time
import random
import math

class GestorEventos(threading.Thread):
    """
    Controlador principal que simula eventos externos que afectan a la colmena
    """
    
    def __init__(self, colmena, tiempo_simulacion=120):
        """
        Inicializa el gestor de eventos
        
        Args:
            colmena: Referencia a la colmena compartida
            tiempo_simulacion: Duración total de la simulación en segundos
        """
        super().__init__()
        self.colmena = colmena
        self.tiempo_simulacion = tiempo_simulacion
        self.daemon = True  # Termina cuando el hilo principal acaba
        
        # Crear hilos para diferentes tipos de eventos
        self.evento_clima = EventoClima(colmena)
        self.evento_ataque = EventoAtaque(colmena)
        self.evento_dia_noche = EventoDiaNoche(colmena)
    
    def run(self):
        """Ejecuta la simulación por el tiempo especificado"""
        print("[Eventos] Iniciando simulación de eventos ambientales...")
        
        # Iniciar todos los hilos de eventos
        self.evento_clima.start()
        self.evento_ataque.start()
        self.evento_dia_noche.start()
        
        # Esperar el tiempo total de simulación
        time.sleep(self.tiempo_simulacion)
        
        # Señalizar fin de simulación
        self.colmena.event_fin_simulacion.set()
        print("[Eventos] Fin de la simulación de eventos ambientales")


class EventoClima(threading.Thread):
    """Simula cambios en el clima que afectan a la calidad de las flores"""
    
    def __init__(self, colmena):
        super().__init__()
        self.colmena = colmena
        self.daemon = True
        
        # Parámetros del clima
        self.probabilidad_lluvia = 0.3  # 30% de probabilidad de lluvia
        self.duracion_min_lluvia = 2    # Duración mínima de lluvia en segundos
        self.duracion_max_lluvia = 5   # Duración máxima de lluvia en segundos
    
    def run(self):
        """Simula cambios climáticos aleatorios"""
        while not self.colmena.event_fin_simulacion.is_set():
            # Tiempo entre cambios climáticos (10-20 segundos)
            tiempo_espera = random.uniform(4,8)
            time.sleep(tiempo_espera)
            
            if self.colmena.event_fin_simulacion.is_set():
                break
            
            # Determinar si lloverá
            lluvia = random.random() < self.probabilidad_lluvia
            
            if lluvia:
                # Cuando llueve, la calidad de las flores disminuye
                calidad_flores = random.uniform(0.3, 0.7)
                duracion = random.uniform(
                    self.duracion_min_lluvia, 
                    self.duracion_max_lluvia
                )
                
                print(f"[Clima] Comienza a llover. Calidad de flores: {calidad_flores:.2f}")
                self.colmena.cambiar_clima(True, calidad_flores)
                
                time.sleep(duracion)
                
                if self.colmena.event_fin_simulacion.is_set():
                    break
            
            # Después de la lluvia o si no llueve, el clima es favorable
            calidad_flores = random.uniform(0.8, 1.2)
            print(f"[Clima] Clima favorable. Calidad de flores: {calidad_flores:.2f}")
            self.colmena.cambiar_clima(False, calidad_flores)


class EventoAtaque(threading.Thread):
    """Simula ataques aleatorios a la colmena"""
    
    def __init__(self, colmena):
        super().__init__()
        self.colmena = colmena
        self.daemon = True
        
        # Parámetros de ataques
        self.probabilidad_base = 0.5  # Probabilidad base de ataque
        self.intervalo_min = 5      # Tiempo mínimo entre ataques (segundos)
        self.intervalo_max = 8      # Tiempo máximo entre ataques (segundos)
    
    def run(self):
        """Genera ataques aleatorios a la colmena"""
        # Espera inicial para dar tiempo a que la colmena se establezca
        time.sleep(10)
        
        while not self.colmena.event_fin_simulacion.is_set():
            # Calcular tiempo hasta el próximo ataque
            tiempo_espera = random.uniform(self.intervalo_min, self.intervalo_max)
            time.sleep(tiempo_espera)
            
            if self.colmena.event_fin_simulacion.is_set():
                break
            
            # Mayor probabilidad de ataque durante el día
            probabilidad_actual = self.probabilidad_base
            if self.colmena.event_dia.is_set():
                probabilidad_actual *= 1.5  # 50% más probable durante el día
            
            # Verificar si ocurre un ataque
            if random.random() < probabilidad_actual:
                # Generar un ataque
                tipo_ataque = random.choice(["avispa", "pájaro", "oso", "humano"])
                intensidad = random.uniform(1, 10)
                
                print(f"[Ataque] ¡Alerta! Ataque de {tipo_ataque} "
                      f"con intensidad {intensidad:.1f}")
                
                # Registrar el ataque en la colmena
                self.colmena.registrar_ataque()
                
                # Esperar a que el ataque sea neutralizado o un timeout
                timeout = 5  # Segundos máximos para neutralizar el ataque
                inicio = time.time()
                
                while (self.colmena.event_ataque.is_set() and 
                       time.time() - inicio < timeout and
                       not self.colmena.event_fin_simulacion.is_set()):
                    time.sleep(0.1)
                
                if self.colmena.event_ataque.is_set():
                    # Ataque no neutralizado a tiempo
                    self.colmena.event_ataque.clear()
                    print("[Ataque] Ataque no neutralizado a tiempo")


class EventoDiaNoche(threading.Thread):
    """Simula los ciclos de día y noche que afectan al comportamiento de las abejas"""
    
    def __init__(self, colmena):
        super().__init__()
        self.colmena = colmena
        self.daemon = True
        
        # Parámetros del ciclo día/noche
        self.duracion_dia = 8    # Duración del día en segundos
        self.duracion_noche = 4  # Duración de la noche en segundos
    
    def run(self):
        """Alterna entre ciclos de día y noche"""
        # Empezamos con el día
        self.colmena.cambiar_ciclo_dia(True)
        es_dia = True
        
        while not self.colmena.event_fin_simulacion.is_set():
            # Duración del ciclo actual
            duracion = self.duracion_dia if es_dia else self.duracion_noche
            
            # Esperar por la duración del ciclo actual
            time.sleep(duracion)
            
            if self.colmena.event_fin_simulacion.is_set():
                break
            
            # Cambiar al ciclo opuesto
            es_dia = not es_dia
            self.colmena.cambiar_ciclo_dia(es_dia)
            
            estado = "día" if es_dia else "noche"
            print(f"[Ciclo] Cambio a {estado}")