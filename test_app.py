from app import app
client = app.test_client()

def test_accueil():
    reponse = client.get("/")
    assert reponse.status_code == 200

def test_health():
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.get_json()["status"] == "ok"

def test_liste_notes():
    reponse = client.get("/notes")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) >= 2

def test_recherche_etudiant():
    reponse = client.get("/notes?etudiant=Amina")
    assert reponse.get_json()[0]["note"] == 15.5

def test_version():
    reponse = client.get("/health")
    assert reponse.get_json()["version"] == "1.0"    