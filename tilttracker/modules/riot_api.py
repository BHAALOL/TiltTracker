# tilttracker/modules/riot_api.py
import os
import logging
import time
import urllib.parse
from typing import Optional, List, Dict, Any
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class RiotAPI:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('RIOT_API_KEY')
        if not self.api_key:
            raise ValueError("RIOT_API_KEY non trouvée dans les variables d'environnement")
        
        # URLs de base pour différentes régions
        self.base_urls = {
            'europe': 'https://europe.api.riotgames.com',
            'euw1': 'https://euw1.api.riotgames.com'
        }
        
        # ID de la file ARAM
        self.ARAM_QUEUE_ID = 450
        
        # Headers par défaut pour les requêtes
        self.headers = {
            'X-Riot-Token': self.api_key
        }

    def _make_request(self, url: str) -> Optional[Dict]:
        """
        Effectue une requête HTTP avec gestion des erreurs et des limites de taux.
        """
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Limite de taux atteinte, attente de {retry_after} secondes")
                time.sleep(retry_after)
                return self._make_request(url)  # Réessayer après l'attente
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Ressource non trouvée: {url}")
                return None
            else:
                logger.error(f"Erreur HTTP lors de la requête à {url}: {e}")
                raise
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête à {url}: {e}")
            raise

    def get_puuid(self, summoner_name: str, tag_line: str) -> Optional[str]:
        """
        Récupère le PUUID d'un joueur à partir de son nom d'invocateur et de son tag.
        """
        encoded_name = urllib.parse.quote(summoner_name)
        encoded_tag = urllib.parse.quote(tag_line)
        url = f"{self.base_urls['europe']}/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"
        
        response = self._make_request(url)
        if response:
            logger.info(f"PUUID récupéré pour {summoner_name}#{tag_line}")
            return response.get('puuid')
        return None

    def get_recent_aram_matches(self, puuid: str, count: int = 20) -> List[str]:
        """
        Récupère les IDs des dernières parties ARAM d'un joueur.
        """
        url = f"{self.base_urls['europe']}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {
            'queue': self.ARAM_QUEUE_ID,
            'start': 0,
            'count': count
        }
        
        full_url = f"{url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        matches = self._make_request(full_url)
        
        if matches:
            logger.info(f"{len(matches)} parties ARAM trouvées pour le PUUID {puuid}")
            return matches
        return []

    def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'une partie spécifique.
        Ne retourne que les parties ARAM.
        """
        url = f"{self.base_urls['europe']}/lol/match/v5/matches/{match_id}"
        match_data = self._make_request(url)
        
        if not match_data:
            return None
            
        # Vérifier que c'est bien une partie ARAM
        if match_data.get('info', {}).get('queueId') != self.ARAM_QUEUE_ID:
            logger.debug(f"Match {match_id} n'est pas une partie ARAM")
            return None
            
        # Extraire les informations pertinentes
        info = match_data['info']
        
        match_details = {
            'match_id': match_id,
            'game_duration': info['gameDuration'],
            'game_version': info['gameVersion'],
            'queue_id': info['queueId']
        }
        
        logger.info(f"Détails récupérés pour le match {match_id}")
        return match_details

    def get_player_match_stats(self, match_id: str, puuid: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les statistiques d'un joueur spécifique dans une partie.
        """
        match_data = self._make_request(f"{self.base_urls['europe']}/lol/match/v5/matches/{match_id}")
        
        if not match_data:
            return None
            
        # Trouver les stats du joueur dans la partie
        for participant in match_data['info']['participants']:
            if participant['puuid'] == puuid:
                stats = {
                    'champion_id': participant['championId'],
                    'champion_name': participant['championName'],
                    'kills': participant['kills'],
                    'deaths': participant['deaths'],
                    'assists': participant['assists'],
                    'total_damage_dealt_to_champions': participant['totalDamageDealtToChampions'],
                    'total_damage_taken': participant['totalDamageTaken'],
                    'damage_self_mitigated': participant['damageSelfMitigated'],
                    'total_time_crowd_control_dealt': participant['totalTimeCCDealt'],
                    'vision_score': participant['visionScore'],
                    'gold_earned': participant['goldEarned'],
                    'win': participant['win'],
                    'team_id': participant['teamId']
                }
                
                logger.info(f"Stats récupérées pour le joueur {puuid} dans le match {match_id}")
                return stats
                
        logger.warning(f"Joueur {puuid} non trouvé dans le match {match_id}")
        return None

    def is_valid_summoner(self, summoner_name: str, tag_line: str) -> bool:
        """
        Vérifie si un compte Riot existe.
        """
        puuid = self.get_puuid(summoner_name, tag_line)
        return puuid is not None