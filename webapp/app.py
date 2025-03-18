#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicación web para transferencia de suscripciones de YouTube
Esta aplicación permite transferir automáticamente todas las suscripciones
de una cuenta de YouTube antigua a una nueva cuenta.
"""

import os
import pickle
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request

# Configuración de la aplicación
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-predeterminada')
app.config['SESSION_TYPE'] = 'filesystem'

# Constantes
CLIENT_SECRETS_FILE = 'client_secrets.json'
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
PROFILE_SCOPES = ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']

# Archivos para almacenar las credenciales
SOURCE_TOKEN_PICKLE = 'source_token.pickle'
TARGET_TOKEN_PICKLE = 'target_token.pickle'

def get_authenticated_service(token_pickle, is_source=True, skip_api_check=False):
    """
    Crea un servicio autenticado de la API de YouTube.
    
    Args:
        token_pickle: Ruta al archivo pickle para almacenar/cargar credenciales
        is_source: Indica si es la cuenta de origen (True) o destino (False)
        skip_api_check: Si es True, solo autentica sin verificar la API (para evitar consumir cuota)
    
    Returns:
        Un objeto de servicio autenticado de la API de YouTube o None si skip_api_check es True
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
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
        
        # Guardar las credenciales para la próxima ejecución
        with open(token_pickle, 'wb') as token:
            pickle.dump(credentials, token)
    
    # Si solo queremos autenticar sin verificar la API, devolvemos None
    if skip_api_check:
        return None
    
    return googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

def get_user_info(youtube):
    """
    Obtiene información del usuario autenticado utilizando el servicio de YouTube API.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
    
    Returns:
        Diccionario con información del usuario o None en caso de error
    """
    try:
        # Obtenemos el ID del canal del usuario autenticado
        channel_request = youtube.channels().list(part="snippet", mine=True)
        channel_response = channel_request.execute()
        
        if not channel_response.get('items'):
            return None
        
        channel = channel_response['items'][0]
        
        return {
            'id': channel['id'],
            'name': channel['snippet']['title'],
            'picture': channel['snippet']['thumbnails'].get('default', {}).get('url', ''),
            'email': f"Canal de YouTube: {channel['snippet']['title']}"
        }
    except Exception as e:
        print(f"Error al obtener información del usuario desde YouTube API: {str(e)}")
        return None

def get_user_info_from_credentials(token_pickle):
    """
    Obtiene información básica del usuario a partir de las credenciales.
    
    Args:
        token_pickle: Ruta al archivo pickle con las credenciales
    
    Returns:
        Diccionario con información del usuario o None si no hay credenciales
    """
    if not os.path.exists(token_pickle):
        return None
    
    try:
        with open(token_pickle, 'rb') as token:
            credentials = pickle.load(token)
        
        # Verificar si las credenciales son válidas
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                return None
        
        # Primero, intentamos obtener la información del token ID
        if hasattr(credentials, 'id_token') and credentials.id_token:
            try:
                import jwt
                # Decodificar el token sin verificar la firma
                token_data = jwt.decode(credentials.id_token, options={"verify_signature": False})
                
                user_info = {
                    'email': token_data.get('email', 'Usuario autenticado'),
                    'name': token_data.get('name', 'Usuario'),
                    'picture': token_data.get('picture', ''),
                    'id': token_data.get('sub', '')
                }
                
                if user_info['picture']:
                    return user_info
            except Exception as e:
                print(f"Error al decodificar token ID: {str(e)}")
        
        # Si no pudimos obtener la información del token o no tiene imagen,
        # intentamos obtenerla a través de la API de YouTube
        try:
            youtube = googleapiclient.discovery.build(
                API_SERVICE_NAME, API_VERSION, credentials=credentials)
            yt_user_info = get_user_info(youtube)
            
            if yt_user_info:
                return yt_user_info
        except Exception as e:
            print(f"Error al obtener información del usuario desde YouTube API: {str(e)}")
        
        # Si todo lo demás falla, devolvemos información básica
        return {'name': 'Usuario autenticado', 'email': 'Cuenta conectada', 'picture': '', 'id': ''}
    
    except Exception as e:
        print(f"Error general al obtener información del usuario: {str(e)}")
        return {'name': 'Usuario autenticado', 'email': 'Cuenta conectada', 'picture': '', 'id': ''}

