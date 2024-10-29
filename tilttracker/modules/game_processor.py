# tilttracker/modules/game_processor.py
import logging
from typing import Optional, Dict
from tilttracker.utils.database import Database
from tilttracker.modules.riot_api import RiotAPI

logger = logging.getLogger(__name__)

class GameProcessor:
    def __init__(self):
        self.db = Database()
        self.riot_api = RiotAPI()

    def ensure_player_exists(self, summoner_name: str, tag_line: str, discord_id: str = None) -> Optional[int]:
        """
        S'assure que le joueur existe dans la base de données.
        Le crée s'il n'existe pas.
        """
        try:
            # Récupérer le PUUID
            puuid = self.riot_api.get_puuid(summoner_name, tag_line)
            if not puuid:
                logger.error(f"Impossible de trouver le compte Riot {summoner_name}#{tag_line}")
                return None

            # Vérifier si le joueur existe déjà
            player_id = self._get_player_id_by_puuid(puuid)
            if player_id:
                return player_id

            # Si le joueur n'existe pas, l'enregistrer
            discord_id = discord_id or f"manual_{summoner_name}"  # ID temporaire si pas de Discord ID
            success = self.db.register_player(
                discord_id=discord_id,
                riot_puuid=puuid,
                summoner_name=summoner_name,
                tag_line=tag_line
            )

            if success:
                logger.info(f"Joueur {summoner_name}#{tag_line} enregistré avec succès")
                return self._get_player_id_by_puuid(puuid)
            
            return None

        except Exception as e:
            logger.error(f"Erreur lors de la vérification/création du joueur: {e}")
            return None

    def process_recent_matches(self, summoner_name: str, tag_line: str, discord_id: str = None) -> bool:
        """
        Traite les parties récentes d'un joueur et les stocke dans la base de données.
        """
        try:
            # S'assurer que le joueur existe
            player_id = self.ensure_player_exists(summoner_name, tag_line, discord_id)
            if not player_id:
                logger.error(f"Impossible de traiter les parties: joueur non trouvé/créé")
                return False

            # Récupérer le PUUID
            puuid = self.riot_api.get_puuid(summoner_name, tag_line)
            if not puuid:
                return False

            # Récupérer les dernières parties ARAM
            matches = self.riot_api.get_recent_aram_matches(puuid, count=10)
            if not matches:
                logger.info(f"Aucune partie ARAM récente trouvée pour {summoner_name}#{tag_line}")
                return True

            logger.info(f"Traitement de {len(matches)} parties pour {summoner_name}#{tag_line}")
            
            processed_matches = 0
            for match_id in matches:
                logger.info(f"Vérification de la partie {match_id}")
                if not self._is_match_processed(match_id):
                    logger.info(f"Traitement de la nouvelle partie {match_id}")
                    if self._process_single_match(match_id, puuid):
                        processed_matches += 1
                else:
                    logger.info(f"Partie {match_id} déjà traitée, ignorée")

            logger.info(f"{processed_matches} nouvelles parties traitées pour {summoner_name}#{tag_line}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors du traitement des parties: {e}")
            return False

    def _is_match_processed(self, match_id: str) -> bool:
        """
        Vérifie si une partie est déjà dans la base de données.
        """
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute("SELECT id FROM matches WHERE match_id = %s", (match_id,))
                result = cursor.fetchone()
                is_processed = result is not None
                logger.info(f"Vérification du match {match_id}: {'déjà traité' if is_processed else 'nouveau match'}")
                return is_processed
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la partie {match_id}: {e}")
            return False

    def _process_single_match(self, match_id: str, puuid: str) -> bool:
        """
        Traite une seule partie et l'enregistre dans la base de données.
        """
        try:
            # Récupérer les détails de la partie
            match_details = self.riot_api.get_match_details(match_id)
            if not match_details:
                logger.warning(f"Impossible de récupérer les détails de la partie {match_id}")
                return False

            # Récupérer les stats du joueur
            player_stats = self.riot_api.get_player_match_stats(match_id, puuid)
            if not player_stats:
                logger.warning(f"Impossible de récupérer les stats du joueur pour la partie {match_id}")
                return False

            # Récupérer l'ID du joueur
            player_id = self._get_player_id_by_puuid(puuid)
            if not player_id:
                logger.error(f"Impossible de trouver l'ID du joueur pour le PUUID {puuid}")
                return False

            # Enregistrer la partie
            match_db_id = self.db.store_match(match_details)
            if not match_db_id:
                logger.error(f"Échec de l'enregistrement de la partie {match_id}")
                return False

            # Préparer les données pour l'enregistrement avec l'ID du match
            player_data = {
                'player_id': player_id,
                'match_id': match_db_id,
                **player_stats
            }

            logger.debug(f"Données préparées pour le stockage: {player_data}")

            # Enregistrer les stats du joueur
            success = self.db.store_player_performance(match_db_id, player_data)
            if not success:
                logger.error(f"Échec de l'enregistrement des stats du joueur pour la partie {match_id}")
                return False

            logger.info(f"Partie {match_id} traitée avec succès")
            return True

        except Exception as e:
            logger.error(f"Erreur lors du traitement de la partie {match_id}: {e}")
            logger.exception(e)
            return False

    def _get_player_id_by_puuid(self, puuid: str) -> Optional[int]:
        """
        Récupère l'ID du joueur depuis la base de données en utilisant son PUUID.
        """
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute("SELECT id FROM players WHERE riot_puuid = %s", (puuid,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'ID du joueur: {e}")
            return None

    def close(self):
        """Ferme les connexions à la base de données"""
        self.db.close()