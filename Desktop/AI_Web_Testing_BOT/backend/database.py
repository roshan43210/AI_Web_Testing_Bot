# database.py
import sqlite3
from datetime import datetime
import os

DB_PATH = "web_testing.db"

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            test_date TEXT NOT NULL,
            total_links INTEGER,
            working_links INTEGER,
            broken_links INTEGER,
            success_rate REAL,
            risk_score REAL,
            ai_summary TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS link_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER,
            url TEXT NOT NULL,
            status INTEGER,
            error_detail TEXT,
            severity TEXT,
            risk_score INTEGER,
            ui_anomalies TEXT,
            FOREIGN KEY (test_id) REFERENCES test_history (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_test_result(url, results):
    """Save test result to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate stats
    total = len(results)
    working = sum(1 for r in results if r.get('status', 0) >= 200 and r.get('status', 0) < 400)
    broken = total - working
    success_rate = (working / total * 100) if total > 0 else 0
    avg_risk = sum(r.get('risk_score', 0) for r in results) / total if total > 0 else 0
    
    # Get AI summary
    from backend.analyzer import generate_ai_summary
    ai_summary = generate_ai_summary(results, url)
    
    # Insert test record
    cursor.execute('''
        INSERT INTO test_history (url, test_date, total_links, working_links, broken_links, success_rate, risk_score, ai_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (url, datetime.now().isoformat(), total, working, broken, success_rate, avg_risk, ai_summary))
    
    test_id = cursor.lastrowid
    
    # Insert link details
    for r in results:
        cursor.execute('''
            INSERT INTO link_details (test_id, url, status, error_detail, severity, risk_score, ui_anomalies)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (test_id, r.get('url'), r.get('status'), r.get('error_detail'), 
              r.get('severity'), r.get('risk_score'), str(r.get('ui_anomalies', []))))
    
    conn.commit()
    conn.close()
    
    return test_id

def get_history(url=None, limit=10):
    """Get test history"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if url:
        cursor.execute('''
            SELECT * FROM test_history 
            WHERE url = ? 
            ORDER BY test_date DESC 
            LIMIT ?
        ''', (url, limit))
    else:
        cursor.execute('''
            SELECT * FROM test_history 
            ORDER BY test_date DESC 
            LIMIT ?
        ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_test_details(test_id):
    """Get details for a specific test"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM link_details 
        WHERE test_id = ?
    ''', (test_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results
