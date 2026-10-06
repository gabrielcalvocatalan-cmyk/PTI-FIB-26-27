# Prácticas de PTI – FIB (UPC)

Prácticas de laboratorio de **Projecte de Tecnologies de la Informació (PTI)**, asignatura del Grau en Enginyeria Informàtica (especialidad de Tecnologies de la Informació) de la Facultat d'Informàtica de Barcelona, curso 2026-2027.

Cada carpeta contiene el código de una práctica y su informe en PDF.

## Prácticas

| Carpeta | Práctica | Tecnologías |
|---|---|---|
| `01-web-api` | API REST de alquiler de coches (carrental) | Python, Flask, Docker |
| `02-microservicios-kubernetes` | Despliegue de la API como microservicio con réplicas, Ingress y autoescalado (HPA) | Docker, Kubernetes, Minikube |
| `03-ml-federated-learning` | Entrenamiento federado de un modelo de detección de neumonía y su integración en una aplicación web | TensorFlow/Keras, Flask |
| `04-agentes-ia` | Chatbot con RAG, chatbot con MCP y red de agentes con identidades DID y credenciales verificables | Ollama, LangChain, MCP, DID, VC |

### 01 · Web API
API con dos endpoints: registrar un nuevo alquiler (calcula el precio total) y listar todos los alquileres guardados en JSON. Empaquetada con Docker.

### 02 · Microservicios con Kubernetes
Despliegue de la API en Minikube con 3 réplicas, inspección desde el Dashboard, gestión mediante manifests YAML, exposición con Ingress (`carrental.local`) y autoescalado horizontal según el uso de CPU, probado con carga generada con `hey`.

### 03 · Machine Learning con federated learning
Red de un servidor agregador y tres clientes que entrenan una CNN con el dataset Chest X-Ray sin compartir los datos, solo los pesos del modelo. El modelo resultante se integra en una aplicación web que clasifica radiografías en *normal* o *pneumonia*.

### 04 · Agentes de IA
- **RAG:** chatbot con un LLM local (Ollama) que responde sobre un dataset de alquileres; comparación entre modelos y entre CSV y PDF.
- **MCP:** chatbot con herramientas externas, incluida una herramienta propia que consulta terremotos en tiempo real (API del USGS).
- **Red de agentes de confianza:** agentes independientes con identidad `did:web`, credenciales verificables firmadas por un *trust anchor* y un orquestador que verifica la credencial antes de cada llamada.

## Cómo ejecutar
Cada práctica tiene sus propias dependencias. En general:

```bash
cd <carpeta-de-la-practica>
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Los pasos concretos están en el README de cada carpeta y en el informe.

> Los datasets grandes (como Chest X-Ray), los modelos entrenados y los entornos virtuales no se incluyen en el repositorio.

## Créditos
El código base de las prácticas lo proporciona el profesorado de PTI (FIB-UPC). Las modificaciones, extensiones e informes son de elaboración propia.

**Autor:** Gabriel Calvo Catalán
