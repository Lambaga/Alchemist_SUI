# Python Cache Cleaner fuer Alchemist Projekt
# Fuehre dieses Skript aus, um alle Python Cache-Dateien zu bereinigen

param(
    [switch]$Verbose = $false
)

Write-Host "Python Cache Bereinigung fuer Alchemist" -ForegroundColor Green
Write-Host "=" * 50

$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Zähle Dateien vor der Bereinigung
$pycFiles = Get-ChildItem -Path $projectPath -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
$pyoFiles = Get-ChildItem -Path $projectPath -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue  
$pycacheDirs = Get-ChildItem -Path $projectPath -Recurse -Directory -Name "__pycache__" -ErrorAction SilentlyContinue

Write-Host "Gefunden:"
Write-Host "   - .pyc Dateien: $($pycFiles.Count)"
Write-Host "   - .pyo Dateien: $($pyoFiles.Count)"
Write-Host "   - __pycache__ Ordner: $($pycacheDirs.Count)"

if ($pycFiles.Count -eq 0 -and $pyoFiles.Count -eq 0 -and $pycacheDirs.Count -eq 0) {
    Write-Host "Keine Cache-Dateien gefunden - Projekt ist bereits sauber!" -ForegroundColor Green
    exit 0
}

# Bereinigung durchfuehren
Write-Host "`nBereinige Cache-Dateien..."

# .pyc Dateien loeschen
if ($pycFiles.Count -gt 0) {
    $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "   * $($pycFiles.Count) .pyc Dateien geloescht"
}

# .pyo Dateien loeschen  
if ($pyoFiles.Count -gt 0) {
    $pyoFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "   * $($pyoFiles.Count) .pyo Dateien geloescht"
}

# __pycache__ Ordner loeschen
if ($pycacheDirs.Count -gt 0) {
    Get-ChildItem -Path $projectPath -Recurse -Directory -Name "__pycache__" -ErrorAction SilentlyContinue | 
        ForEach-Object { 
            $fullPath = Join-Path $projectPath $_
            Remove-Item -Path $fullPath -Recurse -Force -ErrorAction SilentlyContinue
        }
    Write-Host "   * $($pycacheDirs.Count) __pycache__ Ordner geloescht"
}

Write-Host "`nCache-Bereinigung abgeschlossen!" -ForegroundColor Green

# Optionale Verifikation
Write-Host "`nVerifikation..."
$remainingPyc = (Get-ChildItem -Path $projectPath -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue).Count
$remainingPyo = (Get-ChildItem -Path $projectPath -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue).Count
$remainingCache = (Get-ChildItem -Path $projectPath -Recurse -Directory -Name "__pycache__" -ErrorAction SilentlyContinue).Count

if ($remainingPyc + $remainingPyo + $remainingCache -eq 0) {
    Write-Host "Alle Cache-Dateien erfolgreich entfernt!" -ForegroundColor Green
} else {
    Write-Host "Noch vorhanden: $remainingPyc .pyc, $remainingPyo .pyo, $remainingCache __pycache__" -ForegroundColor Yellow
}

Write-Host "`nTipp: Fuehre dieses Skript regelmaessig aus, besonders nach groesseren Code-Aenderungen!"
