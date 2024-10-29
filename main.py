from tilttracker.modules.discord_bot import TiltTrackerBot
import asyncio
import os
import platform
import sys
from datetime import datetime
from dotenv import load_dotenv
from tilttracker.utils.logger import setup_logger

# Configuration initiale
start_time = datetime.now()
logger = setup_logger(__name__)

def check_system_info():
    """Vérifie et log les informations système"""
    logger.info("=== Informations Système ===")
    logger.info(f"OS: {platform.system()} {platform.release()}")
    logger.info(f"Python version: {sys.version.split()[0]}")
    logger.info(f"Processeur: {platform.processor() or 'Non disponible'}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info("==========================")

def check_environment():
    """Vérifie et charge les variables d'environnement"""
    logger.info("=== Chargement Configuration ===")
    logger.info("Chargement du fichier .env...")
    load_dotenv(override=True)
    
    # Liste des variables requises
    required_vars = {
        'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN'),
        'RIOT_API_KEY': os.getenv('RIOT_API_KEY')
    }
    
    # Vérification de chaque variable
    missing_vars = []
    for var_name, var_value in required_vars.items():
        status = "✅ Présent" if var_value else "❌ Manquant"
        logger.info(f"{var_name}: {status}")
        if not var_value:
            missing_vars.append(var_name)
    
    logger.info("=============================")
    
    if missing_vars:
        error_msg = f"Variables manquantes dans .env: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return required_vars

async def main():
    """Fonction principale de lancement du bot"""
    logger.info("=== Démarrage TiltTracker ===")
    logger.info(f"Heure de démarrage: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Vérification système
        check_system_info()
        
        # Vérification configuration
        env_vars = check_environment()
        
        logger.info("=== Initialisation du Bot ===")
        logger.info("Création de l'instance du bot...")
        bot = TiltTrackerBot(riot_api_key=env_vars['RIOT_API_KEY'])
        
        logger.info("Tentative de connexion à Discord...")
        async with bot:
            logger.info("Démarrage du bot...")
            await bot.start(env_vars['DISCORD_TOKEN'])
            
    except Exception as e:
        logger.error("=== Erreur Critique ===")
        logger.error(f"Type d'erreur: {type(e).__name__}")
        logger.error(f"Description: {str(e)}")
        logger.error("=====================")
        raise
       
if __name__ == "__main__":
    try:
        logger.info("=== TiltTracker Bot ===")
        logger.info("Démarrage du processus principal...")
        asyncio.run(main())
        
    except KeyboardInterrupt:
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info("=== Arrêt du Bot ===")
        logger.info(f"Durée de fonctionnement: {duration}")
        logger.info("Arrêt propre du bot...")
        logger.info("Au revoir! 👋")
        
    except Exception as e:
        logger.error("=== Erreur Fatale ===")
        logger.error(f"Type: {type(e).__name__}")
        logger.error(f"Description: {str(e)}")
        logger.error("Le bot s'est arrêté de manière inattendue")
        logger.error("=====================")
        sys.exit(1)