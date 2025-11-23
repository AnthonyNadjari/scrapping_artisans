# 📱 Système de Prospection WhatsApp pour Artisans

Système de prospection par WhatsApp utilisant **Google Maps** pour scraper les artisans et des **liens wa.me (click-to-chat)** pour les contacter.

## ⚡ Démarrage Ultra-Rapide

### 1. Installer (une seule fois)

```bash
pip install -r requirements_whatsapp.txt
```

**Note :** ChromeDriver sera téléchargé automatiquement lors du premier scraping.

### 2. Lancer

**Windows :** Double-cliquez sur `launch_streamlit.bat`

**OU** dans le terminal :
```bash
streamlit run whatsapp_app/Accueil.py
```

### 3. C'est tout !

L'application s'ouvre dans votre navigateur.

---

## 📱 Comment ça marche

### Scraper des artisans depuis Google Maps
1. Page **🔍 Scraping** → Choisissez métier et département → **LANCER LE SCRAPING**
2. Le système scrape automatiquement plusieurs petites villes du département
3. Les téléphones, sites web, adresses sont collectés automatiquement
4. Cliquez sur **💾 SAUVEGARDER EN BDD** pour enregistrer les résultats

### Contacter des artisans
1. Page **📊 Base de Données** → Configurez votre message template
2. Cliquez sur **💬 Ouvrir WhatsApp** → WhatsApp s'ouvre avec message pré-rempli
3. Envoyez le message dans WhatsApp
4. Cliquez sur **✓ Marquer envoyé** dans le dashboard
5. Répétez pour l'artisan suivant !

### Suivre les réponses
1. Page **💬 Réponses** → Marquez les statuts (intéressé/pas intéressé/en cours/à relancer)

---

## ✅ Avantages

- ✅ **Gratuit** - Pas besoin d'API, pas de coût
- ✅ **Sans risque** - Pas d'automatisation, 0% risque de ban
- ✅ **Détection automatique des sites web** - Identifie les meilleurs prospects (sans site web)
- ✅ **Rapide** - 5-10 secondes par artisan
- ✅ **Simple** - Interface claire et intuitive
- ✅ **Efficace** - 100 artisans = 10-15 minutes

---

## ⚠️ Important

- Workflow manuel mais très rapide
- Messages personnalisés automatiquement
- Tracking complet des contacts et réponses

---

**Système basé sur les liens wa.me - Simple, rapide et sans risque ! 🚀**

