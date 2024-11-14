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
        """
        Stocke les performances d'un joueur pour un match donné.
        
        Args:
            match_id: ID du match dans la base de données
            player_data: Données du joueur incluant le rang dans l'équipe
        """
        try:
            logger.info(f"Enregistrement des performances pour le match {match_id}")
            
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO player_matches (
                        player_id, match_id, champion_id, champion_name,
                        kills, deaths, assists,
                        total_damage_dealt_to_champions, total_damage_taken,
                        damage_self_mitigated, total_time_crowd_control_dealt,
                        vision_score, gold_earned, win, team_id, score,
                        rank_in_team  -- Nouveau champ
                    ) VALUES (
                        %(player_id)s, %(match_id)s, %(champion_id)s, %(champion_name)s,
                        %(kills)s, %(deaths)s, %(assists)s,
                        %(total_damage_dealt_to_champions)s, %(total_damage_taken)s,
                        %(damage_self_mitigated)s, %(total_time_crowd_control_dealt)s,
                        %(vision_score)s, %(gold_earned)s, %(win)s, %(team_id)s, %(score)s,
                        %(rank_in_team)s  -- Nouveau champ
                    )
                """, player_data)
                
                self.connection.commit()
                logger.info(f"Performance du joueur stockée avec succès pour le match {match_id}")
                return True
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Erreur lors du stockage des performances du joueur: {e}")
            return False

    async def get_player_stats(self, game_name: str, tag_line: str) -> dict:
        """Récupère les statistiques et l'historique des parties d'un joueur"""
        try:
            logger.info(f"Début de la récupération des stats pour {game_name}#{tag_line}")
            
            # Vérifier d'abord si le joueur existe
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id 
                    FROM players 
                    WHERE summoner_name = %s AND tag_line = %s
                """, (game_name, tag_line))
                
                player = cursor.fetchone()
                if not player:
                    logger.error(f"Joueur {game_name}#{tag_line} non trouvé dans la base")
                    return None
                    
                player_id = player[0]
                logger.info(f"ID du joueur trouvé: {player_id}")
                
                # Puis récupérer ses stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_games,
                        SUM(CASE WHEN win THEN 1 ELSE 0 END) as wins,
                        ROUND(AVG(kills)::numeric, 2) as avg_kills,
                        ROUND(AVG(deaths)::numeric, 2) as avg_deaths,
                        ROUND(AVG(assists)::numeric, 2) as avg_assists,
                        ROUND(AVG(score)::numeric, 2) as avg_score,
                        MAX(score) as best_score,
                        SUM(score) as total_score
                    FROM player_matches
                    WHERE player_id = %s
                """, (player_id,))
                
                stats_row = cursor.fetchone()
                if not stats_row:
                    logger.error(f"Aucune statistique trouvée pour le joueur {player_id}")
                    return None

                stats = dict(zip([
                    'total_games', 'wins', 'avg_kills', 'avg_deaths', 
                    'avg_assists', 'avg_score', 'best_score', 'total_score'
                ], stats_row))

                logger.info("Récupération des parties récentes...")
                # Récupérer l'historique
                cursor.execute("""
                    SELECT 
                        pm.champion_name,
                        pm.kills,
                        pm.deaths,
                        pm.assists,
                        pm.total_damage_dealt_to_champions as damage,
                        pm.total_damage_taken as damage_taken,
                        pm.vision_score,
                        pm.score,
                        pm.win,
                        m.game_duration,
                        m.created_at
                    FROM player_matches pm
                    JOIN matches m ON m.id = pm.match_id
                    WHERE pm.player_id = %s
                    ORDER BY m.created_at DESC
                """, (player_id,))

                matches = []
                for row in cursor.fetchall():
                    match = {
                        'champion_name': row[0],
                        'kills': row[1],
                        'deaths': row[2],
                        'assists': row[3],
                        'damage': row[4],
                        'damage_taken': row[5],
                        'vision_score': row[6],
                        'score': row[7],
                        'win': row[8],
                        'duration': row[9] // 60,
                        'date': row[10].strftime('%Y-%m-%d %H:%M')
                    }
                    matches.append(match)

                logger.info(f"Nombre de parties trouvées: {len(matches)}")
                stats['match_history'] = matches
                return stats

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            logger.exception(e)
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

    async def get_player_score_history(self, game_name: str, tag_line: str) -> list:
        """Récupère l'historique des scores d'un joueur avec les détails de chaque partie"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pm.score,
                        pm.champion_name,
                        pm.win,
                        m.created_at,
                        pm.kills,
                        pm.deaths,
                        pm.assists
                    FROM player_matches pm
                    JOIN players p ON p.id = pm.player_id
                    JOIN matches m ON m.id = pm.match_id
                    WHERE p.summoner_name = %s 
                    AND p.tag_line = %s
                    ORDER BY m.created_at ASC
                """, (game_name, tag_line))
                
                matches = [
                    {
                        'score': row[0],
                        'champion': row[1],
                        'win': row[2],
                        'date': row[3].strftime('%Y-%m-%d %H:%M'),
                        'kda': f"{row[4]}/{row[5]}/{row[6]}"
                    }
                    for row in cursor.fetchall()
                ]
                
                return matches
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique pour {game_name}#{tag_line}: {e}")
            return []

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.connection:
            self.connection.close()
            logger.info("Connexion à la base de données fermée")