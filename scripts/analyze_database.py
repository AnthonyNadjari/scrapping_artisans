#!/usr/bin/env python3
"""Analyse la base de données pour comprendre les doublons et problèmes"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "whatsapp_artisans.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Statistiques générales
cursor.execute("SELECT COUNT(*) FROM artisans")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT telephone) FROM artisans WHERE telephone IS NOT NULL AND telephone != ''")
tel_unique = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM artisans WHERE code_postal IS NULL OR code_postal = ''")
sans_cp = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM artisans WHERE departement IS NULL OR departement = ''")
sans_dept = cursor.fetchone()[0]

# Doublons par téléphone
cursor.execute("""
    SELECT telephone, COUNT(*) as count 
    FROM artisans 
    WHERE telephone IS NOT NULL AND telephone != ''
    GROUP BY telephone 
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 10
""")
doublons_tel = cursor.fetchall()

# Artisans par ville
cursor.execute("""
    SELECT ville, COUNT(*) as count 
    FROM artisans 
    WHERE ville IS NOT NULL AND ville != ''
    GROUP BY ville 
    ORDER BY count DESC
    LIMIT 10
""")
par_ville = cursor.fetchall()

print("=" * 60)
print("ANALYSE DE LA BASE DE DONNEES")
print("=" * 60)
print(f"\nStatistiques generales:")
print(f"   Total artisans: {total}")
print(f"   Artisans avec telephone unique: {tel_unique}")
print(f"   Artisans SANS code postal: {sans_cp} ({sans_cp/total*100:.1f}%)")
print(f"   Artisans SANS departement: {sans_dept} ({sans_dept/total*100:.1f}%)")

if doublons_tel:
    print(f"\nDoublons par telephone (top 10):")
    for tel, count in doublons_tel:
        print(f"   {tel}: {count} fois")

print(f"\nArtisans par ville (top 10):")
for ville, count in par_ville:
    print(f"   {ville}: {count} artisans")

conn.close()

