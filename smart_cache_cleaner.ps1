# Intelligenter PowerShell Cache Cleaner
param(
    [ValidateSet("orphaned", "outdated", "all", "smart")]
    [string]$Mode = "smart",
    [switch]$Verbose = $false,
    [switch]$DryRun = $false
)

Write-Host "Intelligenter Python Cache Cleaner" -ForegroundColor Green
Write-Host "Modus: $Mode" -ForegroundColor Cyan
Write-Host "=" * 50

$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path

function Find-OrphanedCacheFiles {
    param([string]$RootPath)
    
    $orphanedFiles = @()
    $emptyDirs = @()
    
    Write-Host "Analysiere verwaiste Cache-Dateien..." -ForegroundColor Yellow
    
    # Finde alle __pycache__ Ordner
    $pycacheDirs = Get-ChildItem -Path $RootPath -Recurse -Directory -Name "__pycache__" -ErrorAction SilentlyContinue
    
    foreach ($pycacheDir in $pycacheDirs) {
        $fullPycachePath = Join-Path $RootPath $pycacheDir
        $parentDir = Split-Path $fullPycachePath -Parent
        
        $hasValidCache = $false
        
        # Prüfe alle .pyc Dateien in diesem __pycache__ Ordner
        $cacheFiles = Get-ChildItem -Path $fullPycachePath -Filter "*.pyc" -ErrorAction SilentlyContinue
        
        foreach ($cacheFile in $cacheFiles) {
            # Extrahiere den Basis-Dateinamen (vor dem ersten Punkt)
            $baseName = $cacheFile.BaseName.Split('.')[0]
            $correspondingPyFile = Join-Path $parentDir "$baseName.py"
            
            if (-not (Test-Path $correspondingPyFile)) {
                # .py Datei existiert nicht mehr - Cache ist verwaist
                $orphanedFiles += $cacheFile.FullName
                if ($Verbose) {
                    Write-Host "   Verwaist: $($cacheFile.FullName) (keine $correspondingPyFile)" -ForegroundColor Red
                }
            } else {
                $hasValidCache = $true
            }
        }
        
        # Wenn kein gültiger Cache vorhanden ist, markiere den Ordner zum Löschen
        if (-not $hasValidCache) {
            $emptyDirs += $fullPycachePath
        }
    }
    
    return $orphanedFiles, $emptyDirs
}

function Find-OutdatedCacheFiles {
    param([string]$RootPath)
    
    $outdatedFiles = @()
    
    Write-Host "Suche veraltete Cache-Dateien..." -ForegroundColor Yellow
    
    # Finde alle __pycache__ Ordner
    $pycacheDirs = Get-ChildItem -Path $RootPath -Recurse -Directory -Name "__pycache__" -ErrorAction SilentlyContinue
    
    foreach ($pycacheDir in $pycacheDirs) {
        $fullPycachePath = Join-Path $RootPath $pycacheDir
        $parentDir = Split-Path $fullPycachePath -Parent
        
        # Prüfe alle .pyc Dateien in diesem __pycache__ Ordner
        $cacheFiles = Get-ChildItem -Path $fullPycachePath -Filter "*.pyc" -ErrorAction SilentlyContinue
        
        foreach ($cacheFile in $cacheFiles) {
            $baseName = $cacheFile.BaseName.Split('.')[0]
            $correspondingPyFile = Join-Path $parentDir "$baseName.py"
            
            if (Test-Path $correspondingPyFile) {
                $pyFileTime = (Get-Item $correspondingPyFile).LastWriteTime
                $cacheFileTime = $cacheFile.LastWriteTime
                
                if ($cacheFileTime -lt $pyFileTime) {
                    # Cache ist älter als die .py Datei
                    $outdatedFiles += $cacheFile.FullName
                    if ($Verbose) {
                        Write-Host "   Veraltet: $($cacheFile.FullName)" -ForegroundColor Orange
                    }
                }
            }
        }
    }
    
    return $outdatedFiles
}

