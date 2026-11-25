$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

$catalogSource = [System.IO.File]::ReadAllText((Join-Path $root "core/catalog/catalogue_fonctionnalites.py"), [System.Text.Encoding]::UTF8)
$features = [ordered]@{}

foreach ($match in [regex]::Matches($catalogSource, '\("(\d+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)')) {
    $id = [int]$match.Groups[1].Value
    $features[$id.ToString()] = [PSCustomObject]@{
        id = $id
        name = $match.Groups[2].Value
        group = $match.Groups[3].Value
        status = $match.Groups[4].Value
        source = "core/catalog/catalogue_fonctionnalites.py"
    }
}

$docFiles = @(
    "docs/03_Fonctionnalites_138_a_274.txt",
    "docs/04_Fonctionnalites_275_a_411.txt",
    "docs/05_Fonctionnalites_412_a_547.txt",
    "docs/06_Fonctionnalites_548_a_624.txt",
    "docs/07_Fonctionnalites_625_a_700.txt"
)

foreach ($docFile in $docFiles) {
    $text = [System.IO.File]::ReadAllText((Join-Path $root $docFile), [System.Text.Encoding]::UTF8)
    foreach ($line in $text -split "`r?`n") {
        if ($line -match '^\s*(\d{3})\s*(?:[.]|—|-)\s*(.+)$') {
            $id = [int]$Matches[1]
            $name = ($Matches[2] -replace ':.*$', '').Trim()
            if ($name.Length -gt 180) {
                $name = $name.Substring(0, 180).Trim()
            }
            if (-not $features.Contains($id.ToString())) {
                $features[$id.ToString()] = [PSCustomObject]@{
                    id = $id
                    name = $name
                    group = "Extension"
                    status = "a_implanter"
                    source = $docFile
                }
            }
        }
    }
}

$doc625 = "docs/07_Fonctionnalites_625_a_700.txt"
$text625 = [System.IO.File]::ReadAllText((Join-Path $root $doc625), [System.Text.Encoding]::UTF8)
foreach ($line in $text625 -split "`r?`n") {
    if ($line -match '^\s*(6[2-9][0-9]|700)\s*(?:[.]|—|-)\s*(.+)$') {
        $id = [int]$Matches[1]
        $name = ($Matches[2] -replace ':.*$', '').Trim()
        if (-not $features.Contains($id.ToString())) {
            $features[$id.ToString()] = [PSCustomObject]@{
                id = $id
                name = $name
                group = "Extension"
                status = "a_implanter"
                source = $doc625
            }
        }
    }
}

$completeIds = @("138","139","149","150","163","164","165","168","179","182","186","187","188","189","190","193","413","414","416","417","418","422","423","424","432","433","434","435","436","437","438","439","444","445","446","447","448","449","450","455","456","464","465","466","467","625","627","628","631","632","633","634","635","637","638","639","640","641","642","643","645","646","647","648","649")
foreach ($id in $completeIds) {
    if ($features.Contains($id)) {
        $features[$id].status = "complete"
    }
}

$missing = @()
for ($id = 1; $id -le 700; $id++) {
    if (-not $features.Contains($id.ToString())) {
        $missing += $id
    }
}
if ($missing.Count -gt 0) {
    throw "Fonctionnalités manquantes dans l'inventaire : $($missing -join ', ')"
}

$items = for ($id = 1; $id -le 700; $id++) { $features[$id.ToString()] }

$markdown = New-Object System.Text.StringBuilder
[void]$markdown.AppendLine("# Inventaire officiel des 700 fonctionnalités")
[void]$markdown.AppendLine("")
[void]$markdown.AppendLine("Source unique avant implementation : catalogue central + fichiers documentaires 138-700.")
[void]$markdown.AppendLine("")
[void]$markdown.AppendLine("| ID | Fonctionnalité | Groupe | Statut | Source |")
[void]$markdown.AppendLine("|---:|---|---|---|---|")
foreach ($item in $items) {
    [void]$markdown.AppendLine("| $($item.id) | $($item.name -replace '\|','\/') | $($item.group -replace '\|','\/') | $($item.status) | $($item.source) |")
}

[System.IO.File]::WriteAllText((Join-Path $root "docs/700_FONCTIONNALITES.md"), $markdown.ToString(), [System.Text.UTF8Encoding]::new($false))
$json = $items | ConvertTo-Json -Depth 3
[System.IO.File]::WriteAllText((Join-Path $root "docs/700_FONCTIONNALITES.json"), $json, [System.Text.UTF8Encoding]::new($false))

Write-Host "Inventaire 1-700 généré : $($items.Count) fonctionnalités"
