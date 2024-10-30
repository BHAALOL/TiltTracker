# tilttracker/modules/discord_publisher.py
import logging
import discord
from discord import Embed, Colour
import os
from typing import Dict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class DiscordPublisher:
    def __init__(self):
        load_dotenv()
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL non trouvée dans les variables d'environnement")

    def create_match_embed(self, player_stats: Dict, match_stats: Dict, score_info: Dict) -> Embed:
        """
        Crée un embed Discord pour une partie.
        """
        # Déterminer la couleur selon la victoire/défaite
        color = Colour.green() if player_stats['win'] else Colour.red()
        
        # Construire le titre avec le nom d'invocateur
        title = (f"{player_stats['summoner_name']}#{player_stats['tag_line']} "
                f"- {player_stats['champion_name']} "
                f"{'✅' if player_stats['win'] else '❌'}")
        
        # Créer l'embed
        embed = Embed(
            title=title,
            color=color
        )

        # Description avec résultat de la partie
        embed.description = "🏆 Victoire" if player_stats['win'] else "💀 Défaite"

        # Ajouter l'image du champion (si disponible)
        champion_image_url = f"http://ddragon.leagueoflegends.com/cdn/14.21.1/img/champion/{player_stats['champion_name']}.png"
        embed.set_thumbnail(url=champion_image_url)

        # Stats KDA
        kda = f"{player_stats['kills']}/{player_stats['deaths']}/{player_stats['assists']}"
        kda_ratio = (player_stats['kills'] + player_stats['assists']) / max(1, player_stats['deaths'])
        embed.add_field(
            name="KDA",
            value=f"{kda} ({kda_ratio:.2f})",
            inline=True
        )

        # Dégâts
        dmg_formatted = "{:,}".format(player_stats['total_damage_dealt_to_champions']).replace(',', ' ')
        embed.add_field(
            name="Dégâts aux champions",
            value=dmg_formatted,
            inline=True
        )

        # Dégâts tank
        tank_dmg = "{:,}".format(player_stats['total_damage_taken']).replace(',', ' ')
        embed.add_field(
            name="Dégâts subis",
            value=tank_dmg,
            inline=True
        )

        # Score et Points
        points = score_info['final_score']
        points_str = f"+{points}" if points > 0 else str(points)
        embed.add_field(
            name="Score de performance",
            value=f"{score_info['base_score']:.1f}%",
            inline=True
        )
        embed.add_field(
            name="Points",
            value=points_str,
            inline=True
        )

        # Nouveau total de points (si disponible)
        if 'total_points' in score_info:
            embed.add_field(
                name="Total",
                value=str(score_info['total_points']),
                inline=True
            )

        # Footer avec des infos supplémentaires
        match_duration = match_stats.get('game_duration', 0) // 60  # Convertir en minutes
        match_id = match_stats.get('match_id', 'N/A')
        embed.set_footer(text=f"Durée: {match_duration} minutes | Match ID: {match_id}")

        return embed

    def create_performance_message(self, score_info: Dict) -> str:
        """
        Crée un message d'analyse de la performance.
        """
        performance = score_info['base_score']
        if performance >= 90:
            return "🌟 Performance exceptionnelle! Continue comme ça!"
        elif performance >= 75:
            return "💪 Très belle performance!"
        elif performance >= 60:
            return "👍 Bonne performance."
        elif performance >= 45:
            return "😐 Performance moyenne."
        elif performance >= 30:
            return "😕 Performance en dessous de la moyenne."
        else:
            return "😢 Performance difficile. Ne te décourage pas!"

    async def publish_match_result(self, player_stats: Dict, match_stats: Dict, score_info: Dict):
        """
        Publie les résultats d'une partie sur Discord.
        """
        try:
            webhook = discord.Webhook.from_url(self.webhook_url, adapter=discord.AsyncWebhookAdapter())
            
            # Créer l'embed
            embed = self.create_match_embed(player_stats, match_stats, score_info)
            
            # Créer le message d'accompagnement
            message = self.create_performance_message(score_info)
            
            # Envoyer le message
            await webhook.send(
                content=message,
                embed=embed,
                username="TiltTracker"
            )
            
            logger.info(f"Résultats publiés avec succès pour {player_stats['champion_name']}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur Discord: {e}")
            raise

    def publish_match_result_sync(self, player_stats: Dict, match_stats: Dict, score_info: Dict):
        """
        Version synchrone de la publication (pour les tests).
        """
        try:
            import requests
            
            # Créer l'embed
            embed = self.create_match_embed(player_stats, match_stats, score_info)
            message = self.create_performance_message(score_info)
            
            # Convertir l'embed en format webhook Discord
            webhook_data = {
                "content": message,
                "embeds": [embed.to_dict()],
                "username": "TiltTracker"
            }
            
            # Envoyer à Discord
            response = requests.post(self.webhook_url, json=webhook_data)
            response.raise_for_status()
            
            logger.info(f"Résultats publiés avec succès pour {player_stats['champion_name']}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur Discord: {e}")
            raise