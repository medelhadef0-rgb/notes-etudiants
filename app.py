#Application de consultation des notes des étudiants
from auth import utilisateur_connecte
import os
import sqlite3
from flask import Flask, jsonify, request
app = Flask(__name__)
#Fichier où sont conservées les notes de l'école
DB = "notes.db"
# Prépare le registre des notes au démarrage de l'application
def init_db():
    with sqlite3.connect(DB) as con:
        # Chaque note concerne un étudiant, dans un module
        con.execute(
            "CREATE TABLE IF NOT EXISTS notes "
            "(id INTEGER PRIMARY KEY, etudiant TEXT, module TEXT, note REAL)"
        )
        #Si le registre est vide, on y inscrit deux notes d'exemple
        if con.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
            con.executemany(
                "INSERT INTO notes (etudiant, module, note) VALUES (?, ?, ?)",
                [("Amina", "DevSecOps", 15.5), ("Youssef", "DevSecOps", 12.0)]
            )
init_db()
# Page d'accueil
@app.route("/")
def accueil():
    return (
        "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
        "<title>Notes des etudiants</title></head><body>"
        "<h1>Consultation des notes</h1>"
        "<p><a href='/notes'>Voir les notes</a></p></body></html>"
    )
# Indique que le service des notes est disponible
# Indique que le service des notes est disponible
@app.route("/health")
def health():
    return jsonify(status="ok", version="1.0")
# Consultation des notes
@app.route("/notes")
def lister_notes():
    etudiant = request.args.get("etudiant", "")
    with sqlite3.connect(DB) as con:
        rows = con.execute(
            "SELECT id, etudiant, module, note FROM notes WHERE etudiant LIKE ?",
            (f"%{etudiant}%",),
        ).fetchall()
    return jsonify(
        [{"id": r[0], "etudiant": r[1], "module": r[2], "note": r[3]} for r in rows]
    )
if __name__ == "__main__":
    app.run(host=os.environ.get("APP_HOST", "127.0.0.1"), port=5000)
    
@app.route("/notes/<note_id>", methods=["PUT"])
def modifier_note(note_id):
    utilisateur = utilisateur_connecte()

    # S2 : authentification
    if utilisateur is None:
        return {"erreur": "Authentification requise"}, 401

    # S3 : seuls les enseignants peuvent modifier
    if utilisateur.get("role") != "enseignant":
        return {"erreur": "Accès interdit"}, 403

    # Lire et valider les données JSON
    donnees = request.get_json(silent=True)

    if not isinstance(donnees, dict):
        return {"erreur": "Données invalides"}, 400

    note = donnees.get("note")

    # S5 : validation de la note
    if (
        isinstance(note, bool)
        or not isinstance(note, (int, float))
        or not 0 <= note <= 20
    ):
        return {"erreur": "Note invalide"}, 400

    try:
        con = sqlite3.connect(DB)
        try:
            # Adapter cette requête à la structure de la base
            curseur = con.execute(
                "UPDATE notes SET note = ? WHERE id = ?",
                (note, note_id)
            )

            if curseur.rowcount == 0:
                con.rollback()
                return {"erreur": "Note introuvable"}, 404

            con.commit()
            return {"message": "Note modifiée"}, 200

        finally:
            con.close()

    except sqlite3.Error:
        app.logger.exception("Erreur lors de la modification d'une note")
        return {"erreur": "Erreur interne"}, 500
