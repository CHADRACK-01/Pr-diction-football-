"""Contrats d'import pour les routes HTTP extraites."""


def test_modules_routes_sont_importables():
    from web.routes_admin import register_admin_routes
    from web.routes_public import register_public_routes

    assert callable(register_public_routes)
    assert callable(register_admin_routes)
