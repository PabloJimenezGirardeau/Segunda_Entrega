"""
agentes.py - Definición de las abejas con diferentes roles
Implementa los hilos para cada tipo de agente
"""

import threading
import time
import random
import uuid

class Abeja(threading.Thread):
    """Clase base para todos los tipos de abejas"""
    
    def __init__(self, colmena, id_abeja=None, tiempo_vida=60, 
                 tiempo_trabajo=0.5, rol="genérica"):
        """
        Inicializa una abeja base
        
        Args:
            colmena: Referencia a la colmena compartida
            id_abeja: Identificador único (generado si no se proporciona)
            tiempo_vida: Tiempo máximo de vida en segundos
            tiempo_trabajo: Tiempo entre ciclos de trabajo
            rol: Rol de la abeja en la colmena
        """
        super().__init__()
        self.colmena = colmena
        self.id_abeja = id_abeja or str(uuid.uuid4())[:8]
        self.tiempo_vida = tiempo_vida
        self.tiempo_trabajo = tiempo_trabajo
        self.rol = rol
        self.daemon = True  # Termina cuando el hilo principal acaba
        self.activa = True
        self.colmena.registrar_abeja(self.id_abeja, self.rol)
        
        # Para identificación completa de la abeja
        self.nombre_completo = f"{self.rol}_{self.id_abeja}"
    
    def run(self):
        """Ciclo de vida base para cualquier abeja"""
        tiempo_inicio = time.time()
        
        try:
            while (time.time() - tiempo_inicio < self.tiempo_vida and 
                   self.activa and 
                   not self.colmena.event_fin_simulacion.is_set()):
                
                # Verificar si hay que trabajar (depende del día/noche)
                if not self.colmena.event_dia.is_set() and self.rol != "defensora":
                    # Las abejas excepto defensoras descansan en la noche
                    time.sleep(1)
                    continue
                
                # Ejecutar la tarea específica según rol
                self.trabajar()
                
                # Tiempo entre ciclos de trabajo
                time.sleep(self.tiempo_trabajo)
        except Exception as e:
            print(f"Error en {self.nombre_completo}: {e}")
        finally:
            # Informar a la reina antes de morir (para posible reemplazo)
            if not self.colmena.event_fin_simulacion.is_set():
                self.colmena.enviar_mensaje_reina({
                    "tipo": "muerte", 
                    "rol": self.rol,
                    "id": self.id_abeja
                })
    
    def trabajar(self):
        """Método a sobrescribir por cada tipo específico de abeja"""
        pass
    
    def cambiar_rol(self, nuevo_rol):
        """Cambia el rol de la abeja si es necesario"""
        rol_anterior = self.rol
        self.rol = nuevo_rol
        self.nombre_completo = f"{self.rol}_{self.id_abeja}"
        self.colmena.cambiar_rol_abeja(rol_anterior, nuevo_rol)
        return True
    
    def __str__(self):
        return self.nombre_completo


class Recolectora(Abeja):
    """Abeja que viaja a flores y recolecta néctar/polen"""
    
    def __init__(self, colmena, **kwargs):
        super().__init__(colmena, rol="recolectora", **kwargs)
    
    def trabajar(self):
        # Visitar flor y recolectar polen/néctar
        polen = self.colmena.visitar_flor(self.id_abeja)
        
        if polen > 0:
            # Llevar a la colmena y poner en la cola
            self.colmena.agregar_nectar_cola(polen, self.id_abeja)


class Almacenadora(Abeja):
    """Abeja que traslada el néctar de la cola a las celdas"""
    
    def __init__(self, colmena, **kwargs):
        super().__init__(colmena, rol="almacenadora", **kwargs)
        self.intentos_vacios = 0
    
    def trabajar(self):
        # Intentar obtener néctar de la cola
        resultado = self.colmena.obtener_nectar_cola()
        
        if resultado:
            cantidad, id_origen = resultado
            # Almacenar en celdas disponibles
            self.colmena.almacenar_nectar(cantidad, self.id_abeja)
            self.intentos_vacios = 0
        else:
            # No hay néctar en la cola
            self.intentos_vacios += 1
            
            # Si hay muchos intentos sin éxito, informar a la reina
            if self.intentos_vacios > 10:
                self.colmena.enviar_mensaje_reina({
                    "tipo": "inactiva",
                    "rol": self.rol,
                    "id": self.id_abeja,
                    "intentos": self.intentos_vacios
                })
                self.intentos_vacios = 0


class Nodriza(Abeja):
    """Abeja que alimenta a las larvas con el néctar almacenado"""
    
    def __init__(self, colmena, **kwargs):
        super().__init__(colmena, rol="nodriza", **kwargs)
        self.intentos_sin_alimento = 0
    
    def trabajar(self):
        # Intentar alimentar una larva
        if self.colmena.alimentar_larva(self.id_abeja):
            self.intentos_sin_alimento = 0
        else:
            # No hay suficiente alimento para larvas
            self.intentos_sin_alimento += 1
            
            # Si persiste la falta de néctar, informar a la reina
            if self.intentos_sin_alimento > 5:
                self.colmena.enviar_mensaje_reina({
                    "tipo": "falta_alimento",
                    "rol": self.rol,
                    "id": self.id_abeja
                })
                self.intentos_sin_alimento = 0


class Defensora(Abeja):
    """Abeja que protege la colmena de amenazas externas"""
    
    def __init__(self, colmena, **kwargs):
        super().__init__(colmena, rol="defensora", **kwargs)
        self.tiempo_patrulla = 0.2  # Patrulla más rápido que otras tareas
    
    def trabajar(self):
        # Verificar si hay algún ataque
        if self.colmena.event_ataque.is_set():
            # Defender la colmena
            time.sleep(0.3)  # Tiempo de respuesta al ataque
            self.colmena.neutralizar_ataque(self.id_abeja)
        else:
            # Patrullar normalmente (más rápido)
            time.sleep(self.tiempo_patrulla)


