# tilttracker/modules/riot_api.py
import os
import logging
import time
import urllib.parse
from typing import Optional, List, Dict, Any
import aiohttp
import asyncio
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class RiotAPI:
    def __init__(self, riot_api_key: str = None):
        load_dotenv()
        
        # Utiliser la clé API passée en paramètre ou celle de l'environnement
        self.api_key = riot_api_key or os.getenv('RIOT_API_KEY')
        if not self.api_key:
            raise ValueError("RIOT_API_KEY non trouvée")
        
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

        # Session aiohttp
        self.session = None

        logger.info("RiotAPI initialisée avec succès")

    async def _ensure_session(self):
        """S'assure qu'une session est active"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def _make_request(self, url: str) -> Optional[Dict]:
        """
        Effectue une requête HTTP avec gestion des erreurs et des limites de taux.
        """
        await self._ensure_session()
        
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Limite de taux atteinte, attente de {retry_after} secondes")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(url)
                    
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning(f"Ressource non trouvée: {url}")
                return None
            else:
                logger.error(f"Erreur HTTP lors de la requête à {url}: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Erreur lors de la requête à {url}: {e}")
            raise

    async def get_puuid(self, summoner_name: str, tag_line: str) -> Optional[str]:
        """
        Récupère le PUUID d'un joueur à partir de son nom d'invocateur et de son tag.
        """
        encoded_name = urllib.parse.quote(summoner_name)
        encoded_tag = urllib.parse.quote(tag_line)
        url = f"{self.base_urls['europe']}/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"
        
        response = await self._make_request(url)
        if response:
            logger.info(f"PUUID récupéré pour {summoner_name}#{tag_line}")
            return response.get('puuid')
        return None

    async def get_recent_aram_matches(self, puuid: str, count: int = 20) -> List[str]:
        """
        Récupère les IDs des dernières parties ARAM d'un joueur.
        """
        params = {
            'queue': self.ARAM_QUEUE_ID,
            'start': 0,
            'count': count
        }
        
        url = f"{self.base_urls['europe']}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params_str = '&'.join(f'{k}={v}' for k, v in params.items())
        full_url = f"{url}?{params_str}"
        
        matches = await self._make_request(full_url)
        
        if matches:
            logger.info(f"{len(matches)} parties ARAM trouvées pour le PUUID {puuid}")
            return matches
        return []

    async def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'une partie spécifique.
        Ne retourne que les parties ARAM.
        """
        url = f"{self.base_urls['europe']}/lol/match/v5/matches/{match_id}"
        match_data = await self._make_request(url)
        
        if not match_data:
            return None
            
        # Vérifier que c'est bien une partie ARAM
        if match_data.get('info', {}).get('queueId') != self.ARAM_QUEUE_ID:
            logger.debug(f"Match {match_id} n'est pas une partie ARAM")
            return None
            
        info = match_data['info']
        
        match_details = {
            'match_id': match_id,
            'game_duration': info['gameDuration'],
            'game_version': info['gameVersion'],
            'queue_id': info['queueId']
        }
        
        logger.info(f"Détails récupérés pour le match {match_id}")
        return match_details

    async def get_player_match_stats(self, match_id: str, puuid: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les statistiques d'un joueur spécifique dans une partie.
        """
        match_data = await self._make_request(
            f"{self.base_urls['europe']}/lol/match/v5/matches/{match_id}"
        )
        
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


    async def get_account_info(self, game_name: str, tag_line: str) -> Optional[Dict]:
        """
        Récupère les informations détaillées d'un compte Riot à partir du Riot ID.
        """
        try:
            # D'abord récupérer le PUUID
            puuid = await self.get_puuid(game_name, tag_line)
            if not puuid:
                logger.error(f"PUUID non trouvé pour {game_name}#{tag_line}")
                return None

            # Récupérer les infos du compte via PUUID
            summoner_url = f"{self.base_urls['euw1']}/lol/summoner/v4/summoners/by-puuid/{puuid}"
            summoner_data = await self._make_request(summoner_url)
            
            if not summoner_data:
                logger.error(f"Données summoner non trouvées pour {game_name}#{tag_line}")
                return None

            # Récupérer les infos de rang
            rank_url = f"{self.base_urls['euw1']}/lol/league/v4/entries/by-summoner/{summoner_data['id']}"
            rank_data = await self._make_request(rank_url)
            
            # Préparer les données de rang
            ranks = {}
            if rank_data:
                for queue in rank_data:
                    if queue['queueType'] == 'RANKED_SOLO_5x5':
                        ranks['solo_duo'] = {
                            'tier': queue['tier'],
                            'rank': queue['rank'],
                            'lp': queue['leaguePoints'],
                            'wins': queue['wins'],
                            'losses': queue['losses']
                        }
                    elif queue['queueType'] == 'RANKED_FLEX_SR':
                        ranks['flex'] = {
                            'tier': queue['tier'],
                            'rank': queue['rank'],
                            'lp': queue['leaguePoints'],
                            'wins': queue['wins'],
                            'losses': queue['losses']
                        }

            # Construire la réponse
            account_info = {
                'summonerId': summoner_data['id'],
                'accountId': summoner_data.get('accountId'),
                'puuid': puuid,
                'name': game_name,
                'tag_line': tag_line,
                'profileIconId': summoner_data['profileIconId'],
                'summonerLevel': summoner_data['summonerLevel'],
                'ranks': ranks
            }

            logger.info(f"Informations du compte récupérées pour {game_name}#{tag_line}")
            return account_info

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations du compte: {e}")
            logger.exception(e)  # Pour voir la stack trace complète
            return None

    async def cleanup(self):
        """Nettoie les ressources"""
        if self.session:
            await self.session.close()
            self.session = None