def get_subscriptions(youtube):
    """
    Obtiene todas las suscripciones del usuario.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
    
    Returns:
        Lista de diccionarios con información de los canales suscritos
    """
    subscriptions = []
    next_page_token = None
    
    while True:
        request = youtube.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            channel_info = {
                'id': item['snippet']['resourceId']['channelId'],
                'title': item['snippet']['title'],
                'description': item['snippet'].get('description', ''),
                'thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', '')
            }
            subscriptions.append(channel_info)
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return subscriptions

def get_liked_videos(youtube):
    """
    Obtiene todos los videos con "Me gusta" del usuario.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
    
    Returns:
        Lista de diccionarios con información de los videos con "Me gusta"
    """
    liked_videos = []
    next_page_token = None
    
    # Obtener ID de la lista de reproducción "Me gusta"
    channels_response = youtube.channels().list(
        part="contentDetails",
        mine=True
    ).execute()
    
    if not channels_response.get('items'):
        return liked_videos
    
    likes_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['likes']
    
    # Obtener videos de la lista de reproducción "Me gusta"
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=likes_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            video_info = {
                'id': item['snippet']['resourceId']['videoId'],
                'title': item['snippet']['title'],
                'thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', ''),
                'channelTitle': item['snippet']['channelTitle']
            }
            liked_videos.append(video_info)
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return liked_videos

def get_playlists(youtube):
    """
    Obtiene todas las listas de reproducción creadas por el usuario.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
    
    Returns:
        Lista de diccionarios con información de las listas de reproducción
    """
    playlists = []
    next_page_token = None
    
    while True:
        request = youtube.playlists().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            playlist_info = {
                'id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet'].get('description', ''),
                'thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', ''),
                'itemCount': item['contentDetails']['itemCount']
            }
            playlists.append(playlist_info)
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return playlists

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
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            video_info = {
                'id': item['snippet']['resourceId']['videoId'],
                'title': item['snippet']['title'],
                'position': item['snippet']['position']
            }
            playlist_items.append(video_info)
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return playlist_items

def is_already_subscribed(youtube, channel_id):
    """
    Verifica si ya estamos suscritos a un canal.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        channel_id: ID del canal a verificar
    
    Returns:
        True si ya estamos suscritos, False en caso contrario
    """
    request = youtube.subscriptions().list(
        part="snippet",
        mine=True,
        forChannelId=channel_id,
        maxResults=1
    )
    response = request.execute()
    
    return len(response.get('items', [])) > 0

def is_video_liked(youtube, video_id):
    """
    Verifica si ya le dimos "Me gusta" a un video.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        video_id: ID del video a verificar
    
    Returns:
        True si ya le dimos "Me gusta", False en caso contrario
    """
    request = youtube.videos().getRating(
        id=video_id
    )
    response = request.execute()
    
    return response.get('items', [{}])[0].get('rating') == 'like'

def subscribe_to_channels(youtube, subscriptions):
    """
    Suscribe al usuario a una lista de canales.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        subscriptions: Lista de diccionarios con información de los canales
    
    Returns:
        Tupla con el número de suscripciones exitosas y fallidas
    """
    success_count = 0
    failed_count = 0
    already_subscribed_count = 0
    
    for channel in subscriptions:
        channel_id = channel['id']
        channel_title = channel['title']
        
        # Verificar si ya estamos suscritos
        if is_already_subscribed(youtube, channel_id):
            already_subscribed_count += 1
            continue
        
        try:
            # Intentar suscribirse al canal
            request = youtube.subscriptions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": channel_id
                        }
                    }
                }
            )
            request.execute()
            success_count += 1
            
            # Esperar un poco para evitar límites de cuota
            time.sleep(1)
            
        except googleapiclient.errors.HttpError as e:
            failed_count += 1
            print(f"Error al suscribirse a {channel_title}: {str(e)}")
    
    return success_count, failed_count, already_subscribed_count

