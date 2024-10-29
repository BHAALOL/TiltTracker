# tests/verify_data.py
import logging
from tilttracker.utils.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_data():
    db = Database()
    try:
        with db.connection.cursor() as cursor:
            # Statistiques générales
            logger.info("=== Statistiques Générales ===")
            cursor.execute("SELECT COUNT(*) FROM matches")
            matches_count = cursor.fetchone()[0]
            logger.info(f"Nombre total de parties: {matches_count}")

            cursor.execute("SELECT COUNT(*) FROM player_matches")
            performances_count = cursor.fetchone()[0]
            logger.info(f"Nombre total de performances: {performances_count}")

            # Détails des dernières parties
            logger.info("\n=== 5 Dernières Parties ===")
            cursor.execute("""
                SELECT 
                    m.match_id,
                    p.summoner_name,
                    pm.champion_name,
                    pm.kills,
                    pm.deaths,
                    pm.assists,
                    pm.total_damage_dealt_to_champions as damage,
                    CASE WHEN pm.win THEN 'Victoire' ELSE 'Défaite' END as resultat
                FROM player_matches pm
                JOIN matches m ON m.id = pm.match_id
                JOIN players p ON p.id = pm.player_id
                ORDER BY m.created_at DESC
                LIMIT 5
            """)
            
            matches = cursor.fetchall()
            for match in matches:
                logger.info(
                    f"Match {match[0]}: {match[1]} avec {match[2]} - "
                    f"{match[3]}/{match[4]}/{match[5]} - "
                    f"{match[6]} dégâts - {match[7]}"
                )

            # Statistiques moyennes
            logger.info("\n=== Statistiques Moyennes ===")
            cursor.execute("""
                SELECT 
                    AVG(kills) as avg_kills,
                    AVG(deaths) as avg_deaths,
                    AVG(assists) as avg_assists,
                    AVG(total_damage_dealt_to_champions) as avg_damage,
                    COUNT(CASE WHEN win THEN 1 END)::float / COUNT(*) * 100 as winrate
                FROM player_matches
            """)
            
            stats = cursor.fetchone()
            logger.info(f"KDA Moyen: {stats[0]:.1f}/{stats[1]:.1f}/{stats[2]:.1f}")
            logger.info(f"Dégâts Moyens: {stats[3]:.0f}")
            logger.info(f"Winrate: {stats[4]:.1f}%")

    except Exception as e:
        logger.error(f"Erreur lors de la vérification: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_data()