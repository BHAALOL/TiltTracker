import sys
import os
from pathlib import Path
import logging
from typing import Optional

# Configuration du logging en début de fichier
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

import uvicorn
from fastapi import Request, HTTPException
from tilttracker.modules.web import create_app
from tilttracker.utils.database import Database
from tilttracker.modules.teamspeak_manager import TeamSpeakManager
import asyncio

app, templates = create_app()
db = Database()

# Initialisation du manager TeamSpeak
ts_manager = TeamSpeakManager()

# Variable globale pour stocker le statut
ts_status = {
    'status': 'offline',
    'channels': None,
    'last_update': None
}

# Fonction de mise à jour du statut TeamSpeak
async def update_ts_status():
    global ts_status
    while True:
        try:
            new_status = ts_manager.get_server_status()
            if new_status:
                ts_status.update(new_status)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut TS: {e}")
        await asyncio.sleep(30)

# Événement de démarrage
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_ts_status())

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "ts_status": ts_status
        }
    )

@app.get("/leaderboard")
async def leaderboard(request: Request):
    try:
        players = await db.get_leaderboard(limit=100)
        return templates.TemplateResponse(
            "leaderboard.html",
            {
                "request": request,
                "players": players
            }
        )
    except Exception as e:
        logger.error(f"Erreur dans leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{game_name}/{tag_line}")
async def player_details(request: Request, game_name: str, tag_line: str):
    try:
        logger.debug(f"Tentative d'accès à la page joueur pour {game_name}#{tag_line}")
        
        # Vérifier le joueur dans la base de données
        with db.connection.cursor() as cursor:
            logger.debug("Exécution de la requête de vérification du joueur")
            cursor.execute("""
                SELECT summoner_name, tag_line 
                FROM players 
                WHERE summoner_name = %s AND tag_line = %s
            """, (game_name, tag_line))
            
            player = cursor.fetchone()
            logger.debug(f"Résultat de la requête joueur: {player}")

        if not player:
            logger.warning(f"Joueur non trouvé: {game_name}#{tag_line}")
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "message": f"Joueur {game_name}#{tag_line} non trouvé"
                },
                status_code=404
            )

        stats = await db.get_player_stats(game_name, tag_line)
        logger.debug(f"Stats récupérées: {stats}")
        
        if not stats:
            logger.error(f"Aucune statistique trouvée pour {game_name}#{tag_line}")
            raise HTTPException(status_code=404, detail="Statistiques non trouvées")

        required_stats = {
            'summoner_name': game_name,
            'tag_line': tag_line,
            'total_score': stats.get('total_score', 0),
            'total_games': stats.get('total_games', 0),
            'wins': stats.get('wins', 0),
            'avg_kills': float(stats.get('avg_kills', 0)),
            'avg_deaths': float(stats.get('avg_deaths', 0)),
            'avg_assists': float(stats.get('avg_assists', 0)),
            'avg_score': float(stats.get('avg_score', 0)),
            'best_score': stats.get('best_score', 0),
            'winrate': (stats.get('wins', 0) / stats.get('total_games', 1)) * 100 if stats.get('total_games', 0) > 0 else 0,
            'kda_ratio': 0,
            'match_history': stats.get('match_history', [])
        }

        logger.debug(f"Stats formatées: {required_stats}")

        return templates.TemplateResponse(
            "player.html",
            {
                "request": request,
                "stats": required_stats
            }
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compare/{player1_name}/{player1_tag}/{player2_name}/{player2_tag}")
async def compare_players(
    request: Request, 
    player1_name: str, 
    player1_tag: str,
    player2_name: str, 
    player2_tag: str
):
    try:
        # Récupérer les stats des deux joueurs
        player1_stats = await db.get_player_stats(player1_name, player1_tag)
        player2_stats = await db.get_player_stats(player2_name, player2_tag)
        
        if not player1_stats or not player2_stats:
            raise HTTPException(status_code=404, detail="Un ou plusieurs joueurs non trouvés")

        # Ajouter explicitement les noms des joueurs
        player1_stats['summoner_name'] = player1_name
        player1_stats['tag_line'] = player1_tag
        player2_stats['summoner_name'] = player2_name
        player2_stats['tag_line'] = player2_tag

        # Calculer winrate pour chaque joueur
        player1_winrate = (player1_stats['wins'] / player1_stats['total_games'] * 100) if player1_stats['total_games'] > 0 else 0
        player2_winrate = (player2_stats['wins'] / player2_stats['total_games'] * 100) if player2_stats['total_games'] > 0 else 0

        comparison = {
            'kda': {
                'player1': {
                    'kills': player1_stats['avg_kills'],
                    'deaths': player1_stats['avg_deaths'],
                    'assists': player1_stats['avg_assists']
                },
                'player2': {
                    'kills': player2_stats['avg_kills'],
                    'deaths': player2_stats['avg_deaths'],
                    'assists': player2_stats['avg_assists']
                },
                'difference': {
                    'kills': player1_stats['avg_kills'] - player2_stats['avg_kills'],
                    'deaths': player1_stats['avg_deaths'] - player2_stats['avg_deaths'],
                    'assists': player1_stats['avg_assists'] - player2_stats['avg_assists']
                }
            },
            'performance': {
                'player1': {
                    'winrate': player1_winrate,
                    'avg_score': player1_stats['avg_score']
                },
                'player2': {
                    'winrate': player2_winrate,
                    'avg_score': player2_stats['avg_score']
                },
                'difference': {
                    'winrate': player1_winrate - player2_winrate,
                    'avg_score': player1_stats['avg_score'] - player2_stats['avg_score']
                }
            }
        }

        # Ajouter des informations supplémentaires pour chaque joueur
        player1_stats['winrate'] = player1_winrate
        player2_stats['winrate'] = player2_winrate

        return templates.TemplateResponse(
            "compare.html",
            {
                "request": request,
                "player1": player1_stats,
                "player2": player2_stats,
                "comparison": comparison
            }
        )
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/poke/{client_id}")
async def poke_user(request: Request, client_id: str):
    try:
        success = ts_manager.poke_user(client_id)
        if success:
            return {"status": "success"}
        return {"status": "error", "message": "Échec de l'envoi du poke"}
    except Exception as e:
        logger.error(f"Erreur lors du poke: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    try:
        uvicorn.run(
            "run_web:app", 
            host="0.0.0.0",
            port=8084, 
            reload=True
        )
    finally:
        db.close()