def like_videos(youtube, videos):
    """
    Da "Me gusta" a una lista de videos.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        videos: Lista de diccionarios con información de los videos
    
    Returns:
        Tupla con el número de "Me gusta" exitosos y fallidos
    """
    success_count = 0
    failed_count = 0
    already_liked_count = 0
    
    # Procesar videos en lotes para evitar exceder límites de la API
    batch_size = 50
    for i in range(0, len(videos), batch_size):
        batch = videos[i:i+batch_size]
        video_ids = [video['id'] for video in batch]
        
        # Verificar cuáles ya tienen "Me gusta"
        ratings_request = youtube.videos().getRating(
            id=','.join(video_ids)
        )
        ratings_response = ratings_request.execute()
        
        # Filtrar solo los videos que no tienen "Me gusta"
        videos_to_like = []
        for j, item in enumerate(ratings_response.get('items', [])):
            if item.get('rating') == 'like':
                already_liked_count += 1
            else:
                videos_to_like.append(video_ids[j])
        
        if videos_to_like:
            try:
                # Dar "Me gusta" a los videos
                youtube.videos().rate(
                    id=','.join(videos_to_like),
                    rating='like'
                ).execute()
                success_count += len(videos_to_like)
                
                # Esperar un poco para evitar límites de cuota
                time.sleep(1)
                
            except googleapiclient.errors.HttpError as e:
                failed_count += len(videos_to_like)
                print(f"Error al dar 'Me gusta' a videos: {str(e)}")
    
    return success_count, failed_count, already_liked_count

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

def add_video_to_playlist(youtube, playlist_id, video_id, position=0):
    """
    Añade un video a una lista de reproducción.
    
    Args:
        youtube: Servicio autenticado de la API de YouTube
        playlist_id: ID de la lista de reproducción
        video_id: ID del video
        position: Posición en la lista de reproducción
    
    Returns:
        True si se añadió correctamente, False en caso contrario
    """
    try:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    },
                    "position": position
                }
            }
        )
        request.execute()
        return True
    except googleapiclient.errors.HttpError:
        return False

def transfer_playlists(youtube_source, youtube_target, playlists):
    """
    Transfiere listas de reproducción de una cuenta a otra.
    
    Args:
        youtube_source: Servicio autenticado de la API de YouTube (origen)
        youtube_target: Servicio autenticado de la API de YouTube (destino)
        playlists: Lista de diccionarios con información de las listas de reproducción
    
    Returns:
        Tupla con estadísticas de la transferencia
    """
    playlists_success = 0
    playlists_failed = 0
    videos_success = 0
    videos_failed = 0
    
    for playlist in playlists:
        try:
            # Crear nueva lista de reproducción en la cuenta de destino
            new_playlist_id = create_playlist(
                youtube_target, 
                playlist['title'], 
                playlist.get('description', '')
            )
            
            # Obtener videos de la lista de reproducción original
            playlist_items = get_playlist_items(youtube_source, playlist['id'])
            
            # Añadir videos a la nueva lista de reproducción
            videos_added = 0
            for item in playlist_items:
                if add_video_to_playlist(
                    youtube_target, 
                    new_playlist_id, 
                    item['id'], 
                    item['position']
                ):
                    videos_success += 1
                    videos_added += 1
                else:
                    videos_failed += 1
                
                # Esperar un poco para evitar límites de cuota
                time.sleep(0.5)
            
            if videos_added > 0:
                playlists_success += 1
            else:
                playlists_failed += 1
                
        except googleapiclient.errors.HttpError as e:
            playlists_failed += 1
            print(f"Error al transferir la lista de reproducción {playlist['title']}: {str(e)}")
    
    return playlists_success, playlists_failed, videos_success, videos_failed

def check_auth_status():
    """
    Verifica el estado de autenticación de ambas cuentas.
    
    Returns:
        Diccionario con el estado de autenticación
    """
    source_auth = os.path.exists(SOURCE_TOKEN_PICKLE)
    target_auth = os.path.exists(TARGET_TOKEN_PICKLE)
    
    # Obtener información de los usuarios si están autenticados
    source_user_info = get_user_info_from_credentials(SOURCE_TOKEN_PICKLE) if source_auth else None
    target_user_info = get_user_info_from_credentials(TARGET_TOKEN_PICKLE) if target_auth else None
    
    return {
        'source': source_auth,
        'target': target_auth,
        'source_email': source_user_info.get('email') if source_user_info else None,
        'target_email': target_user_info.get('email') if target_user_info else None,
        'source_name': source_user_info.get('name') if source_user_info else None,
        'target_name': target_user_info.get('name') if target_user_info else None,
        'source_picture': source_user_info.get('picture') if source_user_info else None,
        'target_picture': target_user_info.get('picture') if target_user_info else None
    }

