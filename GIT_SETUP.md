# 🔧 Configuration Git pour Éviter les Commits Vides

## Problème

Git annule les commits si le message est vide. Voici comment éviter ce problème.

## ✅ Solution 1 : Configurer un Template de Message

### Windows (PowerShell)
```powershell
git config --global commit.template .gitmessage
```

### Linux/Mac
```bash
git config --global commit.template .gitmessage
```

Maintenant, quand vous faites `git commit` sans `-m`, Git ouvrira un éditeur avec un template pré-rempli.

## ✅ Solution 2 : Toujours Utiliser `-m` avec un Message

**Mauvaise pratique :**
```bash
git commit  # ❌ Peut créer un commit vide
```

**Bonne pratique :**
```bash
git commit -m "feat: Ajout du scraper Google Maps"  # ✅
```

## ✅ Solution 3 : Utiliser les Scripts Helper

### Windows
```powershell
.\git-commit.bat "feat: Ajout nouvelle fonctionnalité"
```

### Linux/Mac
```bash
chmod +x git-commit.sh
./git-commit.sh "feat: Ajout nouvelle fonctionnalité"
```

## 📝 Conventions de Messages de Commit

Utilisez des messages clairs et descriptifs :

```
feat: Ajout du scraper Google Maps
fix: Correction de l'anti-doublons dans la BDD
docs: Mise à jour du README avec instructions
style: Formatage du code selon PEP8
refactor: Refactoring du module emails
test: Ajout de tests pour le scraper
chore: Mise à jour des dépendances
```

## 🚀 Commandes Git Utiles

### Commit rapide avec message
```bash
git add .
git commit -m "votre message ici"
git push
```

### Commit avec message multi-lignes
```bash
git commit -m "Titre" -m "Description détaillée"
```

### Voir l'historique des commits
```bash
git log --oneline
```

### Annuler le dernier commit (garder les changements)
```bash
git reset --soft HEAD~1
```

### Annuler le dernier commit (supprimer les changements)
```bash
git reset --hard HEAD~1
```

## ⚙️ Configuration Recommandée

### Configurer votre nom et email
```bash
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@example.com"
```

### Activer l'éditeur par défaut (VS Code)
```bash
git config --global core.editor "code --wait"
```

### Voir toutes vos configurations
```bash
git config --list
```

## 🔍 Dépannage

### Si vous avez fait un commit vide par erreur
```bash
# Annuler le dernier commit (garder les fichiers)
git reset --soft HEAD~1

# Puis refaire le commit avec un message
git commit -m "votre message"
```

### Si vous avez oublié d'ajouter des fichiers
```bash
# Ajouter les fichiers oubliés
git add fichier_oublie.py

# Modifier le dernier commit
git commit --amend --no-edit
```

---

**Astuce** : Toujours utiliser `git commit -m "message"` pour éviter les commits vides !

