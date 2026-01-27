"""
Streamlit page for generating artisan websites from Google Form responses.

This page allows you to:
1. Paste email content from Google Form notification
2. Select a folder with client photos
3. Preview the generated configuration
4. Deploy to GitHub and Vercel with one click
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from website_generator.parser import parse_email_content
from website_generator.config_generator import generate_config
from website_generator.deployer import (
    deploy_site,
    check_prerequisites,
    prepare_site_directory,
    generate_repo_name,
    slugify,
    open_terminal_for_auth,
    install_cli_tool
)
from website_generator.trade_defaults import TRADE_DISPLAY_NAMES

st.set_page_config(
    page_title="Génération de Site Web",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 Génération de Site Web")
st.markdown("Créez un site web personnalisé à partir des réponses du formulaire Google.")

# Initialize session state
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None
if "config_content" not in st.session_state:
    st.session_state.config_content = None
if "deployment_result" not in st.session_state:
    st.session_state.deployment_result = None


# --- Section 1: Email Input ---
st.header("1️⃣ Contenu de l'email")

email_text = st.text_area(
    "Collez le contenu de l'email de notification Google Form",
    height=300,
    placeholder="""Nouvelle réponse au formulaire: 🎨 Personnalisation de Votre Site Web

Nom de l'entreprise: Martin Plomberie
Type de métier / activité: Plombier
Slogan ou phrase d'accroche: La qualité au service de votre confort
...
""",
    key="email_input"
)

col1, col2 = st.columns([1, 3])
with col1:
    parse_button = st.button("📋 Analyser l'email")


# --- Section 2: Photos Directory ---
st.header("2️⃣ Photos du client (optionnel)")

photos_dir = st.text_input(
    "Chemin vers le dossier contenant les photos du client",
    placeholder=r"C:\clients\martin-plomberie\photos",
    key="photos_dir"
)

if photos_dir and os.path.exists(photos_dir):
    photos = [f for f in os.listdir(photos_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    if photos:
        st.success(f"✅ {len(photos)} photos trouvées")
        # Display thumbnails in columns
        cols = st.columns(min(len(photos), 4))
        for i, photo in enumerate(photos[:8]):
            with cols[i % 4]:
                photo_path = os.path.join(photos_dir, photo)
                st.image(photo_path, caption=photo, width=150)
        if len(photos) > 8:
            st.info(f"... et {len(photos) - 8} autres photos")
    else:
        st.warning("⚠️ Aucune image trouvée dans ce dossier")
elif photos_dir:
    st.error("❌ Le dossier spécifié n'existe pas")
else:
    st.info("ℹ️ Si aucune photo n'est fournie, les images par défaut seront utilisées")


# --- Parse Email ---
if parse_button and email_text:
    with st.spinner("Analyse de l'email en cours..."):
        try:
            st.session_state.parsed_data = parse_email_content(email_text)
            st.session_state.config_content = generate_config(st.session_state.parsed_data)
            st.success("✅ Email analysé avec succès!")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'analyse: {str(e)}")
            st.session_state.parsed_data = None


# --- Section 3: Configuration Preview ---
if st.session_state.parsed_data:
    st.header("3️⃣ Aperçu de la configuration")

    data = st.session_state.parsed_data

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🏢 Entreprise")
        st.write(f"**Nom:** {data.get('business_name', 'N/A')}")
        st.write(f"**Métier:** {TRADE_DISPLAY_NAMES.get(data.get('trade_type', ''), data.get('trade_type', 'N/A'))}")
        st.write(f"**Slogan:** {data.get('slogan', 'N/A')}")

    with col2:
        st.subheader("📍 Localisation")
        st.write(f"**Ville:** {data.get('city', 'N/A')}")
        st.write(f"**Code postal:** {data.get('postal_code', 'N/A')}")
        st.write(f"**Adresse:** {data.get('street', 'N/A')}")

    with col3:
        st.subheader("📞 Contact")
        st.write(f"**Téléphone:** {data.get('phone_display', data.get('phone', 'N/A'))}")
        st.write(f"**Horaires:** {data.get('hours', 'N/A')}")

    # Colors preview
    st.subheader("🎨 Couleurs")
    col1, col2 = st.columns(2)

    with col1:
        primary = data.get('primary_color', {})
        if primary:
            color_css = f"hsl({primary.get('h', 220)}, {primary.get('s', 60)}%, {primary.get('l', 20)}%)"
            st.markdown(
                f'<div style="background-color: {color_css}; padding: 20px; border-radius: 8px; color: white; text-align: center;">Couleur Principale</div>',
                unsafe_allow_html=True
            )

    with col2:
        accent = data.get('accent_color', {})
        if accent:
            color_css = f"hsl({accent.get('h', 25)}, {accent.get('s', 85)}%, {accent.get('l', 50)}%)"
            st.markdown(
                f'<div style="background-color: {color_css}; padding: 20px; border-radius: 8px; color: white; text-align: center;">Couleur Accent</div>',
                unsafe_allow_html=True
            )

    # Features
    st.subheader("⚙️ Fonctionnalités activées")
    features = data.get('features', [])
    feature_labels = {
        "booking": "📅 Réservation en ligne",
        "contactForm": "📧 Formulaire de contact",
        "gallery": "🖼️ Galerie photos",
        "quoteRequest": "📝 Demande de devis",
        "emergencyBanner": "🚨 Urgences 24/7",
        "googleReviews": "⭐ Avis Google",
    }

    feature_cols = st.columns(3)
    for i, (key, label) in enumerate(feature_labels.items()):
        with feature_cols[i % 3]:
            if key in features:
                st.markdown(f"✅ {label}")
            else:
                st.markdown(f"❌ {label}")

    # Repository name preview
    repo_name = generate_repo_name(data)
    st.subheader("📦 Nom du repository")
    st.code(repo_name)

    # Show/hide config code
    with st.expander("📄 Voir le code de configuration généré"):
        st.code(st.session_state.config_content, language="typescript")


# --- Section 4: Deployment ---
if st.session_state.parsed_data and st.session_state.config_content:
    st.header("4️⃣ Déploiement")

    # Check prerequisites
    prereqs = check_prerequisites()

    with st.expander("🔧 Vérification des prérequis", expanded=True):
        col_prereq1, col_prereq2 = st.columns(2)

        with col_prereq1:
            st.markdown("**Outils installés:**")
            for tool in ["git", "node", "npm", "gh", "vercel"]:
                icon = "✅" if prereqs.get(tool) else "❌"
                st.write(f"{icon} {tool}")

        with col_prereq2:
            st.markdown("**Authentification:**")
            icon_gh = "✅" if prereqs.get("gh_auth") else "❌"
            icon_vercel = "✅" if prereqs.get("vercel_auth") else "❌"
            st.write(f"{icon_gh} GitHub authentifié")
            st.write(f"{icon_vercel} Vercel authentifié")

        # Installation buttons if tools are missing
        if not prereqs.get("gh"):
            st.markdown("---")
            st.warning("⚠️ GitHub CLI non installé")
            if st.button("📥 Installer GitHub CLI"):
                install_cli_tool("gh")
                st.info("Terminal ouvert pour l'installation. Fermez et relancez la page une fois terminé.")

        if not prereqs.get("vercel"):
            st.warning("⚠️ Vercel CLI non installé")
            if st.button("📥 Installer Vercel CLI"):
                install_cli_tool("vercel")
                st.info("Terminal ouvert pour l'installation. Fermez et relancez la page une fois terminé.")

        # Authentication buttons
        st.markdown("---")
        st.markdown("**Actions d'authentification:**")
        auth_col1, auth_col2, auth_col3 = st.columns(3)

        with auth_col1:
            if st.button("🔐 Connexion GitHub"):
                if open_terminal_for_auth("gh"):
                    st.success("Terminal ouvert pour GitHub. Suivez les instructions.")
                else:
                    st.error("Impossible d'ouvrir le terminal")

        with auth_col2:
            if st.button("🔐 Connexion Vercel"):
                if open_terminal_for_auth("vercel"):
                    st.success("Terminal ouvert pour Vercel. Suivez les instructions.")
                else:
                    st.error("Impossible d'ouvrir le terminal")

        with auth_col3:
            if st.button("🔄 Revérifier"):
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()

    # Warning if not authenticated
    ready_to_deploy = True
    if not prereqs.get("gh_auth") and not st.session_state.get("skip_github_warning"):
        st.warning("⚠️ GitHub non authentifié - La création du repo sera ignorée sauf si vous vous connectez")
        ready_to_deploy = prereqs.get("vercel_auth")
    if not prereqs.get("vercel_auth") and not st.session_state.get("skip_vercel_warning"):
        st.warning("⚠️ Vercel non authentifié - Le déploiement sera ignoré sauf si vous vous connectez")

    # Deployment options
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        # Try with disabled parameter, fallback to without
        try:
            skip_github = st.checkbox(
                "Passer la création GitHub",
                value=not prereqs.get("gh_auth"),
                disabled=not prereqs.get("gh_auth")
            )
        except TypeError:
            skip_github = st.checkbox(
                "Passer la création GitHub",
                value=not prereqs.get("gh_auth")
            )
    with col2:
        try:
            skip_vercel = st.checkbox(
                "Passer le déploiement Vercel",
                value=not prereqs.get("vercel_auth"),
                disabled=not prereqs.get("vercel_auth")
            )
        except TypeError:
            skip_vercel = st.checkbox(
                "Passer le déploiement Vercel",
                value=not prereqs.get("vercel_auth")
            )

    # Deploy button
    deploy_disabled = not prereqs.get("git") or not prereqs.get("node") or not prereqs.get("npm")
    if deploy_disabled:
        st.error("❌ Impossible de déployer: git, node et npm sont requis")

    # Use try/except for disabled parameter (not available in older Streamlit)
    deploy_clicked = False
    try:
        deploy_clicked = st.button("🚀 Créer et déployer le site", disabled=deploy_disabled)
    except TypeError:
        if not deploy_disabled:
            deploy_clicked = st.button("🚀 Créer et déployer le site")

    if deploy_clicked:
        with st.spinner("Déploiement en cours... Cela peut prendre quelques minutes."):
            try:
                result = deploy_site(
                    st.session_state.parsed_data,
                    st.session_state.config_content,
                    photos_dir if photos_dir and os.path.exists(photos_dir) else None,
                    skip_github=skip_github,
                    skip_vercel=skip_vercel
                )
                st.session_state.deployment_result = result

                if result["success"]:
                    st.success("🎉 Déploiement réussi!")
                else:
                    st.warning("⚠️ Déploiement terminé avec des erreurs")

            except Exception as e:
                st.error(f"❌ Erreur lors du déploiement: {str(e)}")
                st.session_state.deployment_result = {"success": False, "errors": [str(e)]}


# --- Section 5: Results ---
if st.session_state.deployment_result:
    st.header("5️⃣ Résultats")

    result = st.session_state.deployment_result

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📁 Fichiers locaux")
        if result.get("site_path"):
            st.code(result["site_path"])
            if st.button("📂 Ouvrir le dossier"):
                os.startfile(result["site_path"])

    with col2:
        st.subheader("🔗 Liens")
        if result.get("github_url"):
            st.markdown(f"**GitHub:** [{result['github_url']}]({result['github_url']})")
        if result.get("vercel_url"):
            st.markdown(f"**Site en ligne:** [{result['vercel_url']}]({result['vercel_url']})")
            st.balloons()

    if result.get("errors"):
        st.subheader("⚠️ Erreurs rencontrées")
        for error in result["errors"]:
            st.error(error)

    # Copy URLs
    if result.get("vercel_url"):
        st.subheader("📋 Copier pour le client")
        client_message = f"""Bonjour,

