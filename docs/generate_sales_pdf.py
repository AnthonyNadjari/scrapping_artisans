"""
Script to generate the sales PDF from markdown.
Requires: pip install markdown weasyprint
Or simpler: pip install fpdf2
"""

from fpdf import FPDF
import os

class SalesPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'Guide Commercial - Sites Web Artisans', align='R')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(0, 82, 147)  # Blue
        self.cell(0, 10, title, ln=True)
        self.ln(5)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, ln=True)
        self.ln(2)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, text)
        self.ln(3)

    def quote_text(self, text):
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(80, 80, 80)
        self.set_x(15)
        self.multi_cell(0, 6, f'"{text}"')
        self.ln(3)

    def bullet_point(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.cell(8, 6, chr(149))  # bullet
        x = self.get_x()
        self.multi_cell(0, 6, text)
        self.set_x(10)  # Reset to left margin

    def key_stat(self, stat, description):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(0, 120, 60)  # Green
        self.cell(0, 7, stat, ln=True)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, description)
        self.ln(2)


def create_sales_pdf():
    pdf = SalesPDF()
    pdf.add_page()

    # Title Page
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(0, 82, 147)
    pdf.ln(40)
    pdf.cell(0, 15, 'Guide Commercial', ln=True, align='C')
    pdf.set_font('Helvetica', 'B', 22)
    pdf.cell(0, 12, 'Vente de Sites Web', ln=True, align='C')
    pdf.cell(0, 12, 'pour Artisans', ln=True, align='C')
    pdf.ln(20)
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, 'Document de Formation', ln=True, align='C')
    pdf.cell(0, 10, "pour l'Equipe Commerciale", ln=True, align='C')
    pdf.ln(40)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.cell(0, 10, 'Document Interne - Confidentiel', ln=True, align='C')

    # Page 2 - Proposition de Valeur
    pdf.add_page()
    pdf.chapter_title('1. Notre Proposition de Valeur')

    pdf.section_title('Le Probleme que Nous Resolvons')
    pdf.key_stat('87% des clients recherchent un artisan sur internet',
                 'avant de passer un appel telephonique.')

    pdf.body_text('Pourtant, la majorite des artisans ont une presence en ligne insuffisante :')
    pdf.bullet_point('Pas de site web ou site obsolete depuis des annees')
    pdf.bullet_point('Fiche Google My Business incomplete ou mal optimisee')
    pdf.bullet_point('Aucune visibilite sur les recherches locales')
    pdf.bullet_point('Dependance totale au bouche-a-oreille')
    pdf.ln(5)

    pdf.section_title('Notre Solution')
    pdf.body_text('Nous creons des sites web professionnels cles en main specialement concus pour les artisans :')
    pdf.bullet_point('Design moderne et adapte mobile')
    pdf.bullet_point('Optimise pour Google (SEO local)')
    pdf.bullet_point('Formulaire de contact et demande de devis')
    pdf.bullet_point('Mise en ligne en 48-72h')

    # Page 3 - Arguments de Vente
    pdf.add_page()
    pdf.chapter_title('2. Arguments de Vente Cles')

    pdf.section_title('Argument 1 : Visibilite Locale')
    pdf.quote_text('Quand quelqu\'un cherche plombier + votre ville sur Google, est-ce que vous apparaissez ?')
    pdf.ln(3)
    pdf.key_stat('46%', 'des recherches Google ont une intention locale')
    pdf.key_stat('78%', 'des recherches mobiles locales menent a un achat')
    pdf.key_stat('75%', 'des clics vont aux 3 premiers resultats Google')
    pdf.ln(3)
    pdf.body_text('Ce que ca signifie : "Chaque jour, des clients potentiels dans votre zone cherchent vos services. Sans site web optimise, ils appellent vos concurrents."')

    pdf.ln(5)
    pdf.section_title('Argument 2 : Credibilite et Confiance')
    pdf.quote_text('Quand un client hesite entre deux artisans, il choisit celui qui a l\'air le plus professionnel.')
    pdf.body_text('Un site web apporte : image professionnelle, presentation des realisations, avis clients visibles, coordonnees accessibles.')
    pdf.body_text('Phrase cle : "Un site web, c\'est votre vitrine 24h/24. Meme sur un chantier, votre site travaille pour vous."')

    pdf.ln(5)
    pdf.section_title('Argument 3 : Retour sur Investissement')
    pdf.quote_text('Combien vous coute un nouveau client aujourd\'hui ?')
    pdf.body_text('Exemple : Si intervention moyenne = 300EUR et le site apporte 3 clients/mois supplementaires = 900EUR. Site rentabilise en moins de 2 mois.')

    # Page 4 - Objections
    pdf.add_page()
    pdf.chapter_title('3. Reponses aux Objections')

    objections = [
        ("Je n'ai pas le temps",
         "Justement, c'est pour ca qu'on s'occupe de tout. 15 minutes au telephone, et on fait le reste."),
        ("C'est trop cher",
         "Un seul client supplementaire par mois a 300EUR = rentabilise en 2-3 mois. C'est un investissement."),
        ("J'ai deja assez de travail",
         "Super ! Mais ca sera toujours le cas ? Un site = securite. Et le choix de vos clients."),
        ("Je fonctionne au bouche-a-oreille",
         "Quand on recommande quelqu'un, les gens verifient sur Google. Sans site, vous perdez ces clients."),
        ("Mon neveu peut me faire un site",
         "Connait-il le SEO local ? Un site non trouve = carte de visite au fond d'un tiroir."),
        ("J'ai deja Facebook",
         "Facebook n'est pas un site pro. Les recherches d'artisans passent par Google, pas Facebook."),
    ]

    for objection, reponse in objections:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(180, 0, 0)
        pdf.cell(0, 7, f'"{objection}"', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 100, 0)
        pdf.multi_cell(0, 5, f'-> {reponse}')
        pdf.ln(3)

    # Page 5 - Script d'appel
    pdf.add_page()
    pdf.chapter_title('4. Script d\'Appel Type')

    pdf.section_title('Introduction (30 sec)')
    pdf.body_text('"Bonjour [Nom], c\'est [Votre nom]. J\'ai vu votre entreprise sur Google Maps avec [X] avis, c\'est vraiment bien ! Je travaille avec des artisans pour les aider a avoir plus de clients. Vous avez 2 minutes ?"')

    pdf.section_title('Questions de Decouverte')
    pdf.bullet_point('Vous avez un site web actuellement ?')
    pdf.bullet_point('Comment trouvez-vous vos clients aujourd\'hui ?')
    pdf.bullet_point('Satisfait du nombre de demandes recues ?')
    pdf.bullet_point('Vous apparaissez sur Google pour [metier] + [ville] ?')

    pdf.section_title('Presentation (2 min)')
    pdf.body_text('"On cree votre site pro en 48-72h, optimise Google. Presentation services, realisations, contact direct. Tout inclus : design, hebergement, domaine."')

    pdf.section_title('Cloture')
    pdf.body_text('Si interesse : "Pour avancer, j\'ai besoin de quelques infos. 10-15 min maintenant ou formulaire par email ?"')
    pdf.body_text('Si hesitant : "Je vous envoie un exemple de site pour un [meme metier] ?"')

    # Page 6 - Offre et Tarifs
    pdf.add_page()
    pdf.chapter_title('5. Notre Offre')

    pdf.section_title('Ce qui est Inclus')
    inclus = [
        'Site web complet (5-7 pages)',
        'Design personnalise aux couleurs de l\'entreprise',
        'Responsive (mobile, tablette, PC)',
        'Formulaire de contact + demande de devis',
        'Optimisation Google (SEO local)',
        'Hebergement 1 an inclus',
        'Nom de domaine .fr',
        'Certificat SSL (site securise)',
    ]
    for item in inclus:
        pdf.bullet_point(item)

    pdf.ln(5)
    pdf.section_title('Tarification')
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(60, 8, 'Formule', border=1)
    pdf.cell(40, 8, 'Prix', border=1)
    pdf.cell(0, 8, 'Ideal pour', border=1, ln=True)

    pdf.set_font('Helvetica', '', 10)
    tarifs = [
        ('Essentiel', '490 EUR', 'Artisan solo, demarrage'),
        ('Professionnel', '790 EUR', 'PME, plusieurs services'),
        ('Premium', '1190 EUR', 'Entreprise etablie, galerie'),
    ]
    for formule, prix, ideal in tarifs:
        pdf.cell(60, 7, formule, border=1)
        pdf.cell(40, 7, prix, border=1)
        pdf.cell(0, 7, ideal, border=1, ln=True)

    pdf.ln(5)
    pdf.body_text('Paiement en 2-3 fois possible')
    pdf.body_text('Delai de livraison : 48-72h apres reception des informations')

    # Page 7 - Recap
    pdf.add_page()
    pdf.chapter_title('6. Les 5 Points Cles a Retenir')

    points = [
        ('87% des clients cherchent sur Google', 'Sans site, vous etes invisible pour eux'),
        ('Un site = credibilite', 'Les clients font confiance aux professionnels avec un site'),
        ('ROI rapide', 'Rentabilise en 2-3 clients supplementaires seulement'),
        ('On s\'occupe de tout', '15 minutes de votre temps, c\'est tout ce qu\'il faut'),
        ('48-72h', 'Votre site est en ligne en quelques jours seulement'),
    ]

    for i, (titre, desc) in enumerate(points, 1):
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 82, 147)
        pdf.cell(10, 10, str(i))
        pdf.cell(0, 10, titre, ln=True)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.set_x(20)
        pdf.multi_cell(0, 6, desc)
        pdf.ln(5)

    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, 'Document interne - Ne pas diffuser aux clients', ln=True, align='C')
    pdf.cell(0, 10, 'Version 1.0 - Janvier 2025', ln=True, align='C')

    # Save
    output_path = os.path.join(os.path.dirname(__file__), 'Guide_Commercial_Sites_Artisans.pdf')
    pdf.output(output_path)
    print(f'PDF genere : {output_path}')
    return output_path


if __name__ == '__main__':
    create_sales_pdf()
