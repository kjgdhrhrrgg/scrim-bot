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

        # Check if user is already in a ready scrim for this hour
        c.execute("SELECT user_ids FROM ready WHERE hour = ?", (hour,))
        ready_rows = c.fetchall()
        for row in ready_rows:
            ready_user_ids = json.loads(row[0])
            if user_id in ready_user_ids:
                raise ValueError("You are already locked in a ready scrim at this hour.")

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

                # Check if main role is full and handle ready logic
                if role == "main" and len(user_ids) >= 6:
                    c.execute(
                        "INSERT INTO ready (team, hour, user_ids) VALUES (?, ?, ?)",
                        (team, hour, json.dumps(user_ids)),
                    )

                    # Check if sub is also empty before deleting
                    c.execute(
                        "SELECT user_ids FROM signups WHERE team = ? AND hour = ? AND role = ?",
                        (team, hour, "sub"),
                    )
                    sub_row = c.fetchone()
                    if sub_row:
                        sub_user_ids = json.loads(sub_row[0])
                        if not sub_user_ids:
                            c.execute(
                                "DELETE FROM signups WHERE team = ? AND hour = ? AND role IN (?, ?)",
                                (team, hour, "main", "sub"),
                            )
                    else:
                        c.execute(
                            "DELETE FROM signups WHERE team = ? AND hour = ? AND role = ?",
                            (team, hour, role),
                        )

        db.commit()


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

def get_list(table):
    with get_db() as db:
        c = db.cursor()
        c.execute(f"SELECT * FROM {table}")
        rows = c.fetchall()

        if not rows:
            return []

        if table == "signups":
            return [
                {
                    "team": row[1],
                    "hour": row[2],
                    "role": row[3],
                    "user_ids": json.loads(row[4]),
                }
                for row in rows
            ]
        elif table == "ready":
            return [
                {
                    "team": row[1],
                    "hour": row[2],
                    "user_ids": json.loads(row[3]),
                }
                for row in rows
            ]
        else:
            raise ValueError("Unknown table name")
        
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
