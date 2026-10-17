# Prácticas de PTI – FIB (UPC)

Prácticas de laboratorio de **Projecte de Tecnologies de la Informació (PTI)**, asignatura del Grau en Enginyeria Informàtica (especialidad de Tecnologies de la Informació) de la Facultat d'Informàtica de Barcelona, curso 2026-2027.

Cada carpeta contiene el código de una práctica y su informe en PDF.

## Prácticas

| Carpeta | Práctica | Tecnologías |
|---|---|---|
| `1.REST_API` | API REST de alquiler de coches (carrental) | Python, Flask, Docker |
| `2.Agents_lab` | Chatbot con RAG, chatbot con MCP y red de agentes con identidades DID y credenciales verificables | Ollama, LangChain, MCP, DID, VC |
| `3.Microservices` | Despliegue de la API como microservicio con réplicas, Ingress y autoescalado (HPA) | Docker, Kubernetes, Minikube |
| `4.Blockchain` | Blockchain simplificada con Proof-of-Work, consenso entre dos nodos y endpoints para listar nodos, validar y manipular la cadena | Python, Flask, curl |
| `5.MLBA` | Entrenamiento federado de un modelo de detección de neumonía y su integración en una aplicación web | TensorFlow/Keras, Flask |

### 1 · REST API
API con dos endpoints: registrar un nuevo alquiler (calcula el precio total) y listar todos los alquileres guardados en JSON. Empaquetada con Docker.

### 2 · Agents lab
- **RAG:** chatbot con un LLM local (Ollama) que responde sobre un dataset de alquileres; comparación entre modelos y entre CSV y PDF.
- **MCP:** chatbot con herramientas externas, incluida una herramienta propia que consulta terremotos en tiempo real (API del USGS).
- **Red de agentes de confianza:** agentes independientes con identidad `did:web`, credenciales verificables firmadas por un *trust anchor* y un orquestador que verifica la credencial antes de cada llamada.

### 3 · Microservices
Despliegue de la API en Minikube con 3 réplicas, inspección desde el Dashboard, gestión mediante manifests YAML, exposición con Ingress (`carrental.local`) y autoescalado horizontal según el uso de CPU, probado con carga generada con `hey`.

### 4 · Blockchain
Blockchain simplificada accesible mediante una API web, con dos nodos (puertos 5000 y 5001):
- **Transacciones y minado:** alta de transacciones y minado de bloques con Proof-of-Work (hash SHA-256 que empieza por cuatro ceros), con recompensa para el nodo minero.
- **Consenso:** registro mutuo de nodos y resolución de conflictos adoptando la cadena válida más larga. Toda la secuencia se automatiza en `script.sh`.
- **Nuevos endpoints:** `/nodes/list` (nodos registrados), `/validate` (comprueba la cadena de hashes) y `/nodes/manipulate` (altera un bloque para que la validación falle y el consenso rechace la cadena).
- **Informe:** alternativas al PoW (PoS, PoA), protección de las transacciones con firmas digitales, almacenamiento del estado de saldos y técnicas de privacidad (zk-SNARKs, commitments).

Realizada junto con Lucas Díaz López.

### 5 · MLBA (Machine Learning)
Red de un servidor agregador y tres clientes que entrenan una CNN con el dataset Chest X-Ray sin compartir los datos, solo los pesos del modelo. El modelo resultante se integra en una aplicación web que clasifica radiografías en *normal* o *pneumonia*.

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
