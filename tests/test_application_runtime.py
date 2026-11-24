"""Tests du conteneur applicatif orienté objet."""

from types import SimpleNamespace

from web.application import ApplicationRuntime


class _FakeApp:
    pass


class _FakeBot:
    pass


def test_runtime_test_mode_ne_demarre_pas_scheduler(monkeypatch):
    scheduled = []
    monkeypatch.setattr(
        "web.application.threading.Thread",
        lambda *args, **kwargs: scheduled.append((args, kwargs)),
    )

    runtime = ApplicationRuntime(
        app=_FakeApp(),
        bot=_FakeBot(),
        config=SimpleNamespace(MODE_TEST=True, MODE_VITRINE=False),
        initialiser_bdd=lambda: None,
        scheduler_callback=lambda: None,
    )

    runtime.start_scheduler()
    assert scheduled == []


def test_runtime_vitrine_ne_demarre_pas_scheduler(monkeypatch):
    scheduled = []
    monkeypatch.setattr(
        "web.application.threading.Thread",
        lambda *args, **kwargs: scheduled.append((args, kwargs)),
    )

    runtime = ApplicationRuntime(
        app=_FakeApp(),
        bot=_FakeBot(),
        config=SimpleNamespace(MODE_TEST=False, MODE_VITRINE=True),
        initialiser_bdd=lambda: None,
        scheduler_callback=lambda: None,
    )

    runtime.start_scheduler()
    assert scheduled == []
