# Transferencia de Suscripciones de YouTube

Esta herramienta permite transferir automáticamente elementos de una cuenta de YouTube antigua a una nueva cuenta, incluyendo suscripciones, listas de reproducción y videos con "Me gusta".

## Características

- Obtiene todas las suscripciones de la cuenta de origen
- Suscribe automáticamente a los mismos canales en la cuenta de destino
- Transfiere listas de reproducción completas con todos sus videos
- Transfiere los videos marcados con "Me gusta"
- Proporciona un registro detallado del proceso
- Maneja la autenticación OAuth 2.0 para ambas cuentas
- Interfaz de menú para seleccionar qué transferir
- Verifica si ya estás suscrito a un canal antes de intentar suscribirte nuevamente

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

El programa te mostrará un menú con las siguientes opciones:
1. Transferir suscripciones
2. Transferir videos con 'Me gusta'
3. Transferir listas de reproducción
4. Transferir todo
5. Salir

Selecciona la opción deseada y el programa te guiará a través del proceso de autenticación para ambas cuentas y realizará la transferencia de los elementos seleccionados.

## Limitaciones

- La API de YouTube tiene cuotas diarias que pueden limitar el número de operaciones que se pueden realizar en un día
- Se requiere autorización manual para ambas cuentas
- No es posible transferir el historial de visualizaciones directamente a través de la API pública
- Las listas de reproducción se crean como privadas en la cuenta de destino

## Solución de problemas

### Error: "Acceso bloqueado: Transferencia de Youtube no ha completado el proceso de verificación de Google"

Si recibes este error durante la autenticación, significa que tu aplicación está en modo de prueba y necesitas añadir tu correo electrónico como usuario de prueba en la Google Cloud Console.

Para resolver este problema:

1. Ve a la [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a "APIs y servicios" > "Pantalla de consentimiento de OAuth"
4. En la sección "Usuarios de prueba", añade tu correo electrónico
5. Guarda los cambios
6. Ejecuta nuevamente el script

Para instrucciones más detalladas, consulta la sección "Solución de problemas" en el archivo [INSTRUCCIONES_API.md](INSTRUCCIONES_API.md). 