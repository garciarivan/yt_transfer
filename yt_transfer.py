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

def is_already_subscribed(youtube, channel_id):
    """
    Verifica si el usuario ya está suscrito a un canal específico.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        channel_id: ID del canal a verificar
    
    Returns:
        True si ya está suscrito, False en caso contrario
    """
    try:
        # Buscar suscripciones que coincidan con el ID del canal
        request = youtube.subscriptions().list(
            part="snippet",
            mine=True,
            forChannelId=channel_id,
            maxResults=1
        )
        response = request.execute()
        
        # Si hay resultados, ya está suscrito
        return len(response.get('items', [])) > 0
    
    except googleapiclient.errors.HttpError:
        # En caso de error, asumimos que no está suscrito
        return False

def subscribe_to_channels(youtube, subscriptions):
    """
    Suscribe a la cuenta a los canales especificados.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        subscriptions: Lista de diccionarios con IDs y títulos de canales
    
    Returns:
        Tupla con el número de suscripciones exitosas, fallidas y ya existentes
    """
    success_count = 0
    failed_count = 0
    already_subscribed_count = 0
    failed_channels = []
    
    print(f"\nTransfiriendo {len(subscriptions)} suscripciones a la nueva cuenta...")
    
    for channel in tqdm(subscriptions):
        try:
            # Verificar si ya está suscrito al canal
            if is_already_subscribed(youtube, channel['id']):
                already_subscribed_count += 1
                print(f"\nYa estás suscrito a: {channel['title']}")
                continue
            
            # Si no está suscrito, realizar la suscripción
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
    
    return success_count, failed_count, already_subscribed_count, failed_channels

