from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "maintenance.db"

app = Flask(__name__)


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with closing(get_connection()) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                equipment_type TEXT NOT NULL,
                status TEXT NOT NULL,
                serial_number TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                last_service_date TEXT,
                next_service_date TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                service_date TEXT NOT NULL,
                technician TEXT NOT NULL,
                outcome TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE CASCADE
            );
            """
        )
        connection.commit()


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def dashboard_summary(connection: sqlite3.Connection) -> dict:
    total = connection.execute("SELECT COUNT(*) AS count FROM equipment").fetchone()["count"]
    service_due = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM equipment
        WHERE next_service_date IS NOT NULL
          AND date(next_service_date) <= date(?)
        """,
        ((date.today() + timedelta(days=14)).isoformat(),),
    ).fetchone()["count"]
    in_service = connection.execute(
        "SELECT COUNT(*) AS count FROM equipment WHERE status = ?",
        ("In Service",),
    ).fetchone()["count"]
    maintenance_count = connection.execute(
        "SELECT COUNT(*) AS count FROM maintenance_records"
    ).fetchone()["count"]
    return {
        "totalEquipment": total,
        "serviceDueSoon": service_due,
        "inService": in_service,
        "maintenanceRecords": maintenance_count,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "Equipment maintenance system is running"})


@app.route("/api/dashboard")
def dashboard():
    with closing(get_connection()) as connection:
        summary = dashboard_summary(connection)
        due_items = connection.execute(
            """
            SELECT *
            FROM equipment
            WHERE next_service_date IS NOT NULL
              AND date(next_service_date) <= date(?)
            ORDER BY date(next_service_date) ASC
            LIMIT 5
            """,
            ((date.today() + timedelta(days=14)).isoformat(),),
        ).fetchall()
    return jsonify(
        {
            "summary": summary,
            "dueSoon": [row_to_dict(item) for item in due_items],
        }
    )


@app.route("/api/equipment", methods=["GET", "POST"])
def equipment_collection():
    if request.method == "GET":
        search = request.args.get("search", "").strip()
        status = request.args.get("status", "").strip()
        equipment_type = request.args.get("type", "").strip()

        query = "SELECT * FROM equipment WHERE 1=1"
        params: list[str] = []

        if search:
            query += " AND (name LIKE ? OR serial_number LIKE ? OR location LIKE ?)"
            like_term = f"%{search}%"
            params.extend([like_term, like_term, like_term])
        if status:
            query += " AND status = ?"
            params.append(status)
        if equipment_type:
            query += " AND equipment_type = ?"
            params.append(equipment_type)

        query += " ORDER BY created_at DESC"

        with closing(get_connection()) as connection:
            rows = connection.execute(query, params).fetchall()
        return jsonify([row_to_dict(row) for row in rows])

    payload = request.get_json(force=True)
    required_fields = ["name", "equipment_type", "status", "serial_number", "location"]
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    with closing(get_connection()) as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO equipment (
                    name, equipment_type, status, serial_number, location,
                    last_service_date, next_service_date, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["name"],
                    payload["equipment_type"],
                    payload["status"],
                    payload["serial_number"],
                    payload["location"],
                    payload.get("last_service_date"),
                    payload.get("next_service_date"),
                    payload.get("notes", ""),
                ),
            )
            connection.commit()
            created = connection.execute(
                "SELECT * FROM equipment WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        except sqlite3.IntegrityError:
            return jsonify({"error": "Serial number must be unique"}), 400

    return jsonify(row_to_dict(created)), 201


@app.route("/api/equipment/<int:equipment_id>", methods=["PUT", "DELETE"])
def equipment_item(equipment_id: int):
    with closing(get_connection()) as connection:
        existing = connection.execute(
            "SELECT * FROM equipment WHERE id = ?", (equipment_id,)
        ).fetchone()
        if not existing:
            return jsonify({"error": "Equipment not found"}), 404

        if request.method == "DELETE":
            connection.execute("DELETE FROM maintenance_records WHERE equipment_id = ?", (equipment_id,))
            connection.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
            connection.commit()
            return jsonify({"message": "Equipment deleted"})

        payload = request.get_json(force=True)
        try:
            connection.execute(
                """
                UPDATE equipment
                SET name = ?, equipment_type = ?, status = ?, serial_number = ?,
                    location = ?, last_service_date = ?, next_service_date = ?, notes = ?
                WHERE id = ?
                """,
                (
                    payload.get("name", existing["name"]),
                    payload.get("equipment_type", existing["equipment_type"]),
                    payload.get("status", existing["status"]),
                    payload.get("serial_number", existing["serial_number"]),
                    payload.get("location", existing["location"]),
                    payload.get("last_service_date", existing["last_service_date"]),
                    payload.get("next_service_date", existing["next_service_date"]),
                    payload.get("notes", existing["notes"]),
                    equipment_id,
                ),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            return jsonify({"error": "Serial number must be unique"}), 400

        updated = connection.execute(
            "SELECT * FROM equipment WHERE id = ?", (equipment_id,)
        ).fetchone()
    return jsonify(row_to_dict(updated))


@app.route("/api/maintenance", methods=["GET", "POST"])
def maintenance_collection():
    if request.method == "GET":
        equipment_id = request.args.get("equipment_id")
        query = """
            SELECT maintenance_records.*, equipment.name AS equipment_name, equipment.serial_number
            FROM maintenance_records
            JOIN equipment ON equipment.id = maintenance_records.equipment_id
        """
        params: list[object] = []
        if equipment_id:
            query += " WHERE equipment_id = ?"
            params.append(equipment_id)
        query += " ORDER BY date(service_date) DESC, maintenance_records.id DESC"

        with closing(get_connection()) as connection:
            rows = connection.execute(query, params).fetchall()
        return jsonify([row_to_dict(row) for row in rows])

    payload = request.get_json(force=True)
    required_fields = ["equipment_id", "description", "service_date", "technician", "outcome"]
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    with closing(get_connection()) as connection:
        equipment = connection.execute(
            "SELECT id FROM equipment WHERE id = ?", (payload["equipment_id"],)
        ).fetchone()
        if not equipment:
            return jsonify({"error": "Equipment record does not exist"}), 400

        cursor = connection.execute(
            """
            INSERT INTO maintenance_records (
                equipment_id, description, service_date, technician, outcome
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload["equipment_id"],
                payload["description"],
                payload["service_date"],
                payload["technician"],
                payload["outcome"],
            ),
        )
        connection.execute(
            "UPDATE equipment SET last_service_date = ? WHERE id = ?",
            (payload["service_date"], payload["equipment_id"]),
        )
        connection.commit()
        created = connection.execute(
            "SELECT * FROM maintenance_records WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return jsonify(row_to_dict(created)), 201


@app.route("/api/maintenance/<int:record_id>", methods=["DELETE"])
def maintenance_item(record_id: int):
    with closing(get_connection()) as connection:
        existing = connection.execute(
            "SELECT * FROM maintenance_records WHERE id = ?", (record_id,)
        ).fetchone()
        if not existing:
            return jsonify({"error": "Maintenance record not found"}), 404
        connection.execute("DELETE FROM maintenance_records WHERE id = ?", (record_id,))
        connection.commit()
    return jsonify({"message": "Maintenance record deleted"})


init_db()


if __name__ == "__main__":
    app.run(debug=True)
