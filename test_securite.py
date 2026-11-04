
# ============================================================
# Exigences de sécurité vérifiées automatiquement
# ============================================================

import json
import pytest

import app as application
import auth
from app import app

client = app.test_client()

# Comptes fictifs utilisés pendant les vérifications
JETONS = {
    "jeton-prof-devsecops": {
        "nom": "Pr. Alami",
        "role": "enseignant",
        "module": "DevSecOps"
    },
    "jeton-prof-java": {
        "nom": "Pr. Bennani",
        "role": "enseignant",
        "module": "Java"
    },
    "jeton-amina": {
        "nom": "Amina",
        "role": "etudiant",
        "module": None
    },
}


# Chaque vérification utilise un registre de notes et des comptes de test,
# sans jamais toucher aux vraies notes
@pytest.fixture(autouse=True)
def environnement_de_test(tmp_path, monkeypatch):
    fichier = tmp_path / "jetons.json"
    fichier.write_text(json.dumps(JETONS), encoding="utf-8")

    monkeypatch.setattr(auth, "FICHIER_JETONS", str(fichier))
    monkeypatch.setattr(application, "DB", str(tmp_path / "notes.db"))

    application.init_db()


# Demande de modification de la note n° 1, avec ou sans jeton
def modifier(note, jeton=None):
    entetes = {"Authorization": f"Bearer {jeton}"} if jeton else {}
    return client.put(
        "/notes/1",
        json={"note": note},
        headers=entetes
    )


# S1 : la recherche par nom résiste à l'injection SQL
def test_recherche_resiste_a_l_injection():
    reponse = client.get(
        "/notes",
        query_string={"etudiant": "' OR '1'='1"}
    )
    assert reponse.get_json() == []


# S2 : personne ne modifie une note sans être identifié
def test_modification_refusee_sans_identification():
    assert modifier(18).status_code == 401


# S3 : un étudiant ne peut pas modifier une note
def test_modification_refusee_a_un_etudiant():
    assert modifier(20, "jeton-amina").status_code == 403


# S4 : un enseignant ne modifie pas les notes d'un autre module
def test_modification_refusee_a_un_autre_module():
    assert modifier(18, "jeton-prof-java").status_code == 403


# S5 : une note doit être un nombre entre 0 et 20
def test_note_invalide_refusee():
    assert modifier(25, "jeton-prof-devsecops").status_code == 400
    assert modifier("20 WHERE 1=1", "jeton-prof-devsecops").status_code == 400


# S6 : l'enseignant du module peut modifier la note de son étudiant
def test_modification_par_l_enseignant_du_module():
    assert modifier(17, "jeton-prof-devsecops").status_code == 200

    reponse = client.get(
        "/notes",
        query_string={"etudiant": "Amina"}
    )
    assert reponse.get_json()[0]["note"] == 17


# S7 : en cas de problème, aucun détail technique n'est montré
def test_erreur_sans_detail_technique(tmp_path, monkeypatch):
    monkeypatch.setattr(
        application,
        "DB",
        str(tmp_path / "absent" / "notes.db")
    )

    reponse = modifier(15, "jeton-prof-devsecops")

    assert reponse.status_code == 500
    assert "database" not in reponse.get_data(as_text=True).lower()
