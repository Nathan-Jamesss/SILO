import sqlite3
import json
import os
import sys

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def export_data():
    db_path = os.path.join(os.path.dirname(__file__), 'launchradar.db')
    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'silo-web', 'public', 'data.json')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Exporting empty list.")
        opportunities = []
    else:
        conn = sqlite3.connect(db_path)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM opportunities ORDER BY scraped_at DESC")
        opportunities = cursor.fetchall()
        conn.close()
        
    data = {
        "opportunities": opportunities
    }
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Exported {len(opportunities)} opportunities to {out_path}")

if __name__ == "__main__":
    export_data()
