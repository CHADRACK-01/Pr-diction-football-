param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if ($Install) {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
}

python -m compileall -q app.py config.py ai_dev core scripts telegram_bot users tests entrainement
ruff check app.py config.py ai_dev core scripts telegram_bot users tests entrainement
pytest --cov=core --cov=users --cov=telegram_bot --cov-report=term-missing --cov-fail-under=80