def get_liked_videos(youtube):
    """
    Obtiene todos los videos con "Me gusta" de la cuenta.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
    
    Returns:
        Lista de diccionarios con información de los videos con "Me gusta"
    """
    liked_videos = []
    next_page_token = None
    
    print("Obteniendo videos con 'Me gusta'...")
    
    while True:
        request = youtube.videos().list(
            part="snippet",
            myRating="like",
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            video_id = item['id']
            video_title = item['snippet']['title']
            liked_videos.append({
                'id': video_id,
                'title': video_title
            })
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return liked_videos

def is_video_liked(youtube, video_id):
    """
    Verifica si un video ya tiene "Me gusta" en la cuenta.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        video_id: ID del video a verificar
    
    Returns:
        True si el video ya tiene "Me gusta", False en caso contrario
    """
    try:
        request = youtube.videos().getRating(
            id=video_id
        )
        response = request.execute()
        
        # Verificar si el video tiene "Me gusta"
        for item in response['items']:
            if item['videoId'] == video_id and item['rating'] == 'like':
                return True
        
        return False
    
    except googleapiclient.errors.HttpError:
        # En caso de error, asumimos que no tiene "Me gusta"
        return False

def like_videos(youtube, videos):
    """
    Marca como "Me gusta" los videos especificados.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        videos: Lista de diccionarios con IDs y títulos de videos
    
    Returns:
        Tupla con el número de operaciones exitosas, fallidas y ya existentes
    """
    success_count = 0
    failed_count = 0
    already_liked_count = 0
    failed_videos = []
    
    print(f"\nTransfiriendo {len(videos)} videos con 'Me gusta' a la nueva cuenta...")
    
    for video in tqdm(videos):
        try:
            # Verificar si el video ya tiene "Me gusta"
            if is_video_liked(youtube, video['id']):
                already_liked_count += 1
                print(f"\nYa has marcado con 'Me gusta' el video: {video['title']}")
                continue
            
            # Si no tiene "Me gusta", marcarlo
            youtube.videos().rate(
                id=video['id'],
                rating="like"
            ).execute()
            success_count += 1
            
            # Pausa para evitar exceder la cuota de la API
            time.sleep(0.5)
            
        except googleapiclient.errors.HttpError as e:
            failed_count += 1
            failed_videos.append({
                'title': video['title'],
                'id': video['id'],
                'error': str(e)
            })
            
            # Si es un error de cuota, esperar más tiempo
            if "quotaExceeded" in str(e):
                print("\nSe ha excedido la cuota de la API. Esperando 60 segundos...")
                time.sleep(60)
    
    return success_count, failed_count, already_liked_count, failed_videos

def get_playlists(youtube):
    """
    Obtiene todas las listas de reproducción de la cuenta.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
    
    Returns:
        Lista de diccionarios con información de las listas de reproducción
    """
    playlists = []
    next_page_token = None
    
    print("Obteniendo listas de reproducción...")
    
    while True:
        request = youtube.playlists().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            playlist_id = item['id']
            playlist_title = item['snippet']['title']
            playlist_description = item['snippet'].get('description', '')
            playlists.append({
                'id': playlist_id,
                'title': playlist_title,
                'description': playlist_description
            })
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return playlists

def find_playlist_by_title(youtube, title):
    """
    Busca una lista de reproducción por su título.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        title: Título de la lista de reproducción a buscar
    
    Returns:
        ID de la lista de reproducción si existe, None en caso contrario
    """
    playlists = get_playlists(youtube)
    
    for playlist in playlists:
        if playlist['title'] == title:
            return playlist['id']
    
    return None

def get_playlist_items(youtube, playlist_id):
    """
    Obtiene todos los videos de una lista de reproducción.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        playlist_id: ID de la lista de reproducción
    
    Returns:
        Lista de diccionarios con información de los videos
    """
    playlist_items = []
    next_page_token = None
    
    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            video_id = item['contentDetails']['videoId']
            video_title = item['snippet']['title']
            playlist_items.append({
                'id': video_id,
                'title': video_title
            })
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return playlist_items

def is_video_in_playlist(youtube, playlist_id, video_id):
    """
    Verifica si un video ya está en una lista de reproducción.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        playlist_id: ID de la lista de reproducción
        video_id: ID del video a verificar
    
    Returns:
        True si el video ya está en la lista, False en caso contrario
    """
    try:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            videoId=video_id,
            maxResults=1
        )
        response = request.execute()
        
        return len(response.get('items', [])) > 0
    
    except googleapiclient.errors.HttpError:
        # En caso de error, asumimos que no está en la lista
        return False

def create_playlist(youtube, title, description=''):
    """
    Crea una nueva lista de reproducción.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        title: Título de la lista de reproducción
        description: Descripción de la lista de reproducción
    
    Returns:
        ID de la lista de reproducción creada
    """
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description
            },
            "status": {
                "privacyStatus": "private"
            }
        }
    )
    response = request.execute()
    
    return response['id']

def add_video_to_playlist(youtube, playlist_id, video_id):
    """
    Añade un video a una lista de reproducción.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        playlist_id: ID de la lista de reproducción
        video_id: ID del video
    
    Returns:
        True si se añadió correctamente, False en caso contrario
    """
    try:
        # Verificar si el video ya está en la lista
        if is_video_in_playlist(youtube, playlist_id, video_id):
            return False
        
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        return True
    except googleapiclient.errors.HttpError:
        return False

