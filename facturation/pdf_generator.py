"""
Générateur de PDF pour les factures
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from pathlib import Path
from datetime import datetime
from facturation.utils import get_invoices_dir, get_client_slug
import pandas as pd


def generate_invoice_pdf(facture_data, config):
    """
    Génère un PDF de facture
    
    Args:
        facture_data: Dictionnaire avec les données de la facture
        config: Dictionnaire de configuration de l'entreprise
    
    Returns:
        chemin_pdf: Chemin relatif du PDF généré
    """
    # Préparer le chemin de destination
    invoices_dir = get_invoices_dir()
    annee = datetime.now().year
    client_slug = get_client_slug(facture_data['client_nom'])
    
    # Créer la structure de dossiers
    facture_dir = invoices_dir / str(annee) / client_slug
    facture_dir.mkdir(parents=True, exist_ok=True)
    
    # Nom du fichier
    numero = facture_data['numero']
    description_slug = facture_data['description'][:30].replace(' ', '_').replace('/', '-')
    filename = f"{numero}_{description_slug}.pdf"
    pdf_path = facture_dir / filename
    
    # Créer le PDF
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    story = []
    styles = getSampleStyleSheet()
    
    # ============================================
    # BLOC 1 : INFORMATIONS ENTREPRISE (EN HAUT)
    # ============================================
    entreprise_nom = config.get('entreprise_nom', 'TOM&CO')
    entreprise_adresse = config.get('entreprise_adresse', '54 RUE DU MONT VALERIEN\n92210 SAINT-CLOUD')
    siren = config.get('entreprise_siren', '945171288')
    siret = config.get('entreprise_siret', '94517128800018')
    tva = config.get('entreprise_tva', 'FR79945171288')

    # Créer le bloc entreprise avec nom, adresse et informations légales
    entreprise_info = f"""
    <b><font size="14">{entreprise_nom}</font></b><br/>
    <b>{entreprise_adresse.replace(chr(10), '<br/>')}</b><br/>
    """
    
    # Ajouter SIREN, SIRET, TVA
    entreprise_info += f"SIREN: {siren}<br/>"
    entreprise_info += f"SIRET: {siret}<br/>"
    entreprise_info += f"N° TVA: {tva}<br/>"
    
    story.append(Paragraph(entreprise_info, styles['Normal']))
    story.append(Spacer(1, 1.5*cm))
    
    # ============================================
    # BLOC 2 : INFORMATIONS FACTURE + PRODUITS
    # ============================================
    
    # Titre FACTURE
    facture_title = ParagraphStyle(
        'FactureTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=20,
        alignment=TA_LEFT
    )
    story.append(Paragraph("FACTURE", facture_title))
    story.append(Spacer(1, 0.5*cm))
    
    # Informations de la facture (numéro et date)
    date_emission = pd.to_datetime(facture_data['date_emission']).strftime('%d/%m/%Y') if pd.notna(facture_data['date_emission']) else datetime.now().strftime('%d/%m/%Y')
    
    facture_info_data = [
        ['Numéro de facture:', facture_data['numero']],
        ['Date d\'émission:', date_emission],
    ]
    
    facture_info_table = Table(facture_info_data, colWidths=[5*cm, 8*cm])
    facture_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(facture_info_table)
    story.append(Spacer(1, 1*cm))
    
    # Tableau des prestations avec quantité, prix unitaire et total
    quantite = facture_data.get('quantite', 1.0)
    prix_unitaire = facture_data.get('prix_unitaire', facture_data.get('montant', 0.0))
    montant_total = facture_data.get('montant', quantite * prix_unitaire)
    
    prestations_data = [
        ['Description', 'Quantité', 'Prix unitaire HT', 'Montant HT'],
        [
            facture_data['description'],
            f"{quantite:.0f}" if quantite == int(quantite) else f"{quantite:.2f}",
            f"{prix_unitaire:.2f} €",
            f"{montant_total:.2f} €"
        ]
    ]
    
    prestations_table = Table(prestations_data, colWidths=[7*cm, 2.5*cm, 3*cm, 3*cm])
    prestations_table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Description à gauche
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Quantité centrée
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),  # Prix et montant à droite
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        # Corps
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        # Lignes
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    story.append(prestations_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Total (aligné à droite)
    total_data = [
        ['Total HT:', f"{montant_total:.2f} € HT"],
    ]
    
    # Mention TVA
    tva_mention = config.get('tva_mention', 'TVA non applicable, art. 293 B du CGI')
    if tva_mention:
        total_data.append(['', '']),
        total_data.append(['', Paragraph(f"<i>{tva_mention}</i>", styles['Normal'])])
    
    total_table = Table(total_data, colWidths=[12*cm, 3*cm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 12),
        ('FONTSIZE', (1, 0), (1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 1.5*cm))
    
    # ============================================
    # BLOC 3 : DESTINATAIRE + MODE DE PAIEMENT
    # ============================================
    
    # Informations client/destinataire
    client_title_style = ParagraphStyle(
        'ClientTitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10,
    )
    story.append(Paragraph("Facturé à :", client_title_style))
    
    client_info = f"""
    <b>{facture_data['client_nom']}</b><br/>
    {facture_data.get('client_adresse', '')}<br/>
    """
    # Afficher SIRET seulement s'il est renseigné
    client_siret = facture_data.get('client_siret', '')
    # Vérifier que ce n'est pas None, NaN, vide, ou la chaîne "None"
    if client_siret is not None:
        client_siret_str = str(client_siret).strip()
        if client_siret_str and client_siret_str.lower() not in ['none', 'nan', '', 'null']:
            client_info += f"SIRET: {client_siret_str}<br/>"
    
    # Afficher Email seulement s'il est renseigné
    client_email = facture_data.get('client_email', '')
    # Vérifier que ce n'est pas None, NaN, vide, ou la chaîne "None"
    if client_email is not None:
        client_email_str = str(client_email).strip()
        if client_email_str and client_email_str.lower() not in ['none', 'nan', '', 'null']:
            client_info += f"Email: {client_email_str}<br/>"
    
    story.append(Paragraph(client_info, styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Conditions de paiement
    conditions = config.get('conditions_paiement', 'Paiement à réception')
    if conditions:
        story.append(Paragraph(f"<b>Conditions de paiement:</b> {conditions}", styles['Normal']))
    
    # Générer le PDF
    doc.build(story)
    
    # Retourner le chemin relatif
    return Path("invoices") / str(annee) / client_slug / filename
