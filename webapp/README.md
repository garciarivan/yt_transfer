# Aplicación Web para Transferencia de Suscripciones de YouTube

Esta aplicación web permite transferir automáticamente todas las suscripciones de una cuenta de YouTube antigua a una nueva cuenta.

## Características

- Interfaz web amigable y responsive
- Autenticación OAuth con Google para acceder a las cuentas de YouTube
- Transferencia automática de suscripciones
- Manejo de errores y límites de la API de YouTube

## Requisitos

- Python 3.7 o superior
- Credenciales de la API de YouTube (client_secrets.json)
- Navegador web moderno

## Instalación

1. Clona este repositorio o descarga los archivos

2. Instala las dependencias:
```
pip install -r requirements.txt
```

3. Configura las credenciales de la API de YouTube:
   - Crea un proyecto en la [Google Developer Console](https://console.developers.google.com/)
   - Habilita la API de YouTube Data v3
   - Crea credenciales OAuth 2.0
   - Descarga el archivo JSON de credenciales y renómbralo como `client_secrets.json`
   - Coloca el archivo en el directorio raíz de la aplicación

## Uso

1. Inicia la aplicación:
```
python app.py
```

2. Abre tu navegador y ve a `http://localhost:5000`

3. Sigue los pasos en la interfaz:
   - Autenticar la cuenta de origen (donde están tus suscripciones actuales)
   - Autenticar la cuenta de destino (donde quieres transferir las suscripciones)
   - Iniciar la transferencia

## Despliegue en producción

Para desplegar esta aplicación en un entorno de producción:

1. Configura una variable de entorno para la clave secreta:
```
export SECRET_KEY="tu_clave_secreta_segura"
```

2. Usa un servidor WSGI como Gunicorn:
```
gunicorn app:app
```

3. Considera usar un proxy inverso como Nginx para servir la aplicación

## Limitaciones

- La API de YouTube tiene cuotas diarias que pueden limitar el número de suscripciones que se pueden transferir en un día
- El proceso de autenticación requiere acceso a un navegador web

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles. 