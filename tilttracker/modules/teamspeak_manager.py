import os
import logging
import time
from ts3.query import TS3Connection
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class TeamSpeakManager:
    def __init__(self):
        load_dotenv()
        self.ts_host = os.getenv('TS_HOST')
        self.ts_port = int(os.getenv('TS_PORT', 10011))
        self.ts_username = os.getenv('TS_USERNAME')
        self.ts_password = os.getenv('TS_PASSWORD')
        self.ts_virtualserver_id = int(os.getenv('TS_VIRTUALSERVER_ID', 1))
        self.server = None

    def connect(self):
        """Établit la connexion au serveur TeamSpeak"""
        try:
            self.server = TS3Connection(self.ts_host, self.ts_port)
            self.server.login(
                client_login_name=self.ts_username,
                client_login_password=self.ts_password
            )
            self.server.use(sid=self.ts_virtualserver_id)
            logger.info("Connexion au serveur TeamSpeak établie")
            return True
        except Exception as e:
            logger.error(f"Erreur de connexion au serveur TeamSpeak: {e}")
            return False

    def get_server_info(self):
        """Récupère les informations basiques du serveur"""
        try:
            if not self.server:
                if not self.connect():
                    return None
            response = self.server.serverinfo()
            # Convertir la réponse en dictionnaire
            if response and response.parsed:
                return response.parsed[0]
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos serveur: {e}")
            return None

    def get_channels(self):
        """Récupère la liste des canaux avec leurs utilisateurs"""
        try:
            if not self.server:
                if not self.connect():
                    return None

            # Récupère tous les canaux
            channels_response = self.server.channellist()
            channels = channels_response.parsed if channels_response else []
            
            # Récupère tous les clients (utilisateurs)
            clients_response = self.server.clientlist()
            clients = clients_response.parsed if clients_response else []

            # Log pour le débogage
            logger.debug(f"Canaux reçus: {channels}")
            logger.debug(f"Clients reçus: {clients}")

            # Organise les clients par canal
            channels_with_users = {}
            for channel in channels:
                channel_id = int(channel.get('cid', 0))
                channels_with_users[channel_id] = {
                    'info': {
                        'channel_name': channel.get('channel_name', 'Sans nom'),
                        'channel_order': int(channel.get('channel_order', 0))
                    },
                    'users': []
                }

            # Ajoute les utilisateurs dans leurs canaux respectifs
            for client in clients:
                # Ignore les clients ServerQuery
                if client.get('client_type') == '1':
                    continue
                    
                try:
                    channel_id = int(client.get('cid', 0))
                    if channel_id in channels_with_users:
                        user_info = {
                            'name': client.get('client_nickname', 'Inconnu'),
                            'is_away': bool(int(client.get('client_away', 0))),
                            'is_muted': bool(int(client.get('client_input_muted', 0))),
                            'platform': client.get('client_platform', 'unknown')
                        }
                        channels_with_users[channel_id]['users'].append(user_info)
                except (ValueError, TypeError) as e:
                    logger.error(f"Erreur lors du traitement du client: {e}")
                    continue

            return channels_with_users

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des canaux et utilisateurs: {e}")
            logger.exception(e)  # Ajoute la stack trace complète
            return None

    def get_server_status(self):
        """Récupère le statut complet du serveur"""
        try:
            if not self.server:
                if not self.connect():
                    return {
                        'status': 'offline',
                        'channels': None,
                        'error': 'Impossible de se connecter au serveur'
                    }

            server_info = self.get_server_info()
            channels = self.get_channels()

            if not server_info or not channels:
                return {
                    'status': 'error',
                    'channels': None,
                    'error': 'Erreur lors de la récupération des données'
                }

            return {
                'status': 'online',
                'server_name': server_info.get('virtualserver_name', 'Serveur TeamSpeak'),
                'channels': channels,
                'last_update': time.strftime('%H:%M:%S')
            }

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return {
                'status': 'error',
                'channels': None,
                'error': str(e)
            }

    def __del__(self):
        """Ferme la connexion quand l'objet est détruit"""
        if self.server:
            try:
                self.server.quit()
            except:
                pass