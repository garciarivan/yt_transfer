# Transferencia de Suscripciones de YouTube

Esta herramienta permite transferir automáticamente todas las suscripciones de una cuenta de YouTube antigua a una nueva cuenta.

## Características

- Obtiene todas las suscripciones de la cuenta de origen
- Suscribe automáticamente a los mismos canales en la cuenta de destino
- Proporciona un registro detallado del proceso
- Maneja la autenticación OAuth 2.0 para ambas cuentas

## Requisitos

- Python 3.6 o superior
- Credenciales de API de Google (archivo client_secrets.json)
- Acceso a ambas cuentas de YouTube

## Instalación

1. Clona este repositorio o descarga los archivos
2. Instala las dependencias:

```
pip install -r requirements.txt
```

3. Configura las credenciales de la API de Google:
   - Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
   - Habilita la API de YouTube Data v3
   - Crea credenciales OAuth 2.0 y descarga el archivo client_secrets.json
   - Coloca el archivo client_secrets.json en el directorio del proyecto

## Uso

```
python yt_transfer.py
```

El programa te guiará a través del proceso de autenticación para ambas cuentas y realizará la transferencia de suscripciones.

## Limitaciones

- La API de YouTube tiene cuotas diarias que pueden limitar el número de suscripciones que se pueden transferir en un día
- Se requiere autorización manual para ambas cuentas 