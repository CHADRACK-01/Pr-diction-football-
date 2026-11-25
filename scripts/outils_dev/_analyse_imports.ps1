$root = (Get-Location).Path
$files = Get-ChildItem -Recurse -File -Filter *.py | Where-Object { $_.FullName -notmatch '\\\.venv\\|__pycache__' }
$mods = @{}
$src = @{}
foreach ($f in $files) {
    $rel = $f.FullName.Substring($root.Length + 1).Replace('\','/')
    $m = $rel -replace '/','.'
    if ($m.EndsWith('.__init__')) { $m = $m.Substring(0, $m.Length - 9) }
    else { $m = $m.Substring(0, $m.Length - 3) }
    $mods[$m] = $rel
    $src[$m] = (Get-Content -LiteralPath $f.FullName -Raw)
}

# Tous les imports du depot, sous forme de texte brut
$tousTextes = ($src.Values -join "`n")

"=== UTILISATION DES MODULES PLATS core/*.py ==="
$plats = $mods.Keys | Where-Object { $_ -match '^core\.[a-z_0-9]+$' } | Sort-Object
foreach ($p in $plats) {
    $esc = [regex]::Escape($p)
    $n = ([regex]::Matches($tousTextes, "(?m)^\s*(from|import)\s+$esc\b")).Count
    "{0,4}  {1}" -f $n, $p
}

"`n=== UTILISATION DES SOUS-PAQUETS ==="
$packs = 'core.administration','core.api','core.betting','core.catalog','core.data','core.engagement','core.features','core.notifications','core.predictions','core.scheduling','core.utils'
foreach ($p in $packs) {
    $esc = [regex]::Escape($p)
    $n = ([regex]::Matches($tousTextes, "(?m)^\s*(from|import)\s+$esc[\.\s]")).Count
    "{0,4}  {1}" -f $n, $p
}

"`n=== MARQUEURS STUB PAR FICHIER (core) ==="
$rows = foreach ($k in ($mods.Keys | Where-Object { $_ -like 'core.*' })) {
    $s = $src[$k]
    $a = ([regex]::Matches($s, 'a_implanter')).Count
    $pas = ([regex]::Matches($s, '(?m)^\s+pass\s*$')).Count
    $todo = ([regex]::Matches($s, 'TODO')).Count
    if ($a + $pas + $todo -gt 0) {
        [PSCustomObject]@{ Stub = $a; Pass = $pas; Todo = $todo; Module = $k }
    }
}
"Fichiers core avec marqueurs : " + $rows.Count
$rows | Sort-Object Stub -Descending | Select-Object -First 20 | Format-Table -AutoSize | Out-String -Width 160

"`n=== TOTAL MARQUEURS PAR DOSSIER ==="
$parDossier = $src.Keys | Group-Object { if ($_.Contains('.')) { $_.Split('.')[0] + '.' + $_.Split('.')[1] } else { '(racine)' } } | ForEach-Object {
    $a = 0; $pas = 0; $todo = 0
    foreach ($k in $_.Group) { $s = $src[$k]; $a += ([regex]::Matches($s, 'a_implanter')).Count; $pas += ([regex]::Matches($s, '(?m)^\s+pass\s*$')).Count; $todo += ([regex]::Matches($s, 'TODO')).Count }
    [PSCustomObject]@{ Dossier = $_.Name; Fichiers = $_.Count; AImplanter = $a; Pass = $pas; TODO = $todo }
}
$parDossier | Sort-Object AImplanter -Descending | Format-Table -AutoSize | Out-String -Width 160