class Reina(Abeja):
    """Abeja reina que coordina la colmena y redistribuye roles"""
    
    def __init__(self, colmena, equilibrio_ideal=None, **kwargs):
        """
        Inicializa la reina con su equilibrio ideal
        
        Args:
            equilibrio_ideal: Diccionario con % ideal de cada rol
        """
        super().__init__(colmena, rol="reina", **kwargs)
        
        # Equilibrio ideal por defecto si no se proporciona
        self.equilibrio_ideal = equilibrio_ideal or {
            "recolectora": 0.4,  # 40%
            "almacenadora": 0.25, # 25%
            "nodriza": 0.25,     # 25%
            "defensora": 0.1     # 10%
        }
        
        # Mapeo de roles para crear nuevas abejas
        self.fabrica_abejas = {
            "recolectora": Recolectora,
            "almacenadora": Almacenadora,
            "nodriza": Nodriza,
            "defensora": Defensora
        }
        
        # Registro de abejas activas por ID
        self.abejas_activas = {}
    
    def agregar_abeja(self, abeja):
        """Registra una nueva abeja en la colonia"""
        self.abejas_activas[abeja.id_abeja] = abeja
    
    def crear_abeja(self, rol):
        """Crea una nueva abeja del rol especificado"""
        if rol in self.fabrica_abejas:
            nueva_abeja = self.fabrica_abejas[rol](self.colmena)
            self.agregar_abeja(nueva_abeja)
            nueva_abeja.start()
            return nueva_abeja
        return None
    
    def reemplazar_abeja_muerta(self, rol):
        """Crea una abeja nueva para reemplazar una que ha muerto"""
        return self.crear_abeja(rol)
    
    def calcular_roles_ideales(self, total_abejas):
        """Calcula cuántas abejas de cada rol debería haber"""
        return {
            rol: round(total_abejas * porcentaje)
            for rol, porcentaje in self.equilibrio_ideal.items()
        }
    
    def identificar_desequilibrio(self):
        """
        Compara la distribución actual con la ideal
        Devuelve: (rol_excedente, rol_deficiente) o (None, None)
        """
        distribucion_actual = self.colmena.obtener_distribucion_roles()
        total_abejas = sum(distribucion_actual.values())
        
        if total_abejas == 0:
            return None, None
        
        roles_ideales = self.calcular_roles_ideales(total_abejas)
        
        # Calcular diferencias porcentuales
        diferencias = {}
        for rol in self.equilibrio_ideal:
            ideal = roles_ideales.get(rol, 0)
            actual = distribucion_actual.get(rol, 0)
            
            # Evitar división por cero
            if ideal == 0:
                diferencias[rol] = float('inf') if actual > 0 else 0
            else:
                diferencias[rol] = (actual - ideal) / ideal
        
        # Encontrar el rol más excedente y más deficiente
        rol_excedente = max(diferencias, key=diferencias.get)
        rol_deficiente = min(diferencias, key=diferencias.get)
        
        # Solo reasignar si hay desequilibrio significativo (>10%)
        if diferencias[rol_excedente] > 0.1 and diferencias[rol_deficiente] < -0.1:
            return rol_excedente, rol_deficiente
        
        return None, None
    
    def reasignar_roles(self):
        """Reasigna roles según el equilibrio necesario"""
        rol_excedente, rol_deficiente = self.identificar_desequilibrio()
        
        if rol_excedente and rol_deficiente:
            # Buscar una abeja del rol excedente para cambiar
            for id_abeja, abeja in self.abejas_activas.items():
                if abeja.rol == rol_excedente:
                    # Cambiar el rol de esta abeja
                    abeja.cambiar_rol(rol_deficiente)
                    return True
        
        return False
    
    def procesar_mensaje(self, mensaje):
        """Procesa un mensaje recibido de una abeja"""
        if not mensaje:
            return
        
        tipo = mensaje.get("tipo")
        id_abeja = mensaje.get("id")
        rol = mensaje.get("rol")
        
        if tipo == "muerte":
            # Una abeja ha muerto, eliminar y reemplazar
            if id_abeja in self.abejas_activas:
                del self.abejas_activas[id_abeja]
            self.reemplazar_abeja_muerta(rol)
        
        elif tipo == "inactiva" and rol == "almacenadora":
            # Almacenadoras sin trabajo, posible conversión a recolectoras
            if self.colmena.contador_global["nectar_recolectado"] > 0:
                # Solo cambiar si ya hay producción (no al inicio)
                abeja = self.abejas_activas.get(id_abeja)
                if abeja:
                    abeja.cambiar_rol("recolectora")
        
        elif tipo == "falta_alimento" and rol == "nodriza":
            # Falta néctar para alimentar larvas, necesitamos más recolectoras
            self.colmena.enviar_mensaje_reina({
                "tipo": "necesidad_nectar"
            })
    
    def trabajar(self):
        """Monitorea la colmena y realiza ajustes según sea necesario"""
        # Procesar mensajes de las abejas
        mensaje = self.colmena.obtener_mensaje_reina(timeout=0.1)
        if mensaje:
            self.procesar_mensaje(mensaje)
        
        # Periódicamente revisar equilibrio y reasignar roles
        if random.random() < 0.2:  # 20% de probabilidad cada ciclo
            self.reasignar_roles()
        
        # Recolectar métricas periódicamente
        if random.random() < 0.1:  # 10% de probabilidad
            metricas = self.colmena.obtener_metricas()