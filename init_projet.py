import os
import sys
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

def check_environment():
    """Vérifie que toutes les variables d'environnement nécessaires sont présentes"""
    required_vars = [
        'DISCORD_TOKEN', 'DISCORD_WEBHOOK_URL', 'DISCORD_GUILD_ID',
        'DISCORD_CHANNEL_ID', 'RIOT_API_KEY', 'DB_USER', 'DB_PASSWORD',
        'DB_HOST', 'DB_PORT', 'DB_NAME'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
        sys.exit(1)
    
    logger.info("Toutes les variables d'environnement sont présentes")

def create_directory_structure():
    """Crée la structure de dossiers du projet"""
    directories = [
        'logs',
        'modules',
        'utils',
        'tests',
        'tests/unit',
        'tests/integration'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Dossier créé/vérifié: {directory}")

def main():
    """Fonction principale d'initialisation"""
    logger.info("Début de la configuration initiale")
    
    try:
        check_environment()
        create_directory_structure()
        logger.info("Configuration initiale terminée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la configuration: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()