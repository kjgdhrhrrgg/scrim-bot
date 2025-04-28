import sqlite3
import os
import json

DB_PATH = "./data/scrims.db"


def get_db():
    os.makedirs("./data", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_db() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT,
            hour INTEGER,
            role TEXT,
            user_ids TEXT
            )
        """)
        c.execute(""" 
            CREATE TABLE IF NOT EXISTS teams (
            name TEXT PRIMARY KEY,
            max_size INTEGER DEFAULT 6
            )
        """)

        # Create ready table
        c.execute("""
            CREATE TABLE IF NOT EXISTS ready (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT,
                hour INTEGER,
                user_ids TEXT
            )
        """)
        c.commit()

def can(team, hour, user_id, role):
    with get_db() as db:
        c = db.cursor()

        # Ensure both roles exist
        for r in ["main", "sub"]:
            c.execute(
                "SELECT id FROM signups WHERE team = ? AND hour = ? AND role = ?",
                (team, hour, r),
            )
            exists = c.fetchone()
            if not exists:
                c.execute(
                    "INSERT INTO signups (team, hour, role, user_ids) VALUES (?, ?, ?, ?)",
                    (team, hour, r, json.dumps([])),
                )

        # Remove user from the other role if present
        opposite_role = "sub" if role == "main" else "main"
        c.execute(
            "SELECT id, user_ids FROM signups WHERE team = ? AND hour = ? AND role = ?",
            (team, hour, opposite_role),
        )
        row = c.fetchone()
        if row:
            opp_signup_id, opp_user_ids_json = row
            opp_user_ids = json.loads(opp_user_ids_json)
            if user_id in opp_user_ids:
                opp_user_ids.remove(user_id)
                if opp_user_ids:
                    c.execute(
                        "UPDATE signups SET user_ids = ? WHERE id = ?",
                        (json.dumps(opp_user_ids), opp_signup_id),
                    )
                else:
                    c.execute("DELETE FROM signups WHERE id = ?", (opp_signup_id,))

        # Add user to the selected role if not already present
        c.execute(
            "SELECT id, user_ids FROM signups WHERE team = ? AND hour = ? AND role = ?",
            (team, hour, role),
        )
        row = c.fetchone()

        if row:
            signup_id, user_ids_json = row
            user_ids = json.loads(user_ids_json)

            if user_id not in user_ids:
                user_ids.append(user_id)
                c.execute(
                    "UPDATE signups SET user_ids = ? WHERE id = ?",
                    (json.dumps(user_ids), signup_id),
                )

                if role == "main" and len(user_ids) >= 6:
                    c.execute("INSERT INTO ready (team, hour, user_ids) VALUES (?, ?, ?)",
                        (team, hour, json.dumps(user_ids)),
                    )
                    c.execute(
                        "DELETE FROM signups WHERE team = ? AND hour = ? AND role = ?",
                        (team, hour, role),
                    )

def drop(team, hour, user_id):
    with get_db() as db:
        c = db.cursor()

        roles = ["main", "sub"]
        updated = False

        for role in roles:
            c.execute(
                "SELECT id, user_ids FROM signups WHERE team = ? AND hour = ? AND role = ?",
                (team, hour, role),
            )
            row = c.fetchone()

            if row:
                signup_id, user_ids_json = row
                user_ids = json.loads(user_ids_json)

                if user_id in user_ids:
                    user_ids.remove(user_id)
                    updated = True
                    if user_ids:
                        c.execute(
                            "UPDATE signups SET user_ids = ? WHERE id = ?",
                            (json.dumps(user_ids), signup_id),
                        )
                    else:
                        c.execute("DELETE FROM signups WHERE id = ?", (signup_id,))

        # Final safety check: see if both roles are now empty
        empty_roles = []
        for role in roles:
            c.execute(
                "SELECT id, user_ids FROM signups WHERE team = ? AND hour = ? AND role = ?",
                (team, hour, role),
            )
            row = c.fetchone()
            if row:
                _, user_ids_json = row
                user_ids = json.loads(user_ids_json)
                if not user_ids:
                    empty_roles.append(role)

        for role in empty_roles:
            c.execute(
                "DELETE FROM signups WHERE team = ? AND hour = ? AND role = ?",
                (team, hour, role),
            )

        if not updated:
            raise ValueError("You are not signed up for this scrim.")

        db.commit()

def get_list():
    with get_db() as db:
        c = db.cursor()
        c.execute("SELECT * FROM signups")
        rows = c.fetchall()
    
        if not rows:
            return []

        return [
            {
                "team": row[1],
                "hour": row[2],
                "role": row[3],
                "user_ids": json.loads(row[4]),
            }
            for row in rows
        ]
        
def dropall(user_id):
    with get_db() as db:
        c = db.cursor()

        # Fetch everything we need
        c.execute("SELECT id, team, hour, role, user_ids FROM signups")
        rows = c.fetchall()

        affected = set()  # track (team, hour)

        for signup_id, team, hour, role, user_ids_json in rows:
            user_ids = json.loads(user_ids_json)

            if user_id in user_ids:
                user_ids.remove(user_id)
                affected.add((team, hour))  # mark this (team, hour) for later

                if len(user_ids) == 0:
                    c.execute("DELETE FROM signups WHERE id = ?", (signup_id,))
                else:
                    c.execute(
                        "UPDATE signups SET user_ids = ? WHERE id = ?",
                        (json.dumps(user_ids), signup_id),
                    )

        # Now check if BOTH main and sub are empty for each affected (team, hour)
        for team, hour in affected:
            c.execute(
                "SELECT role, user_ids FROM signups WHERE team = ? AND hour = ?",
                (team, hour),
            )
            role_rows = c.fetchall()

            completely_empty = True
            for role, user_ids_json in role_rows:
                user_ids = json.loads(user_ids_json)
                if user_ids:  # still someone left
                    completely_empty = False
                    break

            if completely_empty:
                c.execute(
                    "DELETE FROM signups WHERE team = ? AND hour = ?",
                    (team, hour),
                )

        db.commit()

def reset():
    with get_db() as db:
        db.execute("DELETE FROM signups")
        db.execute("DELETE FROM ready")
        db.commit()
