"""
Authorization flaws for AppSec Reviewer evaluation.
"""

from fastapi import FastAPI

app = FastAPI()
db = {}  # in-memory store


@app.get("/api/v1/reports/{report_id}")
def get_report(report_id: int, user_id: int = 0):
    """
    KD-AUTH-001: BOLA — report fetched before ownership check.
    Attacker can enumerate report IDs and read any report.
    """
    report = db.get(report_id)
    if not report:
        return {"error": "not found"}
    # Ownership check AFTER data retrieval — too late
    if report["owner_id"] != user_id:
        return {"error": "forbidden"}
    return report


@app.delete("/api/v1/admin/reports/{report_id}")
def admin_delete_report(report_id: int, role: str = "user"):
    """
    KD-AUTH-002: Missing function-level auth check.
    'role' param comes from request — attacker can set role=admin.
    """
    # role should be extracted from verified JWT, not from request params
    if role != "admin":
        return {"error": "forbidden"}
    del db[report_id]
    return {"deleted": report_id}


@app.get("/api/v1/export")
def export_all_data(user_id: int = 0):
    """
    KD-AUTH-003: Bulk data export with no rate limiting or ownership scoping.
    Returns all records regardless of who is asking.
    """
    return list(db.values())
