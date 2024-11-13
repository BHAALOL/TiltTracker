# tilttracker/modules/match_watcher.py
import logging
from typing import List, Dict, Optional
from tilttracker.utils.database import Database
from tilttracker.modules.riot_api import RiotAPI
from tilttracker.modules.discord_publisher import DiscordPublisher
from game_data.calc_classe.calculator_factory import CalculatorFactory 

logger = logging.getLogger(__name__)

class MatchWatcher:
    def __init__(self, riot_api_key: str):
        self.db = Database()
        self.riot_api = RiotAPI(riot_api_key)
        self.discord_publisher = DiscordPublisher()
        self.calculator_factory = CalculatorFactory() 
        logger.info("Match Watcher initialisé avec succès")

    async def get_registered_players(self) -> List[Dict]:
        """Récupère la liste des joueurs enregistrés"""
        try:
            with self.db.connection.cursor() as cursor:
                # Ajout de logging pour debug"
                cursor.execute("SELECT COUNT(*) FROM players")
                total_count = cursor.fetchone()[0]
                logger.info(f"Nombre total de joueurs dans la base: {total_count}")
                
                cursor.execute("""
                    SELECT id, summoner_name, tag_line, riot_puuid, discord_id
                    FROM players
                    WHERE riot_puuid IS NOT NULL
                """)
                players = [dict(zip(['id', 'summoner_name', 'tag_line', 'riot_puuid', 'discord_id'], row))
                        for row in cursor.fetchall()]
                
                logger.info(f"Joueurs avec PUUID trouvés: {len(players)}")
                for player in players:
                    logger.info(f"Joueur trouvé: {player['summoner_name']}#{player['tag_line']}")
                    
                return players
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des joueurs: {e}")
            return []

    async def process_new_matches(self, player: Dict) -> None:
        """Traite les nouvelles parties d'un joueur"""
        try:
            logger.info(f"Traitement du joueur: {player['summoner_name']}#{player['tag_line']}")
            
            matches = await self.riot_api.get_recent_aram_matches(player['riot_puuid'], count=5)
            if not matches:
                logger.info(f"Aucune partie ARAM récente pour {player['summoner_name']}#{player['tag_line']}")
                return

            for match_id in matches:
                # Vérifier si la partie a déjà été traitée pour ce joueur spécifique
                if await self._is_match_processed_for_player(match_id, player['id']):
                    logger.info(f"Match {match_id} déjà traité pour {player['summoner_name']}, ignoré")
                    continue
                    
                try:
                    logger.info(f"Traitement de la nouvelle partie {match_id} pour {player['summoner_name']}")
                    await self._process_single_match(match_id, player)
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de la partie {match_id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Erreur lors du traitement des parties pour {player['summoner_name']}: {e}")

    async def _process_single_match(self, match_id: str, player: Dict) -> bool:
        """
        Traite une seule partie et l'enregistre dans la base de données.
        """
        try:
            # Récupérer le total actuel des points avant le nouveau match
            previous_total = await self.db.get_player_total_score(player['id'])
            
            # Récupérer les détails du match
            match_details = await self.riot_api.get_match_details(match_id)
            if not match_details:
                logger.warning(f"Impossible de récupérer les détails pour le match {match_id}")
                return False

            # Récupérer les stats de tous les joueurs de l'équipe
            team_stats = await self.riot_api.get_team_match_stats(match_id, player['riot_puuid'])
            if not team_stats:
                logger.warning(f"Impossible de récupérer les stats d'équipe pour le match {match_id}")
                return False

            # Trouver les stats du joueur dans les stats d'équipe
            player_stats = next((p for p in team_stats if p['puuid'] == player['riot_puuid']), None)
            if not player_stats:
                logger.warning(f"Stats du joueur non trouvées dans l'équipe")
                return False

            # Ajouter summoner_name et tag_line aux stats du joueur
            player_stats['summoner_name'] = player['summoner_name']
            player_stats['tag_line'] = player['tag_line']

            # Calculer le rang des dégâts et ajouter team_size
            team_damages = [p['total_damage_dealt_to_champions'] for p in team_stats 
                        if p['team_id'] == player_stats['team_id']]
            team_damages.sort(reverse=True)
            player_stats['damage_rank'] = team_damages.index(player_stats['total_damage_dealt_to_champions']) + 1
            player_stats['team_size'] = len(team_damages)

            # Calculer les scores de performance pour chaque joueur de l'équipe
            team_performances = []
            for p_stats in team_stats:
                calculator = self.calculator_factory.get_calculator(str(p_stats['champion_id']))
                performance_score = calculator.calculate_performance_score(p_stats)
                team_performances.append({
                    'puuid': p_stats['puuid'],
                    'performance_score': performance_score,
                    'stats': p_stats
                })

            # Trier l'équipe par score de performance
            team_performances.sort(key=lambda x: x['performance_score'], reverse=True)

            # Trouver le rang du joueur dans son équipe
            player_rank = next(i + 1 for i, p in enumerate(team_performances) 
                            if p['puuid'] == player['riot_puuid'])

            # Calculer les points selon le rang et la victoire/défaite
            calculator = self.calculator_factory.get_calculator(str(player_stats['champion_id']))
            final_score = calculator.calculate_score(
                stats=player_stats,
                rank_in_team=player_rank,
                is_victory=player_stats['win']
            )

            # Ajouter le rang aux stats du joueur
            player_stats['rank_in_team'] = player_rank

            # Stocker le match dans la base de données
            match_db_id = await self._store_match(match_details)
            if not match_db_id:
                return False

            # Stocker la performance du joueur avec le score et le rang
            player_data = {
                'player_id': player['id'],
                'match_id': match_db_id,
                'score': final_score,
                'rank_in_team': player_rank,
                **player_stats
            }

            # Enregistrer les stats du joueur
            success = await self._store_performance(match_db_id, player_data)
            if not success:
                return False

            # Récupérer le nouveau total après l'ajout du score
            new_total = await self.db.get_player_total_score(player['id'])

            # Préparer les informations de score pour Discord
            score_info = {
                'final_score': final_score,
                'total_score': new_total,
                'previous_total': previous_total,
                'score_change': new_total - previous_total,
                'rank_in_team': player_rank,
                'base_score': final_score  # Ajouté pour la compatibilité
            }

            # Publier sur Discord
            await self.discord_publisher.publish_match_result(
                player_stats=player_stats,
                match_stats=match_details,
                score_info=score_info
            )

            logger.info(f"Match {match_id} traité avec succès pour {player['summoner_name']} "
                    f"(Rang: {player_rank}, Score: {final_score})")
            return True

        except Exception as e:
            logger.error(f"Erreur lors du traitement de la partie {match_id}: {e}")
            logger.exception(e)
            return False

    async def _is_match_processed_for_player(self, match_id: str, player_id: int) -> bool:
        """Vérifie si une partie a déjà été traitée pour un joueur spécifique"""
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 
                        FROM matches m
                        JOIN player_matches pm ON pm.match_id = m.id
                        WHERE m.match_id = %s AND pm.player_id = %s
                    )
                """, (match_id, player_id))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la partie {match_id} pour le joueur {player_id}: {e}")
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