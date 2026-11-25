$root = (Get-Location).Path
$files = Get-ChildItem -Recurse -File -Filter *.py | Where-Object { $_.FullName -notmatch '\\\.venv\\|__pycache__' }

function Cherche($motif) {
    "### MOTIF: $motif"
    $c = 0
    foreach ($f in $files) {
        $rel = $f.FullName.Substring($root.Length + 1)
        $n = 0
        foreach ($l in (Get-Content -LiteralPath $f.FullName)) {
            $n++
            if ($l -match $motif) {
                $c++
                "  {0}:{1}: {2}" -f $rel, $n, $l.Trim()
            }
        }
    }
    "  -- total: $c"
    ""
}

Cherche 'FICHIERS_INTERDITS'
Cherche 'gemini-'
Cherche '8653408729'
Cherche 'subprocess'