@app.route('/')
def index():
    # Verificar estado de autenticación sin consumir cuota
    auth_status = check_auth_status()
    
    # Obtener resumen de la transferencia de la sesión
    transfer_summary = session.pop('transfer_summary', None)
    
    return render_template('index.html', auth_status=auth_status, transfer_summary=transfer_summary)

@app.route('/auth/source')
def auth_source():
    # Autenticar cuenta de origen sin verificar la API
    try:
        # Solo autenticamos sin hacer llamadas a la API
        get_authenticated_service(SOURCE_TOKEN_PICKLE, is_source=True, skip_api_check=True)
        
        # Obtener información básica del usuario
        user_info = get_user_info_from_credentials(SOURCE_TOKEN_PICKLE)
        if user_info:
            flash(f'Cuenta de origen autenticada correctamente: {user_info.get("email", "Cuenta conectada")}', 'success')
        else:
            flash('Cuenta de origen autenticada correctamente', 'success')
    except Exception as e:
        # Verificar si es un error de scope
        error_str = str(e).lower()
        if "scope has changed" in error_str:
            # Eliminar el archivo de token para volver a autenticar correctamente
            if os.path.exists(SOURCE_TOKEN_PICKLE):
                os.remove(SOURCE_TOKEN_PICKLE)
            flash('Se detectó un cambio en los permisos requeridos. Por favor, intenta conectar la cuenta nuevamente.', 'warning')
        else:
            flash(f'Error al autenticar la cuenta de origen: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/auth/target')
def auth_target():
    # Autenticar cuenta de destino sin verificar la API
    try:
        # Solo autenticamos sin hacer llamadas a la API
        get_authenticated_service(TARGET_TOKEN_PICKLE, is_source=False, skip_api_check=True)
        
        # Obtener información básica del usuario
        user_info = get_user_info_from_credentials(TARGET_TOKEN_PICKLE)
        if user_info:
            flash(f'Cuenta de destino autenticada correctamente: {user_info.get("email", "Cuenta conectada")}', 'success')
        else:
            flash('Cuenta de destino autenticada correctamente', 'success')
    except Exception as e:
        # Verificar si es un error de scope
        error_str = str(e).lower()
        if "scope has changed" in error_str:
            # Eliminar el archivo de token para volver a autenticar correctamente
            if os.path.exists(TARGET_TOKEN_PICKLE):
                os.remove(TARGET_TOKEN_PICKLE)
            flash('Se detectó un cambio en los permisos requeridos. Por favor, intenta conectar la cuenta nuevamente.', 'warning')
        else:
            flash(f'Error al autenticar la cuenta de destino: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/select_subscriptions')
