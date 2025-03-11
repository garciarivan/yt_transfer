#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transferencia de Suscripciones de YouTube
Este script permite transferir automáticamente todas las suscripciones
de una cuenta de YouTube antigua a una nueva cuenta.
"""

import os
import pickle
import time
from tqdm import tqdm
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request

# Constantes
CLIENT_SECRETS_FILE = 'client_secrets.json'
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# Archivos para almacenar las credenciales
SOURCE_TOKEN_PICKLE = 'source_token.pickle'
TARGET_TOKEN_PICKLE = 'target_token.pickle'

def get_authenticated_service(token_pickle, is_source=True):
    """
    Crea un servicio autenticado de la API de YouTube.
    
    Args:
        token_pickle: Ruta al archivo pickle para almacenar/cargar credenciales
        is_source: Indica si es la cuenta de origen (True) o destino (False)
    
    Returns:
        Un objeto de servicio autenticado para la API de YouTube
    """
    credentials = None
    
    # Cargar credenciales desde el archivo pickle si existe
    if os.path.exists(token_pickle):
        with open(token_pickle, 'rb') as token:
            credentials = pickle.load(token)
    
    # Si no hay credenciales válidas, solicitar al usuario que se autentique
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            account_type = "origen" if is_source else "destino"
            print(f"\nNecesitas autenticarte con tu cuenta de {account_type}.")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
        
        # Guardar las credenciales para la próxima ejecución
        with open(token_pickle, 'wb') as token:
            pickle.dump(credentials, token)
    
    # Construir el servicio
    return googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

def get_subscriptions(youtube):
    """
    Obtiene todas las suscripciones de la cuenta.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
    
    Returns:
        Lista de IDs de canales a los que está suscrito el usuario
    """
    subscriptions = []
    next_page_token = None
    
    print("Obteniendo suscripciones...")
    
    while True:
        request = youtube.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            channel_id = item['snippet']['resourceId']['channelId']
            channel_title = item['snippet']['title']
            subscriptions.append({
                'id': channel_id,
                'title': channel_title
            })
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return subscriptions

def subscribe_to_channels(youtube, subscriptions):
    """
    Suscribe a la cuenta a los canales especificados.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        subscriptions: Lista de diccionarios con IDs y títulos de canales
    
    Returns:
        Tupla con el número de suscripciones exitosas y fallidas
    """
    success_count = 0
    failed_count = 0
    failed_channels = []
    
    print(f"\nTransfiriendo {len(subscriptions)} suscripciones a la nueva cuenta...")
    
    for channel in tqdm(subscriptions):
        try:
            youtube.subscriptions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": channel['id']
                        }
                    }
                }
            ).execute()
            success_count += 1
            
            # Pausa para evitar exceder la cuota de la API
            time.sleep(0.5)
            
        except googleapiclient.errors.HttpError as e:
            failed_count += 1
            failed_channels.append({
                'title': channel['title'],
                'id': channel['id'],
                'error': str(e)
            })
            
            # Si es un error de cuota, esperar más tiempo
            if "quotaExceeded" in str(e):
                print("\nSe ha excedido la cuota de la API. Esperando 60 segundos...")
                time.sleep(60)
    
    return success_count, failed_count, failed_channels

def main():
    """Función principal del programa."""
    print("=== Transferencia de Suscripciones de YouTube ===\n")
    
    # Verificar si existe el archivo de credenciales
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"Error: No se encontró el archivo {CLIENT_SECRETS_FILE}")
        print("Por favor, descarga tus credenciales de la API de Google y guárdalas como 'client_secrets.json'")
        return
    
    try:
        # Autenticar con la cuenta de origen
        print("Paso 1: Autenticación con la cuenta de origen")
        youtube_source = get_authenticated_service(SOURCE_TOKEN_PICKLE, is_source=True)
        
        # Obtener suscripciones de la cuenta de origen
        print("\nPaso 2: Obteniendo suscripciones de la cuenta de origen")
        subscriptions = get_subscriptions(youtube_source)
        print(f"Se encontraron {len(subscriptions)} suscripciones")
        
        # Autenticar con la cuenta de destino
        print("\nPaso 3: Autenticación con la cuenta de destino")
        youtube_target = get_authenticated_service(TARGET_TOKEN_PICKLE, is_source=False)
        
        # Transferir suscripciones a la cuenta de destino
        print("\nPaso 4: Transfiriendo suscripciones a la cuenta de destino")
        success_count, failed_count, failed_channels = subscribe_to_channels(youtube_target, subscriptions)
        
        # Mostrar resultados
        print("\n=== Resultados de la transferencia ===")
        print(f"Total de suscripciones: {len(subscriptions)}")
        print(f"Suscripciones transferidas exitosamente: {success_count}")
        print(f"Suscripciones fallidas: {failed_count}")
        
        # Mostrar canales que fallaron
        if failed_count > 0:
            print("\nCanales que no pudieron ser transferidos:")
            for channel in failed_channels:
                print(f"- {channel['title']} (ID: {channel['id']})")
                print(f"  Error: {channel['error']}")
        
        print("\n¡Transferencia completada!")
        
    except Exception as e:
        print(f"\nError inesperado: {str(e)}")

if __name__ == "__main__":
    main() 