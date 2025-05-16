# Simulación Concurrente de una Colmena Inteligente 🐝

Este proyecto simula una colmena inteligente en la que abejas con distintos roles (obreras, exploradoras, soldados, reina, etc.) cooperan en un entorno concurrente. Se desarrolla en el contexto de la asignatura de Programación Paralela y Distribuida.

## Objetivo

Simular el comportamiento cooperativo de una colmena, utilizando hilos (threads) o procesos para representar diferentes tipos de abejas con tareas específicas, gestionando correctamente la concurrencia y la sincronización.

## Funcionalidades

- **Exploradoras**: buscan nuevas fuentes de néctar.
- **Recolectoras**: recogen néctar y lo almacenan en la colmena.
- **Soldados**: defienden la colmena frente a amenazas.
- **Reina**: supervisa y mantiene el equilibrio del ecosistema.
- **Distribución dinámica de tareas** mediante recursos compartidos y estructuras de control de concurrencia.

## Tecnologías

- Python 3
- Módulo `threading` y/o `multiprocessing`
- Estructuras de sincronización (locks, semáforos, colas)

## Ejecución

```bash
python colmena.py
