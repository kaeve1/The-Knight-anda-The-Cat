"""Score session state + SQLite persistence."""
import os
import sqlite3
from datetime import datetime

_DB = './data/scores.db'

# ── Session state (resets each New Game) ─────────────────────────
_session_score      = 0
_next_life_thresh   = 100


def reset():
    global _session_score, _next_life_thresh
    _session_score    = 0
    _next_life_thresh = 100


def add_points(pts, player):
    """Retorna True se o player ganhou uma vida."""
    global _session_score, _next_life_thresh
    _session_score += pts
    gained = False
    while _session_score >= _next_life_thresh:
        if player.hp < player.MAX_HP:
            player.hp += 1
            gained = True
        _next_life_thresh += 100
    return gained


def get_score():
    return _session_score


# ── SQLite persistence ───────────────────────────────────────────

def _init():
    os.makedirs('./data', exist_ok=True)
    conn = sqlite3.connect(_DB)
    conn.execute(
        'CREATE TABLE IF NOT EXISTS scores ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'score INTEGER NOT NULL,'
        'difficulty TEXT NOT NULL,'
        'date TEXT NOT NULL'
        ')'
    )
    conn.commit()
    conn.close()


def save_score(score, difficulty):
    if score <= 0:
        return
    _init()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    conn = sqlite3.connect(_DB)
    conn.execute('INSERT INTO scores (score, difficulty, date) VALUES (?, ?, ?)',
                 (score, difficulty, now))
    conn.commit()
    conn.close()


def get_top_scores(limit=10):
    _init()
    conn = sqlite3.connect(_DB)
    rows = conn.execute(
        'SELECT score, difficulty, date FROM scores ORDER BY score DESC LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    return rows
