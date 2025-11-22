# ⚡ Commit Direct - Sans Éditeur

## 🎯 Le Problème

Quand vous cliquez sur "Commit" dans Cursor, un fichier s'ouvre avec plein de lignes `#`. Vous voulez juste commit direct !

## ✅ Solution : Utiliser le Terminal

**Au lieu de cliquer sur "Commit" dans l'interface**, utilisez le terminal :

### 1. Ouvrez le terminal dans Cursor
- `Ctrl + ù` (ou `Ctrl + Shift + ù`)

### 2. Tapez ces commandes :
```bash
git add .
git commit -m "Initial commit"
git push
```

**C'est tout !** ✅ Pas d'éditeur, commit direct.

## 📝 Messages de Commit Exemples

```bash
git commit -m "Initial commit"
git commit -m "feat: Ajout scraper Google Maps"
git commit -m "fix: Correction bug"
git commit -m "docs: Mise à jour README"
```

## ⚙️ Configurer Cursor pour Popup au lieu d'Éditeur

Si vous voulez quand même utiliser le bouton "Commit" :

1. **Ouvrez Settings** : `Ctrl + ,`
2. **Cherchez** : `git.useEditorAsCommitInput`
3. **Désactivez** cette option (uncheck)

Maintenant, quand vous cliquez sur "Commit", une popup demandera le message au lieu d'ouvrir un fichier.

## 🚀 Workflow Recommandé

**Utilisez toujours le terminal** - c'est plus rapide :

```bash
# 1. Ajouter fichiers
git add .

# 2. Commit avec message
git commit -m "votre message"

# 3. Push
git push
```

**Fini les éditeurs qui s'ouvrent !** ✅