def transfer_playlists(youtube_source, youtube_target):
    """
    Transfiere todas las listas de reproducción de una cuenta a otra.
    
    Args:
        youtube_source: Servicio autenticado de la API de YouTube (cuenta origen)
        youtube_target: Servicio autenticado de la API de YouTube (cuenta destino)
    
    Returns:
        Tupla con estadísticas de la transferencia
    """
    # Obtener listas de reproducción de la cuenta de origen
    playlists = get_playlists(youtube_source)
    
    if not playlists:
        print("No se encontraron listas de reproducción para transferir.")
        return 0, 0, 0, 0, []
    
    print(f"Se encontraron {len(playlists)} listas de reproducción.")
    
    success_count = 0
    failed_count = 0
    already_exists_count = 0
    video_count = 0
    failed_playlists = []
    
    # Transferir cada lista de reproducción
    for playlist in tqdm(playlists):
        try:
            # Verificar si ya existe una lista con el mismo nombre
            existing_playlist_id = find_playlist_by_title(youtube_target, playlist['title'])
            
            if existing_playlist_id:
                print(f"\nYa existe una lista de reproducción con el nombre '{playlist['title']}'")
                already_exists_count += 1
                
                # Obtener videos de la lista de reproducción original
                playlist_items = get_playlist_items(youtube_source, playlist['id'])
                
                # Añadir videos a la lista existente
                videos_added = 0
                for item in playlist_items:
                    if add_video_to_playlist(youtube_target, existing_playlist_id, item['id']):
                        videos_added += 1
                        video_count += 1
                        # Pausa para evitar exceder la cuota de la API
                        time.sleep(0.5)
                
                print(f"Se añadieron {videos_added} videos a la lista existente '{playlist['title']}'")
                success_count += 1
                continue
            
            # Crear nueva lista de reproducción en la cuenta de destino
            new_playlist_id = create_playlist(
                youtube_target, 
                playlist['title'], 
                playlist['description']
            )
            
            # Obtener videos de la lista de reproducción original
            playlist_items = get_playlist_items(youtube_source, playlist['id'])
            
            # Añadir videos a la nueva lista de reproducción
            videos_added = 0
            for item in playlist_items:
                if add_video_to_playlist(youtube_target, new_playlist_id, item['id']):
                    videos_added += 1
                    video_count += 1
                    # Pausa para evitar exceder la cuota de la API
                    time.sleep(0.5)
            
            success_count += 1
            print(f"\nLista de reproducción '{playlist['title']}' transferida con {videos_added} videos.")
            
        except googleapiclient.errors.HttpError as e:
            failed_count += 1
            failed_playlists.append({
                'title': playlist['title'],
                'id': playlist['id'],
                'error': str(e)
            })
            
            # Si es un error de cuota, esperar más tiempo
            if "quotaExceeded" in str(e):
                print("\nSe ha excedido la cuota de la API. Esperando 60 segundos...")
                time.sleep(60)
    
    return success_count, failed_count, already_exists_count, video_count, failed_playlists

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
        
        # Autenticar con la cuenta de destino
        print("\nPaso 2: Autenticación con la cuenta de destino")
        youtube_target = get_authenticated_service(TARGET_TOKEN_PICKLE, is_source=False)
        
        # Menú de opciones
        while True:
            print("\n=== Menú de Transferencia ===")
            print("1. Transferir suscripciones")
            print("2. Transferir videos con 'Me gusta'")
            print("3. Transferir listas de reproducción")
            print("4. Transferir todo")
            print("5. Salir")
            
            opcion = input("\nSelecciona una opción (1-5): ")
            
            if opcion == "1":
                # Transferir suscripciones
                print("\n=== Transferencia de Suscripciones ===")
                subscriptions = get_subscriptions(youtube_source)
                print(f"Se encontraron {len(subscriptions)} suscripciones")
                
                success_count, failed_count, already_subscribed_count, failed_channels = subscribe_to_channels(youtube_target, subscriptions)
                
                # Mostrar resultados
                print("\n=== Resultados de la transferencia de suscripciones ===")
                print(f"Total de suscripciones: {len(subscriptions)}")
                print(f"Suscripciones transferidas exitosamente: {success_count}")
                print(f"Suscripciones ya existentes: {already_subscribed_count}")
                print(f"Suscripciones fallidas: {failed_count}")
                
                # Mostrar canales que fallaron
                if failed_count > 0:
                    print("\nCanales que no pudieron ser transferidos:")
                    for channel in failed_channels:
                        print(f"- {channel['title']} (ID: {channel['id']})")
                        print(f"  Error: {channel['error']}")
            
            elif opcion == "2":
                # Transferir videos con "Me gusta"
                print("\n=== Transferencia de Videos con 'Me gusta' ===")
                liked_videos = get_liked_videos(youtube_source)
                print(f"Se encontraron {len(liked_videos)} videos con 'Me gusta'")
                
                success_count, failed_count, already_liked_count, failed_videos = like_videos(youtube_target, liked_videos)
                
                # Mostrar resultados
                print("\n=== Resultados de la transferencia de videos con 'Me gusta' ===")
                print(f"Total de videos: {len(liked_videos)}")
                print(f"Videos marcados exitosamente: {success_count}")
                print(f"Videos ya marcados anteriormente: {already_liked_count}")
                print(f"Videos fallidos: {failed_count}")
                
                # Mostrar videos que fallaron
                if failed_count > 0:
                    print("\nVideos que no pudieron ser marcados:")
                    for video in failed_videos:
                        print(f"- {video['title']} (ID: {video['id']})")
                        print(f"  Error: {video['error']}")
            
            elif opcion == "3":
                # Transferir listas de reproducción
                print("\n=== Transferencia de Listas de Reproducción ===")
                
                success_count, failed_count, already_exists_count, video_count, failed_playlists = transfer_playlists(youtube_source, youtube_target)
                
                # Mostrar resultados
                print("\n=== Resultados de la transferencia de listas de reproducción ===")
                print(f"Listas de reproducción transferidas exitosamente: {success_count}")
                print(f"Listas de reproducción ya existentes: {already_exists_count}")
                print(f"Videos añadidos a listas de reproducción: {video_count}")
                print(f"Listas de reproducción fallidas: {failed_count}")
                
                # Mostrar listas que fallaron
                if failed_count > 0:
                    print("\nListas de reproducción que no pudieron ser transferidas:")
                    for playlist in failed_playlists:
                        print(f"- {playlist['title']} (ID: {playlist['id']})")
                        print(f"  Error: {playlist['error']}")
            
            elif opcion == "4":
                # Transferir todo
                print("\n=== Transferencia Completa ===")
                
                # Transferir suscripciones
                print("\n--- Transferencia de Suscripciones ---")
                subscriptions = get_subscriptions(youtube_source)
                print(f"Se encontraron {len(subscriptions)} suscripciones")
                
                sub_success, sub_failed, sub_existing, failed_channels = subscribe_to_channels(youtube_target, subscriptions)
                
                # Transferir videos con "Me gusta"
                print("\n--- Transferencia de Videos con 'Me gusta' ---")
                liked_videos = get_liked_videos(youtube_source)
                print(f"Se encontraron {len(liked_videos)} videos con 'Me gusta'")
                
                like_success, like_failed, like_existing, failed_videos = like_videos(youtube_target, liked_videos)
                
                # Transferir listas de reproducción
                print("\n--- Transferencia de Listas de Reproducción ---")
                
                playlist_success, playlist_failed, playlist_existing, video_count, failed_playlists = transfer_playlists(youtube_source, youtube_target)
                
                # Mostrar resultados generales
                print("\n=== Resultados de la transferencia completa ===")
                print(f"Suscripciones transferidas: {sub_success} (de {len(subscriptions)})")
                print(f"Suscripciones ya existentes: {sub_existing}")
                print(f"Videos con 'Me gusta' transferidos: {like_success} (de {len(liked_videos)})")
                print(f"Videos con 'Me gusta' ya existentes: {like_existing}")
                print(f"Listas de reproducción transferidas: {playlist_success}")
                print(f"Listas de reproducción ya existentes: {playlist_existing}")
                print(f"Videos añadidos a listas de reproducción: {video_count}")
            
            elif opcion == "5":
                # Salir
                print("\n¡Gracias por usar el programa de transferencia de YouTube!")
                break
            
            else:
                print("\nOpción no válida. Por favor, selecciona una opción del 1 al 5.")
        
    except Exception as e:
        print(f"\nError inesperado: {str(e)}")

if __name__ == "__main__":
    main() 