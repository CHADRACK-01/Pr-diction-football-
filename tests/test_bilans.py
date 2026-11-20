# tests/test_bilans.py
import datetime as dt, math, os, sqlite3, sys, types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB = sqlite3.connect(":memory:")
DB.execute("CREATE TABLE matchs (date TEXT, home_team TEXT, away_team TEXT, fthg INTEGER, ftag INTEGER, ftr TEXT)")
JOUR = {"date": dt.date(2026, 11, 20)}

def db_execute(q, params=None, db_context=None):
    try:
        cur = DB.execute(q, params or []); DB.commit(); return cur.rowcount
    except Exception:
        return None
def db_fetchone(q, params=None, db_context=None):
    return DB.execute(q, params or []).fetchone()
def db_fetchall(q, params=None, db_context=None):
    return DB.execute(q, params or []).fetchall()

stub_db = types.ModuleType("users.db")
stub_db.db_execute, stub_db.db_fetchone, stub_db.db_fetchall = db_execute, db_fetchone, db_fetchall
sys.modules["users"] = types.ModuleType("users")
sys.modules["users"].__path__ = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "users")]
sys.modules["users.db"] = stub_db
stub_logs = types.ModuleType("core.utils.logs")
stub_logs.log_error = lambda *a, **k: None; stub_logs.log_info = lambda *a, **k: None
sys.modules["core.utils.logs"] = stub_logs
stub_ml = types.ModuleType("core.ml_model")
stub_ml.TZ_KINSHASA = dt.timezone(dt.timedelta(hours=1))
sys.modules["core.ml_model"] = stub_ml

from core import bilans as b

def reset():
    DB.execute("DROP TABLE IF EXISTS estimations"); DB.execute("DELETE FROM matchs"); DB.commit()

def test_enregistrement_une_fois_par_jour():
    reset()
    assert b.enregistrer_estimation("A", "B", 0.5, 0.25, 0.25) is True
    assert b.enregistrer_estimation("A", "B", 0.5, 0.25, 0.25) is False

def test_refus_si_match_deja_joue():
    reset()
    DB.execute("INSERT INTO matchs VALUES ('2026-11-20', 'A', 'B', 2, 1, 'H')"); DB.commit()
    assert b.enregistrer_estimation("A", "B", 0.5, 0.25, 0.25) is False

def test_refus_si_probabilites_absentes():
    reset()
    assert b.enregistrer_estimation("A", "B", None, 0.2, 0.3) is False

def test_resolution_puis_bilan_exact():
    reset()
    b.enregistrer_estimation("A", "B", 0.6, 0.2, 0.2)   # pick = H
    b.enregistrer_estimation("C", "D", 0.2, 0.2, 0.6)   # pick = A
    # Résultats joués ensuite (date >= aujourd'hui)
    DB.execute("INSERT INTO matchs VALUES ('2026-11-21', 'A', 'B', 1, 0, 'H')")  # pick juste
    DB.execute("INSERT INTO matchs VALUES ('2026-11-21', 'C', 'D', 2, 2, 'D')")  # pick faux
    DB.commit()
    assert b.resoudre_estimations() == 2
    s = b.statistiques()
    assert s["resolues"] == 2 and s["enregistrees"] == 2
    assert abs(s["precision"] - 0.5) < 1e-9
    attendu = -(math.log(0.6) + math.log(0.2)) / 2
    assert abs(s["log_loss"] - attendu) < 1e-9, (s["log_loss"], attendu)

def test_bilan_vide_sans_division_par_zero():
    reset()
    assert b.statistiques()["resolues"] == 0

def test_aucune_estimation_non_enregistree_nest_comptee():
    reset()
    b.enregistrer_estimation("A", "B", 0.5, 0.3, 0.2)
    assert b.statistiques()["resolues"] == 0   # pas encore de résultat

if __name__ == "__main__":
    n = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); n += 1; print("✅", nom)
    print(f"{n} tests OK")
