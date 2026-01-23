"""
Data source management routes for DataPlunge.
Handles listing and disconnecting user data sources.
"""

from flask import Blueprint, jsonify

from auth import login_required, get_current_user
from db import get_db

datasources_bp = Blueprint('datasources', __name__, url_prefix='/user')


@datasources_bp.route("/datasources", methods=["GET"])
@login_required
def get_user_datasources():
    """Get all data sources connected by the current user."""
    user = get_current_user()
    user_id = user['id']

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, source_name, created_at
                FROM datasources
                WHERE user_id = %s
                ORDER BY created_at DESC;
                """,
                (user_id,)
            )
            rows = cursor.fetchall()

            datasources = []
            for row in rows:
                # Get last sync info from performanceMetrics
                cursor.execute(
                    """
                    SELECT MAX(updated_at) as last_sync
                    FROM performanceMetrics pm
                    WHERE pm.data_source_id = %s;
                    """,
                    (row['id'],)
                )
                sync_row = cursor.fetchone()

                datasources.append({
                    'id': row['id'],
                    'source_name': row['source_name'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'last_sync': sync_row['last_sync'].isoformat() if sync_row and sync_row['last_sync'] else None,
                    'status': 'connected'
                })

    return jsonify(datasources), 200


@datasources_bp.route("/datasources/<int:datasource_id>", methods=["DELETE"])
@login_required
def delete_user_datasource(datasource_id):
    """Disconnect a data source (delete with CASCADE)."""
    user = get_current_user()
    user_id = user['id']

    with get_db() as conn:
        with conn.cursor() as cursor:
            # Verify datasource belongs to user
            cursor.execute(
                "SELECT id FROM datasources WHERE id = %s AND user_id = %s;",
                (datasource_id, user_id)
            )
            if not cursor.fetchone():
                return jsonify({"error": "Data source not found or unauthorized"}), 404

            # Delete datasource (CASCADE will handle related data)
            cursor.execute("DELETE FROM datasources WHERE id = %s;", (datasource_id,))
        conn.commit()

    return jsonify({"message": "Data source disconnected successfully"}), 200
