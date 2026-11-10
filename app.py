
# Application de consultation et de modification des notes
import os
import sqlite3

from flask import Flask, jsonify, request
import auth

app = Flask(__name__)

# Fichier où sont conservées les notes
DB = "notes.db"


# Prépare le registre des notes
def init_db():
    with sqlite3.connect(DB) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                etudiant TEXT,
                module TEXT,
                note REAL
            )
            """
        )

        if con.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
            con.executemany(
                "INSERT INTO notes (etudiant, module, note) VALUES (?, ?, ?)",
                [
                    ("Amina", "DevSecOps", 15.5),
                    ("Youssef", "DevSecOps", 12.0),
                ],
            )


init_db()


# Page d'accueil
@app.route("/")
def accueil():
    return (
        "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
        "<title>Notes des étudiants</title></head><body>"
        "<h1>Consultation des notes</h1>"
        "<p><a href='/notes'>Voir les notes</a></p></body></html>"
    )


# Vérification de disponibilité
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

    return jsonify([
        {"id": r[0], "etudiant": r[1], "module": r[2], "note": r[3]}
        for r in rows
    ])


# Modification sécurisée d'une note
@app.route("/notes/<int:note_id>", methods=["PUT"])
def modifier_note(note_id):

    # S2 : authentification obligatoire
    utilisateur = auth.utilisateur_connecte()

    if utilisateur is None:
        return jsonify(erreur="Authentification requise"), 401

    # S3 : seuls les enseignants peuvent modifier les notes
    if utilisateur.get("role") != "enseignant":
        return jsonify(erreur="Accès interdit"), 403

    donnees = request.get_json(silent=True) or {}
    nouvelle_note = donnees.get("note")

    # S5 : validation de la note
    if (
        isinstance(nouvelle_note, bool)
        or not isinstance(nouvelle_note, (int, float))
        or not 0 <= nouvelle_note <= 20
    ):
        return jsonify(erreur="Note invalide"), 400

    try:
        with sqlite3.connect(DB) as con:
            con.row_factory = sqlite3.Row

            # Rechercher la note avec une requête paramétrée
            ligne = con.execute(
                "SELECT id, module FROM notes WHERE id = ?",
                (note_id,),
            ).fetchone()

            if ligne is None:
                return jsonify(erreur="Note introuvable"), 404

            # S4 : l'enseignant ne peut modifier que son propre module
            if utilisateur.get("module") != ligne["module"]:
                return jsonify(erreur="Accès interdit"), 403

            # Mise à jour avec paramètres SQL
            con.execute(
                "UPDATE notes SET note = ? WHERE id = ?",
                (nouvelle_note, note_id),
            )

        return jsonify(message="Note modifiée avec succès"), 200

    except sqlite3.Error:
        # S7 : ne pas exposer les détails techniques
        app.logger.error("Erreur lors de la modification d'une note")
        return jsonify(erreur="Erreur interne du serveur"), 500


if __name__ == "__main__":
    app.run(
        host=os.environ.get("APP_HOST", "127.0.0.1"),
        port=5000,
    )
