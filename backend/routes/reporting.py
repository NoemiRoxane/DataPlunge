"""
Reporting and analytics routes for DataPlunge.
Provides aggregated performance data across all platforms.
"""

from flask import Blueprint, jsonify, request

from auth import login_required
from db import get_db

reporting_bp = Blueprint('reporting', __name__)


@reporting_bp.route("/filter-performance", methods=["GET"])
@login_required
def filter_performance():
    """Filter performance metrics by date range."""
    time_range = request.args.get("range")
    value = request.args.get("value")

    with get_db() as conn:
        with conn.cursor() as cursor:
            if time_range == "day":
                cursor.execute(
                    """
                    SELECT pm.date, pm.costs, pm.conversions, pm.cost_per_conversion,
                           pm.impressions, pm.clicks, pm.sessions, pm.cost_per_click,
                           ds.source_name
                    FROM performanceMetrics pm
                    JOIN datasources ds ON pm.data_source_id = ds.id
                    WHERE pm.date = %s;
                    """,
                    (value,),
                )
            elif time_range == "range":
                start_date, end_date = (value or "").split("|")
                cursor.execute(
                    """
                    SELECT pm.date, pm.costs, pm.conversions, pm.cost_per_conversion,
                           pm.impressions, pm.clicks, pm.sessions, pm.cost_per_click,
                           ds.source_name
                    FROM performanceMetrics pm
                    JOIN datasources ds ON pm.data_source_id = ds.id
                    WHERE pm.date BETWEEN %s AND %s;
                    """,
                    (start_date, end_date),
                )
            else:
                return jsonify({"error": "Invalid range"}), 400

            rows = cursor.fetchall()

    return jsonify(
        [
            {
                "date": r["date"],
                "costs": r["costs"],
                "conversions": r["conversions"],
                "cost_per_conversion": r["cost_per_conversion"],
                "impressions": r["impressions"],
                "clicks": r["clicks"],
                "sessions": r["sessions"],
                "cost_per_click": r["cost_per_click"],
                "source": r["source_name"],
            }
            for r in rows
        ]
    )