Votre site web est maintenant en ligne ! 🎉

📱 Accédez à votre site : {result['vercel_url']}

Le site est entièrement fonctionnel et prêt à être partagé avec vos clients.

Si vous souhaitez un nom de domaine personnalisé (ex: www.votre-entreprise.fr), n'hésitez pas à nous contacter.

Cordialement,
L'équipe"""
        st.text_area("Message à envoyer au client", client_message, height=200)


# --- Sidebar ---
with st.sidebar:
    st.header("ℹ️ Guide")

    st.markdown("""
    ### Étapes

    1. **Recevez l'email** de notification Google Form
    2. **Copiez le contenu** de l'email
    3. **Collez-le** dans la zone de texte
    4. **Ajoutez les photos** du client (optionnel)
    5. **Vérifiez** la configuration générée
    6. **Connectez-vous** à GitHub et Vercel si nécessaire
    7. **Déployez** en un clic!

    ### Prérequis

    Les outils requis sont vérifiés automatiquement.
    Utilisez les boutons dans la section Déploiement
    pour installer ou vous authentifier.

    - [GitHub CLI](https://cli.github.com/)
    - [Vercel CLI](https://vercel.com/docs/cli)
    - Node.js & npm
    """)

    st.markdown("---")

    if st.button("🔄 Réinitialiser"):
        st.session_state.parsed_data = None
        st.session_state.config_content = None
        st.session_state.deployment_result = None
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()
