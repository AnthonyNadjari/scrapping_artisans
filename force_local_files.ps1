# Script PowerShell pour forcer les fichiers à rester en local (toujours disponible hors ligne)
# Empêche OneDrive de synchroniser automatiquement et d'ouvrir les fichiers modifiés

Write-Host "🔧 Configuration des fichiers pour rester en local..." -ForegroundColor Cyan

$projectPath = $PSScriptRoot

# Liste des extensions de fichiers à forcer en local
$extensions = @("*.py", "*.json", "*.db", "*.sqlite", "*.sqlite3", "*.html", "*.png", "*.log")

$count = 0

foreach ($ext in $extensions) {
    $files = Get-ChildItem -Path $projectPath -Filter $ext -Recurse -ErrorAction SilentlyContinue
    
    foreach ($file in $files) {
        try {
            # Forcer le fichier à rester en local (toujours disponible hors ligne)
            $file.Attributes = $file.Attributes -bor [System.IO.FileAttributes]::Offline
            
            # Alternative: Utiliser attrib.exe pour forcer le fichier en local
            $attribResult = attrib.exe "+U" $file.FullName 2>&1
            
            $count++
            Write-Host "  ✓ $($file.Name)" -ForegroundColor Green
        }
        catch {
            Write-Host "  ✗ Erreur pour $($file.Name): $_" -ForegroundColor Red
        }
    }
}

Write-Host "`n✅ $count fichiers configurés pour rester en local" -ForegroundColor Green
Write-Host "`n💡 Astuce: Si les fichiers s'ouvrent encore automatiquement," -ForegroundColor Yellow
Write-Host "   désactivez la synchronisation OneDrive pour ce dossier dans les paramètres OneDrive." -ForegroundColor Yellow

