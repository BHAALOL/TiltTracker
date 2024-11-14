from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

def create_app():
    app = FastAPI(title="TiltTracker Web")
    
    # Montage des fichiers statiques
    app.mount("/static", StaticFiles(directory="tilttracker/modules/web/static"), name="static")
    
    # Configuration des templates
    templates = Jinja2Templates(directory="tilttracker/modules/web/templates")
    
    return app, templates