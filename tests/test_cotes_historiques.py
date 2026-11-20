# tests/test_cotes_historiques.py
import datetime as dt, os, sqlite3, sys, types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB = sqlite3.connect(":memory:")
def db_execute(q, params=None, db_context=None):
    try:
        cur = DB.execute(q, params or []); DB.commit(); return cur.rowcount
    except Exception:
        return None
stub_db = types.ModuleType("users.db"); stub_db.db_execute = db_execute
sys.modules["users"] = types.ModuleType("users")
sys.modules["users"].__path__ = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "users")]
sys.modules["users.db"] = stub_db
stub_logs = types.ModuleType("core.utils.logs"); stub_logs.log_error = lambda *a, **k: None
sys.modules["core.utils.logs"] = stub_logs

from core import cotes_historiques as ch

def reset():
    DB.execute("DROP TABLE IF EXISTS cotes_snapshots"); DB.commit()

def cotes(bk="Bk1", h=2.0, d=3.5, a=3.8):
    return {"bookmaker": bk, "cote_home": h, "cote_draw": d, "cote_away": a}

def test_proba_marche_somme_1_et_marge_retiree():
    p = ch.proba_marche(2.0, 3.5, 3.8)
    assert abs(sum(p) - 1.0) < 1e-9
    assert p[0] > p[2] > 0

def test_cote_invalide_refusee():
    assert ch.proba_marche("?", 3.5, 3.8) is None
    assert ch.proba_marche(1.0, 3.5, 3.8) is None
    assert ch.proba_marche(None, 3.5, 3.8) is None

def test_enregistrement_et_deduplication_par_heure():
    reset()
    t = dt.datetime(2026, 11, 20, 10, 15, tzinfo=dt.timezone.utc)
    assert ch.enregistrer_snapshot("Lens", "Lille", [cotes()], t) == 1
    assert ch.enregistrer_snapshot("Lens", "Lille", [cotes()], t.replace(minute=40)) == 0  # même heure
    assert ch.enregistrer_snapshot("Lens", "Lille", [cotes()], t.replace(hour=11)) == 1     # heure suivante

def test_observations_invalides_ignorees():
    reset()
    t = dt.datetime(2026, 11, 20, 10, 0, tzinfo=dt.timezone.utc)
    n = ch.enregistrer_snapshot("A", "B", [cotes(h="?"), cotes(bk="Bk2")], t)
    assert n == 1

def test_observations_passees_jamais_modifiees():
    reset()
    t = dt.datetime(2026, 11, 20, 10, 0, tzinfo=dt.timezone.utc)
    ch.enregistrer_snapshot("A", "B", [cotes(h=2.0)], t)
    ch.enregistrer_snapshot("A", "B", [cotes(h=1.5)], t.replace(hour=11))
    rows = DB.execute("SELECT cote_h FROM cotes_snapshots ORDER BY date_capture").fetchall()
    assert rows == [(2.0,), (1.5,)], rows

if __name__ == "__main__":
    n = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); n += 1; print("✅", nom)
    print(f"{n} tests OK")
