# Bu klasör image'a GİRMEMELİ (.dockerignore → tests/)
from app import app


def test_bilgi():
    yanit = app.test_client().get("/")
    assert yanit.status_code == 200