def select_subscriptions():
    # Verificar que la cuenta de origen esté autenticada
    if not os.path.exists(SOURCE_TOKEN_PICKLE):
        flash('Primero debes autenticar la cuenta de origen', 'error')
        return redirect(url_for('index'))
    
    try:
        # Obtener servicio autenticado
        youtube_source = get_authenticated_service(SOURCE_TOKEN_PICKLE, is_source=True)
        
        # Obtener suscripciones
        subscriptions = get_subscriptions(youtube_source)
        
        # Ordenar alfabéticamente por título
        subscriptions.sort(key=lambda x: x['title'].lower())
        
        return render_template('select_subscriptions.html', subscriptions=subscriptions)
    
    except googleapiclient.errors.HttpError as e:
        error_content = e.content.decode() if hasattr(e, 'content') else str(e)
        
        # Verificar si es un error de exceso de cuota
        if "quota" in error_content.lower() or "429" in error_content:
            flash('Has alcanzado el límite diario de la API de YouTube. Por favor, espera 24 horas y vuelve a intentarlo.', 'warning')
        else:
            flash(f'Error al obtener las suscripciones: {str(e)}', 'error')
        
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error al obtener las suscripciones: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/select_liked_videos')
def select_liked_videos():
    # Verificar que la cuenta de origen esté autenticada
    if not os.path.exists(SOURCE_TOKEN_PICKLE):
        flash('Primero debes autenticar la cuenta de origen', 'error')
        return redirect(url_for('index'))
    
    try:
        # Obtener servicio autenticado
        youtube_source = get_authenticated_service(SOURCE_TOKEN_PICKLE, is_source=True)
        
        # Obtener videos con "Me gusta"
        liked_videos = get_liked_videos(youtube_source)
        
        return render_template('select_liked_videos.html', liked_videos=liked_videos)
    
    except googleapiclient.errors.HttpError as e:
        error_content = e.content.decode() if hasattr(e, 'content') else str(e)
        
        # Verificar si es un error de exceso de cuota
        if "quota" in error_content.lower() or "429" in error_content:
            flash('Has alcanzado el límite diario de la API de YouTube. Por favor, espera 24 horas y vuelve a intentarlo.', 'warning')
        else:
            flash(f'Error al obtener los videos con "Me gusta": {str(e)}', 'error')
        
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error al obtener los videos con "Me gusta": {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/select_playlists')
def select_playlists():
    # Verificar que la cuenta de origen esté autenticada
    if not os.path.exists(SOURCE_TOKEN_PICKLE):
        flash('Primero debes autenticar la cuenta de origen', 'error')
        return redirect(url_for('index'))
    
    try:
        # Obtener servicio autenticado
        youtube_source = get_authenticated_service(SOURCE_TOKEN_PICKLE, is_source=True)
        
        # Obtener listas de reproducción
        playlists = get_playlists(youtube_source)
        
        # Ordenar alfabéticamente por título
        playlists.sort(key=lambda x: x['title'].lower())
        
        return render_template('select_playlists.html', playlists=playlists)
    
    except googleapiclient.errors.HttpError as e:
        error_content = e.content.decode() if hasattr(e, 'content') else str(e)
        
        # Verificar si es un error de exceso de cuota
        if "quota" in error_content.lower() or "429" in error_content:
            flash('Has alcanzado el límite diario de la API de YouTube. Por favor, espera 24 horas y vuelve a intentarlo.', 'warning')
        else:
            flash(f'Error al obtener las listas de reproducción: {str(e)}', 'error')
        
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error al obtener las listas de reproducción: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/transfer', methods=['POST'])
def transfer():
    try:
        # Verificar que ambas cuentas estén autenticadas
        if not os.path.exists(SOURCE_TOKEN_PICKLE) or not os.path.exists(TARGET_TOKEN_PICKLE):
            flash('Debes autenticar ambas cuentas antes de transferir contenido', 'error')
            return redirect(url_for('index'))
        
        # Obtener servicios autenticados
        youtube_source = get_authenticated_service(SOURCE_TOKEN_PICKLE, is_source=True)
        youtube_target = get_authenticated_service(TARGET_TOKEN_PICKLE, is_source=False)
        
        # Determinar el tipo de transferencia
        transfer_type = request.form.get('transfer_type', 'subscriptions')
        
        # Diccionario para almacenar el resumen de la transferencia
        transfer_summary = {}
        
        # Transferir suscripciones
        if transfer_type == 'subscriptions' or transfer_type == 'all':
            selected_channels = request.form.getlist('selected_channels')
            
            if selected_channels:
                # Transferir solo las suscripciones seleccionadas
                subscriptions = []
                all_subscriptions = get_subscriptions(youtube_source)
                
                for channel in all_subscriptions:
                    if channel['id'] in selected_channels:
                        subscriptions.append(channel)
                
                success_count, failed_count, already_subscribed_count = subscribe_to_channels(youtube_target, subscriptions)
                transfer_summary['subscriptions'] = {
                    'success': success_count,
                    'failed': failed_count,
                    'existing': already_subscribed_count,
                    'total': len(subscriptions)
                }
                flash(f'Transferencia de suscripciones completada: {success_count} transferidas, {failed_count} fallidas, {already_subscribed_count} ya existentes', 'success')
            elif transfer_type == 'all':
                # Transferir todas las suscripciones
                subscriptions = get_subscriptions(youtube_source)
                success_count, failed_count, already_subscribed_count = subscribe_to_channels(youtube_target, subscriptions)
                transfer_summary['subscriptions'] = {
                    'success': success_count,
                    'failed': failed_count,
                    'existing': already_subscribed_count,
                    'total': len(subscriptions)
                }
                flash(f'Transferencia de suscripciones completada: {success_count} transferidas, {failed_count} fallidas, {already_subscribed_count} ya existentes', 'success')
        
        # Transferir videos con "Me gusta"
        if transfer_type == 'liked_videos' or transfer_type == 'all':
            selected_videos = request.form.getlist('selected_videos')
            
            if selected_videos:
                # Transferir solo los videos seleccionados
                videos = []
                all_liked_videos = get_liked_videos(youtube_source)
                
                for video in all_liked_videos:
                    if video['id'] in selected_videos:
                        videos.append(video)
                
                success_count, failed_count, already_liked_count = like_videos(youtube_target, videos)
                transfer_summary['liked_videos'] = {
                    'success': success_count,
                    'failed': failed_count,
                    'existing': already_liked_count,
                    'total': len(videos)
                }
                flash(f'Transferencia de "Me gusta" completada: {success_count} transferidos, {failed_count} fallidos, {already_liked_count} ya existentes', 'success')
            elif transfer_type == 'all':
                # Transferir todos los videos con "Me gusta"
                liked_videos = get_liked_videos(youtube_source)
                success_count, failed_count, already_liked_count = like_videos(youtube_target, liked_videos)
                transfer_summary['liked_videos'] = {
                    'success': success_count,
                    'failed': failed_count,
                    'existing': already_liked_count,
                    'total': len(liked_videos)
                }
                flash(f'Transferencia de "Me gusta" completada: {success_count} transferidos, {failed_count} fallidos, {already_liked_count} ya existentes', 'success')
        
        # Transferir listas de reproducción
        if transfer_type == 'playlists' or transfer_type == 'all':
            selected_playlists = request.form.getlist('selected_playlists')
            
            if selected_playlists:
                # Transferir solo las listas de reproducción seleccionadas
                playlists_to_transfer = []
                all_playlists = get_playlists(youtube_source)
                
                for playlist in all_playlists:
                    if playlist['id'] in selected_playlists:
                        playlists_to_transfer.append(playlist)
                
                playlists_success, playlists_failed, videos_success, videos_failed = transfer_playlists(youtube_source, youtube_target, playlists_to_transfer)
                transfer_summary['playlists'] = {
                    'success': playlists_success,
                    'failed': playlists_failed,
                    'videos_success': videos_success,
                    'videos_failed': videos_failed,
                    'total': len(playlists_to_transfer)
                }
                flash(f'Transferencia de listas de reproducción completada: {playlists_success} listas transferidas, {playlists_failed} fallidas, {videos_success} videos añadidos, {videos_failed} videos fallidos', 'success')
            elif transfer_type == 'all':
                # Transferir todas las listas de reproducción
                playlists = get_playlists(youtube_source)
                playlists_success, playlists_failed, videos_success, videos_failed = transfer_playlists(youtube_source, youtube_target, playlists)
                transfer_summary['playlists'] = {
                    'success': playlists_success,
                    'failed': playlists_failed,
                    'videos_success': videos_success,
                    'videos_failed': videos_failed,
                    'total': len(playlists)
                }
                flash(f'Transferencia de listas de reproducción completada: {playlists_success} listas transferidas, {playlists_failed} fallidas, {videos_success} videos añadidos, {videos_failed} videos fallidos', 'success')
        
        # Almacenar el resumen en la sesión para mostrarlo en la página principal
        session['transfer_summary'] = transfer_summary
        
    except googleapiclient.errors.HttpError as e:
        error_content = e.content.decode() if hasattr(e, 'content') else str(e)
        
        # Verificar si es un error de exceso de cuota
        if "quota" in error_content.lower() or "429" in error_content:
            flash('Has alcanzado el límite diario de la API de YouTube. Por favor, espera 24 horas y vuelve a intentarlo. Tu progreso se guardará y el proceso continuará por donde lo dejaste.', 'warning')
        else:
            flash(f'Error durante la transferencia: {str(e)}', 'error')
    
    except Exception as e:
        flash(f'Error durante la transferencia: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/logout/source')
def logout_source():
    if os.path.exists(SOURCE_TOKEN_PICKLE):
        os.remove(SOURCE_TOKEN_PICKLE)
        flash('Se ha cerrado la sesión de la cuenta de origen', 'success')
    return redirect(url_for('index'))

@app.route('/logout/target')
def logout_target():
    if os.path.exists(TARGET_TOKEN_PICKLE):
        os.remove(TARGET_TOKEN_PICKLE)
        flash('Se ha cerrado la sesión de la cuenta de destino', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Permitir OAuth en modo de desarrollo
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True) 