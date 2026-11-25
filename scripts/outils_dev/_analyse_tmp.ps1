$root = (Get-Location).Path
$files = Get-ChildItem -Recurse -File -Filter *.py | Where-Object { $_.FullName -notmatch '\\\.venv\\|__pycache__' }
"FICHIERS PY: " + $files.Count
$total = 0
$rows = foreach ($f in $files) {
    $n = (Get-Content -LiteralPath $f.FullName | Measure-Object -Line).Lines
    $total += $n
    [PSCustomObject]@{
        Lignes = $n
        Chemier = $f.FullName.Substring($root.Length + 1)
    }
}
"TOTAL LIGNES PY: " + $total
"--- TOP 30 FICHIERS ---"
$rows | Sort-Object Lignes -Descending | Select-Object -First 30 | Format-Table -AutoSize | Out-String -Width 200
"--- PAR DOSSIER ---"
$rows | Group-Object { ($_.Chemier -split '\\')[0] } | ForEach-Object {
    [PSCustomObject]@{ Dossier = $_.Name; Fichiers = $_.Count; Lignes = ($_.Group | Measure-Object Lignes -Sum).Sum }
} | Sort-Object Lignes -Descending | Format-Table -AutoSize | Out-String -Width 200