@reporting_bp.route("/insights", methods=["GET"])
@login_required
def get_insights():
    """Get AI-generated insights about performance trends."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    # Aggregate to ONE row per day
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pm.date,
                    SUM(pm.costs) AS costs,
                    SUM(pm.conversions) AS conversions,
                    CASE
                        WHEN SUM(pm.conversions) > 0 THEN SUM(pm.costs) / SUM(pm.conversions)
                        ELSE 0
                    END AS cost_per_conversion,
                    SUM(pm.impressions) AS impressions,
                    SUM(pm.clicks) AS clicks,
                    SUM(pm.sessions) AS sessions,
                    CASE
                        WHEN SUM(pm.clicks) > 0 THEN SUM(pm.costs) / SUM(pm.clicks)
                        ELSE 0
                    END AS cost_per_click
                FROM performanceMetrics pm
                WHERE pm.date BETWEEN %s AND %s
                GROUP BY pm.date
                ORDER BY pm.date;
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()

    # Return empty list if no data
    if not rows:
        return jsonify([]), 200

    # Compute summary stats
    total_costs = sum(float(r["costs"] or 0) for r in rows)
    total_conversions = sum(float(r["conversions"] or 0) for r in rows)
    avg_cpa = (total_costs / total_conversions) if total_conversions else 0

    highest_cost_day = max(rows, key=lambda x: float(x["costs"] or 0))
    highest_conv_day = max(rows, key=lambda x: float(x["conversions"] or 0))

    best_cpa_day = None
    rows_with_conv = [r for r in rows if float(r["conversions"] or 0) > 0]
    if rows_with_conv:
        best_cpa_day = min(rows_with_conv, key=lambda x: float(x["cost_per_conversion"] or 0))

    first = rows[0]
    last = rows[-1]
    first_cost = float(first["costs"] or 0)
    last_cost = float(last["costs"] or 0)
    cost_change_pct = ((last_cost - first_cost) / first_cost * 100) if first_cost else 0

    # Build insights
    insights = [
        {
            "date": highest_cost_day["date"].isoformat(),
            "message": (
                f"Highest costs were on {highest_cost_day['date'].isoformat()} "
                f"with CHF {float(highest_cost_day['costs'] or 0):.2f}."
            ),
        },
        {
            "message": f"Average cost per conversion for the period: CHF {avg_cpa:.2f}."
        },
        {
            "message": (
                f"Cost trend from {first['date'].isoformat()} → {last['date'].isoformat()}: "
                f"{cost_change_pct:+.2f}%."
            )
        },
        {
            "date": highest_conv_day["date"].isoformat(),
            "message": (
                f"Most conversions were on {highest_conv_day['date'].isoformat()} "
                f"({float(highest_conv_day['conversions'] or 0):.0f} conversions)."
            ),
        },
    ]

    if best_cpa_day:
        insights.append(
            {
                "date": best_cpa_day["date"].isoformat(),
                "message": (
                    f"Best cost per conversion was on {best_cpa_day['date'].isoformat()}: "
                    f"CHF {float(best_cpa_day['cost_per_conversion'] or 0):.2f}."
                ),
            }
        )

    return jsonify(insights), 200


@reporting_bp.route("/aggregated-performance", methods=["GET"])
@login_required
def get_aggregated_performance():
    """Get channel-level aggregated performance metrics."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ds.source_name AS channel,
                    SUM(pm.costs) AS total_costs,
                    SUM(pm.impressions) AS total_impressions,
                    SUM(pm.clicks) AS total_clicks,
                    CASE WHEN SUM(pm.clicks) > 0 THEN SUM(pm.costs) / SUM(pm.clicks) ELSE 0 END AS cost_per_click,
                    SUM(pm.sessions) AS total_sessions,
                    SUM(pm.conversions) AS total_conversions,
                    CASE WHEN SUM(pm.conversions) > 0 THEN SUM(pm.costs) / SUM(pm.conversions) ELSE 0 END AS cost_per_conversion
                FROM performanceMetrics pm
                JOIN datasources ds ON pm.data_source_id = ds.id
                WHERE pm.date BETWEEN %s AND %s
                GROUP BY ds.source_name
                ORDER BY ds.source_name;
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()

    return jsonify(
        [
            {
                "source": r["channel"],
                "costs": float(r["total_costs"]),
                "impressions": r["total_impressions"],
                "clicks": r["total_clicks"],
                "cost_per_click": float(r["cost_per_click"]),
                "sessions": r["total_sessions"],
                "conversions": r["total_conversions"],
                "cost_per_conversion": float(r["cost_per_conversion"]),
            }
            for r in rows
        ]
    )


@reporting_bp.route("/get-campaigns", methods=["GET"])
@login_required
def get_campaigns():
    """Get campaign-level performance breakdown."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ds.source_name AS traffic_source,
                    c.campaign_name,
                    SUM(pm.costs) AS total_costs,
                    SUM(pm.impressions) AS total_impressions,
                    SUM(pm.clicks) AS total_clicks,
                    CASE WHEN SUM(pm.clicks) > 0 THEN SUM(pm.costs) / SUM(pm.clicks) ELSE 0 END AS avg_cpc,
                    SUM(pm.sessions) AS total_sessions,
                    CASE WHEN SUM(pm.sessions) > 0 THEN SUM(pm.costs) / SUM(pm.sessions) ELSE 0 END AS avg_cost_per_session,
                    SUM(pm.conversions) AS total_conversions,
                    CASE WHEN SUM(pm.conversions) > 0 THEN SUM(pm.costs) / SUM(pm.conversions) ELSE 0 END AS avg_cost_per_conversion
                FROM performanceMetrics pm
                JOIN datasources ds ON pm.data_source_id = ds.id
                JOIN campaigns c ON pm.campaign_id = c.id
                WHERE pm.date BETWEEN %s AND %s
                GROUP BY ds.source_name, c.campaign_name
                ORDER BY total_costs DESC;
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()

    return jsonify(
        [
            {
                "traffic_source": r[0],
                "campaign_name": r[1],
                "costs": float(r[2]),
                "impressions": r[3],
                "clicks": r[4],
                "cost_per_click": float(r[5]),
                "sessions": r[6],
                "cost_per_session": float(r[7]),
                "conversions": r[8],
                "cost_per_conversion": float(r[9]),
            }
            for r in rows
        ]
    )
