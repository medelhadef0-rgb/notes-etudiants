# Identification des utilisateurs de l'application des notes

import json
import os
from flask import request

# Les jetons sont conservés dans un fichier séparé
FICHIER_JETONS = os.environ.get("FICHIER_JETONS", "jetons.json")


def utilisateur_connecte():
    entete = request.headers.get("Authorization", "")

    # Vérifier la présence du jeton Bearer
    if not entete.startswith("Bearer "):
        return None

    try:
        with open(FICHIER_JETONS, encoding="utf-8") as fichier:
            jetons = json.load(fichier)

    except (FileNotFoundError, json.JSONDecodeError):
        return None

    jeton = entete.removeprefix("Bearer ")
    return jetons.get(jeton)