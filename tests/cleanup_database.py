# tests/cleanup_database.py
import logging
from tilttracker.utils.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_database():
    db = Database()
    try:
        with db.connection.cursor() as cursor:
            # Désactiver temporairement les contraintes de clés étrangères
            cursor.execute("SET session_replication_role = replica;")
            
            # Supprimer toutes les données des tables dans le bon ordre
            logger.info("Suppression des données de toutes les tables...")
            
            # 1. Supprimer d'abord les tables dépendantes
            cursor.execute("TRUNCATE TABLE player_matches CASCADE")
            logger.info("Table player_matches vidée")
            
            cursor.execute("TRUNCATE TABLE matches CASCADE")
            logger.info("Table matches vidée")
            
            cursor.execute("TRUNCATE TABLE players CASCADE")
            logger.info("Table players vidée")
            
            # Réactiver les contraintes de clés étrangères
            cursor.execute("SET session_replication_role = DEFAULT;")
            
            # Réinitialiser les séquences d'ID auto-incrémentés
            cursor.execute("ALTER SEQUENCE players_id_seq RESTART WITH 1")
            cursor.execute("ALTER SEQUENCE matches_id_seq RESTART WITH 1")
            
        db.connection.commit()
        logger.info("Nettoyage complet de la base de données terminé avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")
        logger.exception(e)  # Affiche la stack trace complète
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_database()  