function Remove-CacheFiles {
    param(
        [string[]]$FilesToRemove,
        [string[]]$DirsToRemove,
        [string]$Description
    )
    
    $removed = 0
    
    if ($FilesToRemove.Count -gt 0) {
        Write-Host "$Description Dateien: $($FilesToRemove.Count)" -ForegroundColor Cyan
        
        foreach ($file in $FilesToRemove) {
            if ($DryRun) {
                Write-Host "   [DRY RUN] Würde löschen: $file" -ForegroundColor Gray
            } else {
                try {
                    Remove-Item $file -Force -ErrorAction Stop
                    $removed++
                    if ($Verbose) {
                        Write-Host "   Gelöscht: $file" -ForegroundColor Green
                    }
                } catch {
                    Write-Host "   Fehler bei $file`: $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        }
    }
    
    if ($DirsToRemove.Count -gt 0) {
        Write-Host "$Description Ordner: $($DirsToRemove.Count)" -ForegroundColor Cyan
        
        foreach ($dir in $DirsToRemove) {
            if ($DryRun) {
                Write-Host "   [DRY RUN] Würde löschen: $dir" -ForegroundColor Gray
            } else {
                try {
                    Remove-Item $dir -Recurse -Force -ErrorAction Stop
                    $removed++
                    if ($Verbose) {
                        Write-Host "   Gelöscht: $dir" -ForegroundColor Green
                    }
                } catch {
                    Write-Host "   Fehler bei $dir`: $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        }
    }
    
    return $removed
}

# Hauptlogik
$totalRemoved = 0

switch ($Mode) {
    "orphaned" {
        $orphanedFiles, $emptyDirs = Find-OrphanedCacheFiles $projectPath
        $totalRemoved += Remove-CacheFiles $orphanedFiles $emptyDirs "Verwaiste"
    }
    "outdated" {
        $outdatedFiles = Find-OutdatedCacheFiles $projectPath
        $totalRemoved += Remove-CacheFiles $outdatedFiles @() "Veraltete"
    }
    "smart" {
        # Kombiniert orphaned + outdated
        $orphanedFiles, $emptyDirs = Find-OrphanedCacheFiles $projectPath
        $outdatedFiles = Find-OutdatedCacheFiles $projectPath
        $totalRemoved += Remove-CacheFiles $orphanedFiles $emptyDirs "Verwaiste"
        $totalRemoved += Remove-CacheFiles $outdatedFiles @() "Veraltete"
    }
    "all" {
        # Traditionelle Vollbereinigung
        $allPycFiles = Get-ChildItem -Path $projectPath -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
        $allPyoFiles = Get-ChildItem -Path $projectPath -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue
        $allPycacheDirs = Get-ChildItem -Path $projectPath -Recurse -Directory -Name "__pycache__" -ErrorAction SilentlyContinue
        
        $allFiles = @()
        $allFiles += $allPycFiles.FullName
        $allFiles += $allPyoFiles.FullName
        
        $allDirs = @()
        foreach ($dir in $allPycacheDirs) {
            $allDirs += Join-Path $projectPath $dir
        }
        
        $totalRemoved += Remove-CacheFiles $allFiles $allDirs "Alle"
    }
}

Write-Host "`nBereinigung abgeschlossen!" -ForegroundColor Green
if ($DryRun) {
    Write-Host "DRY RUN: Es wurden keine Dateien tatsächlich gelöscht." -ForegroundColor Yellow
} else {
    Write-Host "Entfernte Elemente: $totalRemoved" -ForegroundColor Green
}

Write-Host "`nNutzung:"
Write-Host "  .\smart_cache_cleaner.ps1 -Mode smart     # Verwaiste + veraltete (empfohlen)"
Write-Host "  .\smart_cache_cleaner.ps1 -Mode orphaned  # Nur verwaiste"
Write-Host "  .\smart_cache_cleaner.ps1 -Mode outdated  # Nur veraltete"
Write-Host "  .\smart_cache_cleaner.ps1 -Mode all       # Alles löschen"
Write-Host "  .\smart_cache_cleaner.ps1 -DryRun         # Simulation ohne löschen"
