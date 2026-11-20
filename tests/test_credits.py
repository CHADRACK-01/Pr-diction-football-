# tests/test_credits.py
import os, sqlite3, sys, types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB = sqlite3.connect(":memory:")
ETAT = {"ajouts": [], "echec": False}

def db_execute(q, params=None, db_context=None):
    try:
        cur = DB.execute(q, params or [])
        DB.commit()
        return cur.rowcount
    except Exception:
        return None

def db_fetchone(q, params=None, db_context=None):
    return DB.execute(q, params or []).fetchone()

stub_db = types.ModuleType("users.db"); stub_db.db_execute = db_execute; stub_db.db_fetchone = db_fetchone
sys.modules["users"] = types.ModuleType("users"); sys.modules["users"].__path__ = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "users")]
sys.modules["users.db"] = stub_db
stub_logs = types.ModuleType("core.utils.logs")
stub_logs.log_error = lambda *a, **k: None; stub_logs.log_info = lambda *a, **k: None
sys.modules["core.utils.logs"] = stub_logs
stub_acc = types.ModuleType("users.account_base")
def ajouter_jours_premium(user_id, jours):
    if ETAT["echec"]:
        return False
    ETAT["ajouts"].append((user_id, jours))
    return True
stub_acc.ajouter_jours_premium = ajouter_jours_premium
sys.modules["users.account_base"] = stub_acc

from users import credits as cr

def reset():
    DB.execute("DROP TABLE IF EXISTS credits_premium")
    DB.commit()
    ETAT["ajouts"].clear(); ETAT["echec"] = False

def test_credit_une_seule_fois():
    reset()
    assert cr.crediter_premium("paiement:1", 42, 30, "paiement") == "ok"
    assert cr.crediter_premium("paiement:1", 42, 30, "paiement") == "deja"
    assert cr.crediter_premium("paiement:1", 42, 30, "paiement") == "deja"
    assert ETAT["ajouts"] == [(42, 30)], ETAT["ajouts"]

def test_references_differentes_creditent_chacune():
    reset()
    assert cr.crediter_premium("parrainage:7", 7, 1) == "ok"
    assert cr.crediter_premium("parrainage:8", 7, 1) == "ok"
    assert len(ETAT["ajouts"]) == 2

def test_echec_libere_la_reservation_puis_reessai_ok():
    reset()
    ETAT["echec"] = True
    assert cr.crediter_premium("code:ABC", 5, 7, "code") == "echec"
    assert not cr.deja_credite("code:ABC"), "la réservation aurait dû être libérée"
    ETAT["echec"] = False
    assert cr.crediter_premium("code:ABC", 5, 7, "code") == "ok"
    assert ETAT["ajouts"] == [(5, 7)]

def test_parametres_invalides_refuses():
    reset()
    assert cr.crediter_premium("", 1, 1) == "echec"
    assert cr.crediter_premium("x", "1", 1) == "echec"
    assert cr.crediter_premium("x", 1, 0) == "echec"
    assert ETAT["ajouts"] == []

def test_deja_credite_reflete_letat():
    reset()
    assert cr.deja_credite("paiement:9") is False
    cr.crediter_premium("paiement:9", 9, 30)
    assert cr.deja_credite("paiement:9") is True

if __name__ == "__main__":
    n = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); n += 1; print("✅", nom)
    print(f"{n} tests OK")
