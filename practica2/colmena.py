"""
colmena.py - Contenedor central del estado de la colmena
Define las estructuras compartidas y mecanismos de sincronización
"""

import threading
import queue
import random
from collections import defaultdict

class Colmena:
    """Clase principal que mantiene el estado compartido de la colmena"""
    
    def __init__(self, 
                 capacidad_celdas=100,
                 capacidad_polen=5,
                 num_larvas=20):
        """
        Inicializa el estado de la colmena y las estructuras compartidas
        
        Args:
            capacidad_celdas: Número máximo de celdas para almacenar néctar
            capacidad_polen: Capacidad de cada recolectora para transportar polen/néctar
            num_larvas: Número de larvas en la colmena
        """
        # Recursos compartidos y capacidades
        self.capacidad_celdas = capacidad_celdas
        self.capacidad_polen = capacidad_polen
        self.celdas_ocupadas = 0
        
        # Estado de larvas
        self.num_larvas = num_larvas
        self.larvas_alimentadas = 0
        
        # Colas de comunicación
        self.queue_nectar = queue.Queue()  # Cola entre recolectoras y almacenadoras
        
        # Contadores para métricas
        self.contador_global = {
            "nectar_recolectado": 0,
            "nectar_almacenado": 0,
            "ataques_detectados": 0,
            "ataques_neutralizados": 0,
            "cambios_rol": 0,
            "flores_visitadas": 0,
            "larvas_alimentadas": 0
        }
        
        # Estadísticas por abeja
        self.estadisticas_abejas = defaultdict(lambda: defaultdict(int))
        
        # Mecanismos de sincronización
        self.semaforo_celdas = threading.Semaphore(capacidad_celdas)  # Control de acceso a celdas
        self.lock_celdas = threading.Lock()  # Para actualizar estado de celdas ocupadas
        self.lock_larvas = threading.Lock()  # Exclusión mutua para alimentar larvas
        self.lock_estadisticas = threading.Lock()  # Para actualizar estadísticas
        
        # Eventos
        self.event_ataque = threading.Event()  # Señal de ataque
        self.event_dia = threading.Event()  # Señal de día (True) o noche (False)
        self.event_dia.set()  # Empezamos en el día
        self.event_lluvia = threading.Event()  # Señal de lluvia
        self.event_fin_simulacion = threading.Event()  # Señal para terminar
        
        # Condiciones ambientales
        self.calidad_flores = 1.0  # Multiplicador de calidad de flores (afectado por clima)
        self.lock_calidad_flores = threading.Lock()
        
        # Registro de abejas activas por rol
        self.abejas_por_rol = defaultdict(int)
        self.lock_roles = threading.Lock()
        
        # Cola para mensajes a la reina
        self.queue_reina = queue.Queue()
    
    def registrar_abeja(self, id_abeja, rol):
        """Registra una nueva abeja en el contador por rol"""
        with self.lock_roles:
            self.abejas_por_rol[rol] += 1
    
    def cambiar_rol_abeja(self, rol_anterior, rol_nuevo):
        """Actualiza el registro cuando una abeja cambia de rol"""
        with self.lock_roles:
            self.abejas_por_rol[rol_anterior] -= 1
            self.abejas_por_rol[rol_nuevo] += 1
            self.contador_global["cambios_rol"] += 1
    
    def obtener_distribucion_roles(self):
        """Devuelve un diccionario con la cantidad de abejas por rol"""
        with self.lock_roles:
            return dict(self.abejas_por_rol)
    
    def agregar_nectar_cola(self, cantidad, id_abeja):
        """
        Una recolectora añade néctar a la cola para las almacenadoras
        """
        self.queue_nectar.put((cantidad, id_abeja))
        with self.lock_estadisticas:
            self.contador_global["nectar_recolectado"] += cantidad
            self.estadisticas_abejas[id_abeja]["nectar_recolectado"] += cantidad
    
    def obtener_nectar_cola(self):
        """
        Una almacenadora obtiene néctar de la cola para almacenar
        Devuelve: (cantidad, id_abeja_origen) o None si no hay
        """
        try:
            return self.queue_nectar.get(block=False)
        except queue.Empty:
            return None
    
    def almacenar_nectar(self, cantidad, id_abeja):
        """
        Almacena néctar en las celdas disponibles
        Devuelve: True si pudo almacenarse, False si no
        """
        if self.semaforo_celdas.acquire(blocking=False):
            with self.lock_celdas:
                self.celdas_ocupadas += 1
            
            with self.lock_estadisticas:
                self.contador_global["nectar_almacenado"] += cantidad
                self.estadisticas_abejas[id_abeja]["nectar_almacenado"] += cantidad
            
            return True
        return False
    
    def consumir_nectar(self, id_abeja):
        """
        Consume néctar de las celdas (para alimentar larvas)
        Devuelve: True si pudo consumirse, False si no hay celdas ocupadas
        """
        with self.lock_celdas:
            if self.celdas_ocupadas > 0:
                self.celdas_ocupadas -= 1
                self.semaforo_celdas.release()
                with self.lock_estadisticas:
                    self.estadisticas_abejas[id_abeja]["nectar_consumido"] += 1
                return True
            return False
    
    def alimentar_larva(self, id_abeja):
        """
        Intenta alimentar una larva. Requiere néctar disponible
        Devuelve: True si pudo alimentar, False si no
        """
        if self.consumir_nectar(id_abeja):
            with self.lock_larvas:
                if self.larvas_alimentadas < self.num_larvas:
                    self.larvas_alimentadas += 1
                    with self.lock_estadisticas:
                        self.contador_global["larvas_alimentadas"] += 1
                        self.estadisticas_abejas[id_abeja]["larvas_alimentadas"] += 1
                    return True
            return False
        return False
    
    def visitar_flor(self, id_abeja):
        """
        Simula una visita a una flor para recolectar néctar
        Afectado por condiciones climáticas
        """
        if not self.event_dia.is_set():  # Es de noche
            return 0  # No se recolecta de noche
        
        with self.lock_calidad_flores:
            calidad = self.calidad_flores
        
        # Cantidad base entre 1-5, multiplicada por calidad y aleatorizada
        polen_recolectado = min(
            round(random.uniform(1, self.capacidad_polen) * calidad),
            self.capacidad_polen
        )
        
        with self.lock_estadisticas:
            self.contador_global["flores_visitadas"] += 1
            self.estadisticas_abejas[id_abeja]["flores_visitadas"] += 1
        
        return max(0, polen_recolectado)  # Mínimo 0
    
    def registrar_ataque(self):
        """Registra un ataque a la colmena"""
        self.event_ataque.set()
        with self.lock_estadisticas:
            self.contador_global["ataques_detectados"] += 1
    
    def neutralizar_ataque(self, id_abeja):
        """Una defensora neutraliza un ataque"""
        self.event_ataque.clear()
        with self.lock_estadisticas:
            self.contador_global["ataques_neutralizados"] += 1
            self.estadisticas_abejas[id_abeja]["ataques_neutralizados"] += 1
    
    def cambiar_clima(self, lluvia, calidad_flores):
        """Actualiza el estado climático y su efecto en las flores"""
        if lluvia:
            self.event_lluvia.set()
        else:
            self.event_lluvia.clear()
        
        with self.lock_calidad_flores:
            self.calidad_flores = calidad_flores
    
    def cambiar_ciclo_dia(self, es_dia):
        """Cambia entre día y noche"""
        if es_dia:
            self.event_dia.set()
        else:
            self.event_dia.clear()
    
    def enviar_mensaje_reina(self, mensaje):
        """Envía un mensaje a la reina a través de la cola"""
        self.queue_reina.put(mensaje)
    
    def obtener_mensaje_reina(self, timeout=0.1):
        """Obtiene un mensaje de la cola de la reina"""
        try:
            return self.queue_reina.get(block=True, timeout=timeout)
        except queue.Empty:
            return None
    
    def obtener_metricas(self):
        """Devuelve las métricas globales de la colmena"""
        with self.lock_estadisticas, self.lock_celdas:
            metricas = dict(self.contador_global)
            metricas["celdas_ocupadas"] = self.celdas_ocupadas
            metricas["celdas_libres"] = self.capacidad_celdas - self.celdas_ocupadas
            return metricas
    
    def obtener_estadisticas_abejas(self):
        """Devuelve las estadísticas individuales de cada abeja"""
        with self.lock_estadisticas:
            return dict(self.estadisticas_abejas)