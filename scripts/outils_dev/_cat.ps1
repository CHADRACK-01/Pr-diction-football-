function StatsCatalog($chemin, $motif) {
    $s = Get-Content -LiteralPath $chemin -Raw
    $m = [regex]::Matches($s, $motif)
    "Fichier : $chemin"
    "  entrees detectees : " + $m.Count
    $st = @{}
    foreach ($x in $m) {
        $statut = $x.Groups[4].Value
        if (-not $st.ContainsKey($statut)) { $st[$statut] = 0 }
        $st[$statut]++
    }
    foreach ($k in $st.Keys) { "    {0,-14} {1}" -f $k, $st[$k] }
    ""
}

StatsCatalog "core\catalog\catalogue_fonctionnalites.py" '\("(\d+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)'
StatsCatalog "core\catalog\catalogue_extensions.py" '"(\d+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"'
StatsCatalog "core\catalog\fonctionnalites_700.py" '"(\d+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"'

"=== TAILLE DES FICHIERS CATALOGUE ==="
Get-ChildItem core\catalog -File | ForEach-Object { "{0,6} lignes  {1}" -f (Get-Content -LiteralPath $_.FullName).Count, $_.Name }
