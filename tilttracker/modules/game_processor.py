# tilttracker/modules/game_processor.py
import logging
from typing import Optional, Dict, Tuple, List
from tilttracker.utils.database import Database
from tilttracker.modules.riot_api import RiotAPI
from game_data.calc_classe.calculator_factory import CalculatorFactory

logger = logging.getLogger(__name__)

class GameProcessor:
    def __init__(self):
        self.db = Database()
        self.riot_api = RiotAPI()
        self.calculator_factory = CalculatorFactory()

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

    def calculate_match_score(self, match_stats: Dict, player_stats: Dict) -> Tuple[float, str]:
        """
        Calcule le score d'une partie pour un joueur.
        Retourne le score et un résumé de la performance.
        """
        try:
            # Obtenir le calculateur approprié pour le champion
            calculator = self.calculator_factory.get_calculator(player_stats['champion_id'])
            champion_class = self.calculator_factory.get_champion_class(player_stats['champion_id'])

            # Extraire les kills de l'équipe
            team_kills = 0
            team_id = player_stats['team_id']
            
            # Vérifier si match_stats contient directement les participants ou a une structure imbriquée
            participants = match_stats.get('participants', match_stats.get('info', {}).get('participants', []))
            
            for participant in participants:
                if participant.get('teamId', participant.get('team_id')) == team_id:
                    team_kills += participant.get('kills', 0)

            # Préparer les données complètes pour le calcul
            enhanced_stats = {
                **player_stats,
                'team_kills': team_kills if team_kills > 0 else 1  # Éviter la division par zéro
            }

            # Calculer le score de base et le score final
            base_score = calculator.calculate_base_score(enhanced_stats)
            final_score = calculator.calculate_final_score(base_score, player_stats['win'])

            # Préparer le résumé de performance
            performance_summary = (
                f"Champion: {player_stats['champion_name']} ({champion_class})\n"
                f"KDA: {player_stats['kills']}/{player_stats['deaths']}/{player_stats['assists']}\n"
                f"Dégâts: {player_stats['total_damage_dealt_to_champions']:,}\n"
                f"Score de base: {base_score:.2f}\n"
                f"Points {'gagnés' if final_score > 0 else 'perdus'}: {final_score}"
            )

            return final_score, performance_summary

        except Exception as e:
            logger.error(f"Erreur lors du calcul du score: {e}")
            logger.exception(e)  # Affiche la stack trace complète
            return 0, "Erreur lors du calcul du score"

    def _get_team_kills(self, match_data: Dict, team_id: int) -> int:
        """Calcule le nombre total de kills pour une équipe"""
        team_kills = 0
        for participant in match_data['info']['participants']:
            if participant['teamId'] == team_id:
                team_kills += participant['kills']
        return team_kills

    def _process_single_match(self, match_id: str, puuid: str) -> bool:
        """
        Traite une seule partie et l'enregistre dans la base de données.
        """
        try:
            # Vérifier si la partie existe déjà
            if self._is_match_processed(match_id):
                logger.info(f"La partie {match_id} a déjà été traitée")
                return True

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

            # Calculer le score
            score, performance_summary = self.calculate_match_score(match_details, player_stats)
            logger.info(f"Score calculé pour la partie {match_id}:\n{performance_summary}")

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

            # Ajouter le score aux données du joueur
            player_data = {
                'player_id': player_id,
                'match_id': match_db_id,
                'score': score,
                **player_stats
            }

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