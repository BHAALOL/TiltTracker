import os
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
import asyncpg

# Configuration du logger
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        load_dotenv()
        
        # Récupération des variables d'environnement
        self.db_params = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT")
        }
        
        self.connection = None
        self.connect()

    def connect(self):
        """Établit la connexion à la base de données."""
        try:
            self.connection = psycopg2.connect(**self.db_params)
            logger.info("Connexion à la base de données établie avec succès")
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la connexion à la base de données: {e}")
            raise

    async def register_player(self, discord_id: str, riot_puuid: str, summoner_name: str, tag_line: str) -> bool:
        """
        Enregistre un nouveau joueur dans la base de données.
        Version asynchrone qui utilise psycopg2 de manière synchrone.
        """
        try:
            with self.connection.cursor() as cursor:
                # On vérifie si la combinaison summoner_name/tag_line existe déjà
                cursor.execute("""
                    SELECT id FROM players 
                    WHERE summoner_name = %s AND tag_line = %s
                """, (summoner_name, tag_line))
                
                existing_player = cursor.fetchone()
                
                if existing_player:
                    # Mise à jour du joueur existant
                    cursor.execute("""
                        UPDATE players 
                        SET riot_puuid = %s,
                            discord_id = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE summoner_name = %s AND tag_line = %s
                        RETURNING id
                    """, (riot_puuid, discord_id, summoner_name, tag_line))
                else:
                    # Insertion d'un nouveau joueur
                    cursor.execute("""
                        INSERT INTO players (discord_id, riot_puuid, summoner_name, tag_line)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (discord_id, riot_puuid, summoner_name, tag_line))
                
                self.connection.commit()
                logger.info(f"Joueur {summoner_name}#{tag_line} {'mis à jour' if existing_player else 'enregistré'} avec succès")
                return True
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Erreur lors de l'enregistrement du joueur: {e}")
            return False

    async def store_match(self, match_data: dict) -> int:
        """
        Stocke les données d'une partie et retourne son ID.
        Version asynchrone qui utilise psycopg2 de manière synchrone.
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO matches (match_id, game_duration, game_version, queue_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (match_id) DO UPDATE
                    SET game_duration = EXCLUDED.game_duration
                    RETURNING id
                """, (
                    match_data['match_id'],
                    match_data['game_duration'],
                    match_data['game_version'],
                    match_data['queue_id']
                ))
                
                match_db_id = cursor.fetchone()[0]
                self.connection.commit()
                logger.info(f"Match {match_data['match_id']} stocké avec succès")
                return match_db_id
                
        except psycopg2.Error as e:
            self.connection.rollback()
            logger.error(f"Erreur lors du stockage de la partie: {e}")
            raise

    async def store_player_performance(self, match_id: int, player_data: dict) -> bool:
        """Version asynchrone de store_player_performance"""
        try:
            logger.info(f"Tentative d'enregistrement des performances pour le match {match_id}")
            logger.debug(f"Données du joueur: {player_data}")
            
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO player_matches (
                        player_id, match_id, champion_id, champion_name,
                        kills, deaths, assists,
                        total_damage_dealt_to_champions, total_damage_taken,
                        damage_self_mitigated, total_time_crowd_control_dealt,
                        vision_score, gold_earned, win, team_id, score
                    ) VALUES (
                        %(player_id)s, %(match_id)s, %(champion_id)s, %(champion_name)s,
                        %(kills)s, %(deaths)s, %(assists)s,
                        %(total_damage_dealt_to_champions)s, %(total_damage_taken)s,
                        %(damage_self_mitigated)s, %(total_time_crowd_control_dealt)s,
                        %(vision_score)s, %(gold_earned)s, %(win)s, %(team_id)s, %(score)s
                    )
                """, player_data)
                
                self.connection.commit()
                logger.info(f"Performance du joueur stockée avec succès pour le match {match_id}")
                return True
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Erreur lors du stockage des performances du joueur: {e}")
            return False

    def get_player_by_discord_id(self, discord_id: str) -> dict:
        """
        Récupère les informations d'un joueur par son ID Discord.
        """
        try:
            with self.connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM players WHERE discord_id = %s
                """, (discord_id,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la récupération du joueur: {e}")
            return None

    def get_player_by_riot_id(self, riot_puuid: str) -> dict:
        """
        Récupère les informations d'un joueur par son PUUID Riot.
        """
        try:
            with self.connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM players WHERE riot_puuid = %s
                """, (riot_puuid,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la récupération du joueur: {e}")
            return None

    async def get_player_stats(self, game_name: str, tag_line: str) -> dict:
        """Récupère les statistiques complètes d'un joueur"""
        try:
            with self.connection.cursor() as cursor:
                # Statistiques générales
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_games,
                        SUM(CASE WHEN win THEN 1 ELSE 0 END) as wins,
                        AVG(kills) as avg_kills,
                        AVG(deaths) as avg_deaths,
                        AVG(assists) as avg_assists,
                        AVG(score) as avg_score,
                        MAX(score) as best_score,
                        SUM(score) as total_score
                    FROM player_matches pm
                    JOIN players p ON p.id = pm.player_id
                    WHERE p.summoner_name = %s AND p.tag_line = %s
                """, (game_name, tag_line))
                
                stats = dict(zip([column[0] for column in cursor.description], cursor.fetchone()))
                
                # Champions les plus joués
                cursor.execute("""
                    SELECT 
                        champion_name,
                        COUNT(*) as games,
                        SUM(CASE WHEN win THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as winrate
                    FROM player_matches pm
                    JOIN players p ON p.id = pm.player_id
                    WHERE p.summoner_name = %s AND p.tag_line = %s
                    GROUP BY champion_name
                    ORDER BY games DESC, winrate DESC
                    LIMIT 3
                """, (game_name, tag_line))
                
                stats['top_champions'] = [
                    dict(zip([column[0] for column in cursor.description], row))
                    for row in cursor.fetchall()
                ]
                
                # Calculer les stats dérivées
                stats['losses'] = stats['total_games'] - stats['wins']
                stats['winrate'] = (stats['wins'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0
                stats['kda_ratio'] = ((stats['avg_kills'] + stats['avg_assists']) / stats['avg_deaths']) if stats['avg_deaths'] > 0 else float('inf')
                
                # Récupérer le classement
                cursor.execute("""
                    WITH rankings AS (
                        SELECT 
                            p.summoner_name,
                            p.tag_line,
                            SUM(score) as total_score,
                            RANK() OVER (ORDER BY SUM(score) DESC) as rank
                        FROM player_matches pm
                        JOIN players p ON p.id = pm.player_id
                        GROUP BY p.id, p.summoner_name, p.tag_line
                    )
                    SELECT rank
                    FROM rankings
                    WHERE summoner_name = %s AND tag_line = %s
                """, (game_name, tag_line))
                
                stats['rank'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats pour {game_name}#{tag_line}: {e}")
            return None

    async def get_leaderboard(self, limit: int = 10) -> list:
        """Récupère le classement des meilleurs joueurs"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.summoner_name,
                        p.tag_line,
                        COUNT(*) as total_games,
                        SUM(CASE WHEN win THEN 1 ELSE 0 END) as wins,
                        SUM(score) as total_score,
                        AVG(score) as avg_score
                    FROM player_matches pm
                    JOIN players p ON p.id = pm.player_id
                    GROUP BY p.id, p.summoner_name, p.tag_line
                    ORDER BY total_score DESC
                    LIMIT %s
                """, (limit,))
                
                players = [dict(zip([column[0] for column in cursor.description], row))
                          for row in cursor.fetchall()]
                
                # Calculer le winrate pour chaque joueur
                for player in players:
                    player['winrate'] = (player['wins'] / player['total_games'] * 100)
                    
                return players
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du classement: {e}")
            return None

    async def get_last_game(self, game_name: str, tag_line: str) -> dict:
        """Récupère la dernière partie d'un joueur"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pm.*,
                        m.match_id,
                        m.game_duration,
                        m.created_at
                    FROM player_matches pm
                    JOIN players p ON p.id = pm.player_id
                    JOIN matches m ON m.id = pm.match_id
                    WHERE p.summoner_name = %s 
                    AND p.tag_line = %s
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                """, (game_name, tag_line))
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"Aucune partie trouvée pour {game_name}#{tag_line}")
                    return None

                game = dict(zip([column[0] for column in cursor.description], result))
                
                logger.info(f"Dernière partie trouvée pour {game_name}#{tag_line} : {game['match_id']}")
                
                return {
                    'player_stats': {
                        'summoner_name': game_name,
                        'tag_line': tag_line,
                        'champion_name': game['champion_name'],
                        'kills': game['kills'],
                        'deaths': game['deaths'],
                        'assists': game['assists'],
                        'total_damage_dealt_to_champions': game['total_damage_dealt_to_champions'],
                        'total_damage_taken': game['total_damage_taken'],
                        'win': game['win']
                    },
                    'match_stats': {
                        'match_id': game['match_id'],
                        'game_duration': game['game_duration'],
                        'created_at': game['created_at']
                    },
                    'score_info': {
                        'final_score': game.get('score', 0),
                        'base_score': game.get('score', 0)
                    }
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la dernière partie pour {game_name}#{tag_line}: {e}")
            return None

    async def get_player_total_score(self, player_id: int) -> int:
        """
        Récupère le total des points d'un joueur.
        
        Args:
            player_id: L'ID du joueur dans la base de données
            
        Returns:
            Le total des points du joueur (0 si aucun match)
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COALESCE(SUM(score), 0) as total_score
                    FROM player_matches
                    WHERE player_id = %s
                """, (player_id,))
                
                total = cursor.fetchone()[0]
                logger.info(f"Total des points récupéré pour le joueur {player_id}: {total}")
                return total
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du total des points pour le joueur {player_id}: {e}")
            return 0

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.connection:
            self.connection.close()
            logger.info("Connexion à la base de données fermée")