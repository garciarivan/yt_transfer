# Cómo obtener credenciales para la API de YouTube

Para utilizar este programa, necesitarás crear un proyecto en Google Cloud Console y habilitar la API de YouTube Data v3. Sigue estos pasos para obtener las credenciales necesarias:

## 1. Crear un proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Inicia sesión con tu cuenta de Google
3. Haz clic en "Seleccionar un proyecto" en la parte superior de la página
4. Haz clic en "Nuevo proyecto"
5. Asigna un nombre al proyecto (por ejemplo, "Transferencia de YouTube")
6. Haz clic en "Crear"

## 2. Habilitar la API de YouTube Data v3

1. En el menú de navegación, ve a "APIs y servicios" > "Biblioteca"
2. Busca "YouTube Data API v3"
3. Haz clic en la API y luego en "Habilitar"

## 3. Crear credenciales OAuth 2.0

1. En el menú de navegación, ve a "APIs y servicios" > "Credenciales"
2. Haz clic en "Crear credenciales" y selecciona "ID de cliente de OAuth"
3. Si es la primera vez que creas credenciales OAuth, deberás configurar la pantalla de consentimiento:
   - Selecciona "Externo" como tipo de usuario
   - Completa la información requerida (nombre de la aplicación, correo electrónico, etc.)
   - En "Ámbitos", añade el ámbito: `https://www.googleapis.com/auth/youtube.force-ssl`
   - Guarda y continúa
4. Para el tipo de aplicación, selecciona "Aplicación de escritorio"
5. Asigna un nombre a la aplicación (por ejemplo, "Transferencia de YouTube")
6. Haz clic en "Crear"

## 4. Descargar el archivo de credenciales

1. Se mostrará una ventana con el ID de cliente y el secreto de cliente
2. Haz clic en "Descargar JSON"
3. Renombra el archivo descargado a `client_secrets.json`
4. Coloca este archivo en el mismo directorio que el script `yt_transfer.py`

## 5. Verificar el estado de la API

1. En el menú de navegación, ve a "APIs y servicios" > "Panel"
2. Verifica que la API de YouTube Data v3 esté habilitada
3. Puedes ver las cuotas disponibles en la sección "Cuotas"

## Notas importantes

- La API de YouTube tiene límites de cuota. Por defecto, tienes 10,000 unidades por día.
- Cada operación de suscripción consume 50 unidades, lo que significa que puedes transferir aproximadamente 200 suscripciones por día con la cuota predeterminada.
- Si necesitas transferir más suscripciones, puedes solicitar un aumento de cuota en la sección "APIs y servicios" > "Cuotas".

## Solución de problemas

### Error: "Acceso bloqueado: Transferencia de Youtube no ha completado el proceso de verificación de Google"

Si recibes este error (Error 403: access_denied), significa que tu aplicación está en modo de prueba y no ha sido verificada por Google. Para solucionarlo, tienes varias opciones:

#### Opción 1: Añadirte como usuario de prueba (Recomendada)

1. Ve a la [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a "APIs y servicios" > "Pantalla de consentimiento de OAuth"
4. En la sección "Usuarios de prueba", añade tu correo electrónico
5. Guarda los cambios
6. Regenera el archivo client_secrets.json si es necesario
7. Ejecuta nuevamente el script

#### Opción 2: Configurar la aplicación solo para uso personal

Si solo vas a usar esta aplicación tú mismo y tienes una cuenta de Google Workspace:

1. Ve a la [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a "APIs y servicios" > "Pantalla de consentimiento de OAuth"
4. Cambia el tipo de usuario a "Interno"
   - Esto limitará el uso a personas dentro de tu organización
   - No requiere verificación de Google

#### Opción 3: Completar el proceso de verificación

Si planeas distribuir la aplicación a otros usuarios:

1. Ve a la [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a "APIs y servicios" > "Pantalla de consentimiento de OAuth"
4. Completa toda la información requerida (política de privacidad, términos de servicio, etc.)
5. Envía la aplicación para verificación

**Nota importante**: Para uso personal, la Opción 1 es la más rápida y sencilla. 