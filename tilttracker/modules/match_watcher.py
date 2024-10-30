# tilttracker/modules/match_watcher.py
import logging
from typing import List, Dict, Optional
from tilttracker.utils.database import Database
from tilttracker.modules.riot_api import RiotAPI
from tilttracker.modules.discord_publisher import DiscordPublisher

logger = logging.getLogger(__name__)

class MatchWatcher:
    def __init__(self, riot_api_key: str):
        self.db = Database()
        self.riot_api = RiotAPI(riot_api_key)
        self.discord_publisher = DiscordPublisher()
        logger.info("Match Watcher initialisé avec succès")

    async def get_registered_players(self) -> List[Dict]:
        """Récupère la liste des joueurs enregistrés"""
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, summoner_name, tag_line, riot_puuid, discord_id
                    FROM players
                    WHERE riot_puuid IS NOT NULL
                """)
                return [dict(zip(['id', 'summoner_name', 'tag_line', 'riot_puuid', 'discord_id'], row))
                        for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des joueurs: {e}")
            return []

    async def process_new_matches(self, player: Dict) -> None:
        """Traite les nouvelles parties d'un joueur"""
        try:
            # Récupérer les dernières parties ARAM
            matches = await self.riot_api.get_recent_aram_matches(player['riot_puuid'])
            if not matches:
                logger.info(f"Aucune partie ARAM récente pour {player['summoner_name']}#{player['tag_line']}")
                return

            for match_id in matches:
                # Vérifier si la partie a déjà été traitée
                if not await self._is_match_processed(match_id):
                    logger.info(f"Nouvelle partie trouvée: {match_id}")
                    
                    # Récupérer les détails
                    match_details = await self.riot_api.get_match_details(match_id)
                    if match_details:
                        player_stats = await self.riot_api.get_player_match_stats(match_id, player['riot_puuid'])

                        if player_stats:
                            # Stocker la partie
                            match_db_id = await self._store_match(match_details)
                            
                            if match_db_id:
                                # Ajouter les infos du joueur
                                player_data = {
                                    'player_id': player['id'],
                                    'match_id': match_db_id,
                                    **player_stats
                                }
                                
                                # Stocker les performances
                                success = await self._store_performance(match_db_id, player_data)
                                
                                if success:
                                    # Préparer les données pour Discord
                                    score_info = {
                                        'base_score': player_stats.get('score', 0),
                                        'final_score': player_stats.get('score', 0)
                                    }
                                    
                                    # Publier sur Discord
                                    await self.discord_publisher.publish_match_result(
                                        player_stats={
                                            **player_stats,
                                            'summoner_name': player['summoner_name'],
                                            'tag_line': player['tag_line']
                                        },
                                        match_stats=match_details,
                                        score_info=score_info
                                    )
                                    
                                    logger.info(f"Partie {match_id} traitée avec succès")

        except Exception as e:
            logger.error(f"Erreur lors du traitement des parties pour {player['summoner_name']}: {e}")


    async def _is_match_processed(self, match_id: str) -> bool:
        """Vérifie si une partie a déjà été traitée"""
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM matches WHERE match_id = %s)",
                    (match_id,)
                )
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la partie {match_id}: {e}")
            return False

    async def _store_match(self, match_details: Dict) -> Optional[int]:
        """Stocke une partie dans la base de données"""
        try:
            return await self.db.store_match(match_details)
        except Exception as e:
            logger.error(f"Erreur lors du stockage de la partie: {e}")
            return None

    async def _store_performance(self, match_id: int, player_data: Dict) -> bool:
        """Stocke les performances d'un joueur"""
        try:
            return await self.db.store_player_performance(match_id, player_data)
        except Exception as e:
            logger.error(f"Erreur lors du stockage des performances: {e}")
            return False

    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.db.close()
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")