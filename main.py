from tilttracker.modules.discord_bot import TiltTrackerBot
from tilttracker.modules.match_watcher import MatchWatcher
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
        'RIOT_API_KEY': os.getenv('RIOT_API_KEY'),
        'DISCORD_WEBHOOK_URL': os.getenv('DISCORD_WEBHOOK_URL')  # Ajout du webhook
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

async def match_checker(watcher: MatchWatcher):
    """Fonction de vérification périodique des matches"""
    while True:
        try:
            logger.info("Vérification des nouvelles parties...")
            players = watcher.get_registered_players()
            
            for player in players:
                logger.info(f"Vérification des parties de {player['summoner_name']}#{player['tag_line']}")
                watcher.process_new_matches(player)
                await asyncio.sleep(2)  # Pause entre chaque joueur
                
            await asyncio.sleep(60)  # Attendre 1 minute avant la prochaine vérification
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des parties: {e}")
            await asyncio.sleep(60)  # En cas d'erreur, attendre avant de réessayer

async def run_match_watcher(watcher: MatchWatcher):
    """Gère la surveillance des matches"""
    while True:
        try:
            logger.info("=== Début de la vérification des parties ===")
            players = await watcher.get_registered_players()
            
            logger.info(f"Nombre total de joueurs enregistrés: {len(players)}")
            
            for player in players:
                logger.info(f"Traitement du joueur: {player['summoner_name']}#{player['tag_line']}")
                await watcher.process_new_matches(player)
                await asyncio.sleep(5)  # Pause entre chaque joueur
                
            logger.info("=== Fin de la vérification des parties ===")
            logger.info("Attente de 60 secondes avant la prochaine vérification...")
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Erreur dans le watcher: {e}")
            logger.error("Attente avant nouvelle tentative...")
            await asyncio.sleep(60)


async def main():
    """Fonction principale de lancement du bot"""
    logger.info("=== Démarrage TiltTracker ===")
    logger.info(f"Heure de démarrage: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Vérification système
        check_system_info()
        
        # Vérification configuration
        env_vars = check_environment()
        riot_api_key = env_vars['RIOT_API_KEY']
        
        logger.info("=== Initialisation du Bot ===")
        logger.info("Création de l'instance du bot...")
        bot = TiltTrackerBot(riot_api_key=riot_api_key)
        
        # Initialisation du watcher
        logger.info("=== Initialisation du Match Watcher ===")
        watcher = MatchWatcher(riot_api_key=riot_api_key)
        
        # Création des tâches asynchrones
        logger.info("Démarrage des services...")
        tasks = [
            asyncio.create_task(bot.start(env_vars['DISCORD_TOKEN'])),
            asyncio.create_task(run_match_watcher(watcher))
        ]
        
        # Exécution des tâches
        try:
            logger.info("Bot et Watcher démarrés avec succès")
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Arrêt des services demandé")
        finally:
            # Nettoyage
            for task in tasks:
                task.cancel()
            watcher.cleanup()
            
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