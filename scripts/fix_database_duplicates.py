"""
Script to fix database issues:
1. Remove massive duplicates (same name, no phone)
2. Keep only unique entries
3. Report statistics
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def fix_database():
    db_path = Path(__file__).parent.parent / "data" / "whatsapp_artisans.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("DATABASE CLEANUP SCRIPT")
    print("=" * 80)

    # Get initial stats
    cursor.execute("SELECT COUNT(*) FROM artisans")
    initial_count = cursor.fetchone()[0]
    print(f"\nInitial count: {initial_count}")

    cursor.execute("SELECT COUNT(*) FROM artisans WHERE telephone IS NULL")
    null_phone_count = cursor.fetchone()[0]
    print(f"Entries with NULL phone: {null_phone_count}")

    # Find duplicates (same nom_entreprise + ville + departement, no phone)
    cursor.execute("""
        SELECT nom_entreprise, ville, departement, COUNT(*) as count
        FROM artisans
        WHERE telephone IS NULL
        GROUP BY nom_entreprise, ville, departement
        HAVING count > 1
        ORDER BY count DESC
    """)
    duplicates = cursor.fetchall()
    print(f"\nFound {len(duplicates)} duplicate groups (NULL phone)")

    total_to_delete = 0
    for nom, ville, dept, count in duplicates[:10]:
        print(f"  {nom} ({ville}, {dept}): {count} duplicates")
        total_to_delete += (count - 1)  # Keep one, delete the rest

    if len(duplicates) > 10:
        for nom, ville, dept, count in duplicates[10:]:
            total_to_delete += (count - 1)

    print(f"\nTotal duplicates to remove: {total_to_delete}")

    # Ask for confirmation
    response = input("\nDo you want to proceed with cleanup? (yes/no): ")
    if response.lower() != 'yes':
        print("Cleanup cancelled.")
        conn.close()
        return

    # Delete duplicates, keeping only the oldest entry (lowest ID) for each group
    deleted = 0
    for nom, ville, dept, count in duplicates:
        # Get all IDs for this duplicate group
        cursor.execute("""
            SELECT id FROM artisans
            WHERE nom_entreprise = ? AND ville IS ? AND departement = ? AND telephone IS NULL
            ORDER BY id ASC
        """, (nom, ville, dept))

        ids = [row[0] for row in cursor.fetchall()]
        if len(ids) > 1:
            # Keep the first (oldest) entry, delete the rest
            ids_to_delete = ids[1:]
            cursor.execute(f"""
                DELETE FROM artisans WHERE id IN ({','.join('?' * len(ids_to_delete))})
            """, ids_to_delete)
            deleted += len(ids_to_delete)

    conn.commit()

    # Get final stats
    cursor.execute("SELECT COUNT(*) FROM artisans")
    final_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM artisans WHERE telephone IS NULL")
    final_null_phone = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM artisans WHERE telephone IS NOT NULL")
    final_with_phone = cursor.fetchone()[0]

    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print(f"\nInitial entries: {initial_count}")
    print(f"Deleted duplicates: {deleted}")
    print(f"Final entries: {final_count}")
    print(f"  With phone: {final_with_phone}")
    print(f"  Without phone: {final_null_phone}")
    print(f"\nReduction: {initial_count - final_count} entries removed")

    conn.close()

if __name__ == "__main__":
    fix_database()
