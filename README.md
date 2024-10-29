# League of Legends Ranking System

## Description
Système de ranking pour League of Legends avec intégration Discord. Le système permet de suivre les performances des joueurs, calculer leur classement et partager les résultats via Discord.

## Fonctionnalités
- Inscription des joueurs via Discord
- Suivi automatique des parties
- Calcul du classement
- Publication des résultats sur Discord
- Interface d'administration

## Prérequis
- Python 3.8+
- Docker et Docker Compose
- Compte développeur Riot Games
- Bot Discord

## Installation

1. Cloner le dépôt
```bash
git clone https://github.com/votre-username/league-ranking.git
cd league-ranking

Créer et activer l'environnement virtuel
```
2. Créer et activer l'environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```
3. Installer les dépendances
```bash 
pip install -r requirements.txt
```
4. Configurer les variables d'environnement 
Copier le fichier .env.example vers .env et remplir les variables nécessaires :
```bash 
cp .env.example .env
```
5. Lancer la base de données
```bash 
cp .env.example .env
```
6. Initialiser la base de données
```bash 
python setup.py
```

##Structure du Projet
```bash
TiltTracker/
├── main.py
├── setup.py
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── modules/
│   ├── discord_bot.py
│   ├── riot_api.py
│   ├── game_processor.py
│   └── discord_publisher.py
├── utils/
│   ├── logger.py
│   ├── database.py
│   └── config.py
└── tests/
    ├── unit/
    └── integration/
```
