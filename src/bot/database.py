import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'trading_bot.db'))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Portfolio Status (Single row tracking Cash)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_status (
            id INTEGER PRIMARY KEY,
            cash_balance REAL NOT NULL
        )
    ''')
    
    # Initialize with $10,000 if empty
    cursor.execute('SELECT COUNT(*) FROM portfolio_status')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO portfolio_status (id, cash_balance) VALUES (1, 10000.0)')
    
    # Holdings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holdings (
            ticker TEXT PRIMARY KEY,
            amount REAL NOT NULL
        )
    ''')
    
    # Ledger Table (Multi-Asset)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,      -- BUY, SELL
            shares_traded REAL NOT NULL,
            price REAL NOT NULL,
            cash_after REAL NOT NULL,
            portfolio_value_after REAL NOT NULL
        )
    ''')
    
    # Predictions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ticker TEXT NOT NULL,
            predicted_close REAL NOT NULL,
            actual_close REAL,
            error_pct REAL
        )
    ''')
    
    conn.commit()
    conn.close()

def get_portfolio_state():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT cash_balance FROM portfolio_status WHERE id = 1')
    cash = cursor.fetchone()[0]
    
    cursor.execute('SELECT ticker, amount FROM holdings')
    holdings = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    return cash, holdings

def update_portfolio(cash_balance, new_holdings):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE portfolio_status SET cash_balance = ? WHERE id = 1', (float(cash_balance),))
    
    for ticker, amount in new_holdings.items():
        if amount > 0:
            cursor.execute('''
                INSERT INTO holdings (ticker, amount) VALUES (?, ?)
                ON CONFLICT(ticker) DO UPDATE SET amount=excluded.amount
            ''', (ticker, float(amount)))
        else:
            cursor.execute('DELETE FROM holdings WHERE ticker = ?', (ticker,))
            
    conn.commit()
    conn.close()

def log_trade(ticker, action, shares_traded, price, cash_after, portfolio_value_after):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO ledger (timestamp, ticker, action, shares_traded, price, cash_after, portfolio_value_after)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, ticker, action, float(shares_traded), float(price), float(cash_after), float(portfolio_value_after)))
    
    conn.commit()
    conn.close()

def log_prediction(ticker, predicted_close):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        INSERT INTO predictions (timestamp, ticker, predicted_close)
        VALUES (?, ?, ?)
    ''', (timestamp, ticker, float(predicted_close)))
    
    conn.commit()
    conn.close()

def update_actual_price(ticker, actual_close):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, predicted_close FROM predictions 
        WHERE ticker = ? AND actual_close IS NULL 
        ORDER BY timestamp DESC LIMIT 1
    ''', (ticker,))
        
    row = cursor.fetchone()
    
    if row:
        pred_id, predicted_close = row
        error_pct = abs((float(actual_close) - float(predicted_close)) / float(actual_close)) * 100
        
        cursor.execute('''
            UPDATE predictions 
            SET actual_close = ?, error_pct = ?
            WHERE id = ?
        ''', (float(actual_close), float(error_pct), pred_id))
        
        conn.commit()
        conn.close()
        return error_pct
        
    conn.close()
    return None

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
