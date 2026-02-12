# SISLAB - Sistema de Gestión de Laboratorios Distribuidos

Sistema de alta disponibilidad para la gestión de inventarios y mantenimiento de laboratorios universitarios. Implementa una arquitectura de microservicios tolerante a fallos, utilizando balanceo de carga y replicación.

## 🚀 Arquitectura Tecnológica
* **Frontend:** React + Vite + Material UI (Ejecución Local)
* **Load Balancer:** Nginx (Proxy Inverso & Round Robin)
* **Backend Cluster:** 3 Réplicas de FastAPI (Python)
* **Auth DB:** MySQL 8.0 (Persistencia Relacional)
* **Inventory DB:** MongoDB (Persistencia NoSQL)
* **Status Monitor:** Redis (Heartbeat & Caché)
* **Stress Testing:** K6 (Pruebas de Carga)

## 📋 Requisitos Previos
* **Docker Desktop:** Instalado y corriendo.
* **Node.js:** v18 o superior.
* **Git:** Para control de versiones.
* **Puertos Libres:** 8001 (API Gateway), 5173 (Frontend), 3306, 27018, 6379.

## ⚙️ Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <TU_URL_DEL_REPO>
cd laboratorios