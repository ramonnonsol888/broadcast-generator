import streamlit as st
from datetime import datetime, timedelta, date, time
from html import escape
import base64
import sqlite3
import json
from pathlib import Path

st.set_page_config(
    page_title="IT Broadcast Notification Generator",
    page_icon="📢",
    layout="wide",
)

LOCAL_BLUE = "#8EAADB"
ISP_GREEN = "#0B8F2F"
DD_YELLOW = "#FFC000"


# =========================================================
# HELPERS
# =========================================================

def format_time(value):
    return value.strftime("%I:%M%p").lstrip("0") if value else ""


def format_date(value):
    return value.strftime("%d-%B %Y") if value else ""


def calculate_duration(start_time, end_time):
    if not start_time or not end_time:
        return ""

    start_dt = datetime.combine(datetime.today(), start_time)
    end_dt = datetime.combine(datetime.today(), end_time)

    if end_dt < start_dt:
        end_dt += timedelta(days=1)

    total_minutes = int((end_dt - start_dt).total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d} hour(s) and {minutes:02d} minute(s)"


def uploaded_image_html(uploaded_file, max_width=420):
    if uploaded_file is None:
        return ""

    mime = uploaded_file.type or "image/png"
    data = base64.b64encode(uploaded_file.getvalue()).decode("ascii")
    return (
        f'<img src="data:{mime};base64,{data}" '
        f'style="max-width:{max_width}px;max-height:210px;'
        f'object-fit:contain;display:block;margin-top:6px;">'
    )


def clear_form():
    """Immediately clear all editable fields and preview state."""
    keys = [
        # Local
        "local_ticket", "local_summary", "local_activity", "local_objective",
        "local_date", "local_start", "local_end", "local_add_second",
        "local_date2", "local_start2", "local_end2", "local_affected",
        "local_impact", "local_workaround",
        "local_show_summary", "local_show_activity", "local_show_objective",
        "local_show_schedule", "local_show_duration", "local_show_affected",
        "local_show_impact", "local_show_workaround",

        # ISP
        "isp_ticket", "isp_activity", "isp_summary", "isp_objective",
        "isp_date1", "isp_start1", "isp_end1", "isp_add_second",
        "isp_date2", "isp_start2", "isp_end2",
        "isp_down_date1", "isp_down_start1", "isp_down_end1",
        "isp_down_date2", "isp_down_start2", "isp_down_end2",
        "isp_impact", "isp_workaround",
        "isp_show_activity", "isp_show_summary", "isp_show_objective",
        "isp_show_schedule", "isp_show_duration", "isp_show_downtime",
        "isp_show_impact", "isp_show_workaround",

        # Global
        "global_ticket", "global_activity", "global_summary", "global_objective",
        "global_ph_date", "global_ph_start", "global_ph_end",
        "global_sl_date", "global_sl_start", "global_sl_end",
        "global_impact", "global_workaround",
        "global_show_activity", "global_show_summary", "global_show_objective",
        "global_show_schedule", "global_show_duration",
        "global_show_impact", "global_show_workaround",

        # Emergency
        "emergency_ticket", "emergency_activity", "emergency_summary",
        "emergency_objective", "emergency_date", "emergency_start",
        "emergency_end", "emergency_downtime", "emergency_impact",
        "emergency_workaround",
        "emergency_show_activity", "emergency_show_summary",
        "emergency_show_objective", "emergency_show_schedule",
        "emergency_show_duration", "emergency_show_downtime",
        "emergency_show_impact", "emergency_show_workaround",

        # DD Approval
        "dd_ticket", "dd_requestor", "dd_background", "dd_objective",
        "dd_scope", "dd_impact", "dd_duration", "dd_gict_text",
        "dd_other_url", "dd_other_users", "dd_other_hardware",
        "dd_line_manager_text", "dd_gict_image", "dd_manager_image",
        "dd_show_requestor", "dd_show_background", "dd_show_objective",
        "dd_show_scope", "dd_show_impact", "dd_show_duration",
        "dd_show_gict", "dd_show_other", "dd_show_manager",
        "incident_ticket",
        "incident_summary",
        "incident_date",
        "incident_time",
        "incident_impact",
        "incident_background",
        "incident_workaround",
        "incident_update",
        "incident_root_cause",
        "incident_show_workaround",
        "incident_show_update",
        "incident_show_root_cause",
        "local_timezone",
        "incident_resolved",
        "incident_resolved_time",
        "isp_timezone",
        "global_timezone_1",
        "global_timezone_2",
        "emergency_timezone",
        "global_incident_ticket",
        "global_incident_summary",
        "global_incident_date",
        "global_incident_time",
        "global_incident_resolved",
        "global_incident_resolved_time",
        "global_incident_impact",
        "global_incident_background",
        "global_incident_workaround",
        "global_incident_update",
        "global_incident_root_cause",
        "global_incident_show_workaround",
        "global_incident_show_update",
        "global_incident_show_root_cause",

        # Bulletin Advisory
        "bulletin_greeting", "bulletin_content", "bulletin_closing",
        "bulletin_regards", "bulletin_team_1", "bulletin_team_2",
    ]

    for key in keys:
        st.session_state.pop(key, None)

    st.session_state["blank_start"] = True
    st.session_state["form_cleared"] = True
    st.session_state["repository_loaded_id"] = None
    st.session_state["last_html"] = ""
    st.session_state["last_filename"] = ""
    st.session_state["last_preview_height"] = 600
    st.session_state["preview_only"] = False

# =========================================================
# BROADCAST REPOSITORY
# =========================================================

DB_PATH = Path(__file__).with_name("broadcast_repository.db")

REPOSITORY_KEYS = [
    # Local
    "local_ticket", "local_summary", "local_activity", "local_objective",
    "local_date", "local_start", "local_end", "local_add_second",
    "local_date2", "local_start2", "local_end2", "local_affected",
    "local_impact", "local_workaround",
    "local_show_summary", "local_show_activity", "local_show_objective",
    "local_show_schedule", "local_show_duration", "local_show_affected",
    "local_show_impact", "local_show_workaround",

    # ISP
    "isp_ticket", "isp_activity", "isp_summary", "isp_objective",
    "isp_date1", "isp_start1", "isp_end1", "isp_add_second",
    "isp_date2", "isp_start2", "isp_end2",
    "isp_down_date1", "isp_down_start1", "isp_down_end1",
    "isp_down_date2", "isp_down_start2", "isp_down_end2",
    "isp_impact", "isp_workaround",
    "isp_show_activity", "isp_show_summary", "isp_show_objective",
    "isp_show_schedule", "isp_show_duration", "isp_show_downtime",
    "isp_show_impact", "isp_show_workaround",

    # DD Approval
    "dd_ticket", "dd_requestor", "dd_background", "dd_objective",
    "dd_scope", "dd_impact", "dd_duration", "dd_gict_text",
    "dd_other_url", "dd_other_users", "dd_other_hardware",
    "dd_line_manager_text",
    "dd_show_requestor", "dd_show_background", "dd_show_objective",
    "dd_show_scope", "dd_show_impact", "dd_show_duration",
    "dd_show_gict", "dd_show_other", "dd_show_manager",

    "global_ticket",
    "global_activity",
    "global_summary",
    "global_objective",
    "global_ph_date",
    "global_ph_start",
    "global_ph_end",
    "global_sl_date",
    "global_sl_start",
    "global_sl_end",
    "global_impact",
    "global_workaround",
    "global_show_activity",
    "global_show_summary",
    "global_show_objective",
    "global_show_schedule",
    "global_show_duration",
    "global_show_impact",
    "global_show_workaround",
    "incident_ticket",
    "incident_summary",
    "incident_date",
    "incident_time",
    "incident_impact",
    "incident_background",
    "incident_workaround",
    "incident_update",
    "incident_root_cause",
    "incident_show_workaround",
    "incident_show_update",
    "incident_show_root_cause",
    "local_timezone",
    "incident_resolved",
    "incident_resolved_time",
    "isp_timezone",
    "global_timezone_1",
    "global_timezone_2",
    "emergency_timezone",
    "global_incident_ticket",
    "global_incident_summary",
    "global_incident_date",
    "global_incident_time",
    "global_incident_resolved",
    "global_incident_resolved_time",
    "global_incident_impact",
    "global_incident_background",
    "global_incident_workaround",
    "global_incident_update",
    "global_incident_root_cause",
    "global_incident_show_workaround",
    "global_incident_show_update",
    "global_incident_show_root_cause",

    # Bulletin Advisory
    "bulletin_greeting", "bulletin_content", "bulletin_closing",
    "bulletin_regards", "bulletin_team_1", "bulletin_team_2",
]


def init_repository():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_type TEXT NOT NULL,
                title TEXT NOT NULL,
                ticket TEXT,
                searchable_text TEXT,
                state_json TEXT NOT NULL,
                html_output TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def serialize_value(value):
    if isinstance(value, datetime):
        return {"__type__": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"__type__": "date", "value": value.isoformat()}
    if isinstance(value, time):
        return {"__type__": "time", "value": value.isoformat()}
    return value


def deserialize_value(value):
    if isinstance(value, dict) and "__type__" in value:
        value_type = value.get("__type__")
        raw = value.get("value", "")
        if value_type == "datetime":
            return datetime.fromisoformat(raw)
        if value_type == "date":
            return date.fromisoformat(raw)
        if value_type == "time":
            return time.fromisoformat(raw)
    return value


def capture_form_state(template_type):
    state = {"broadcast_template": template_type}
    for key in REPOSITORY_KEYS:
        if key in st.session_state:
            state[key] = serialize_value(st.session_state[key])
    return state


def restore_form_state(state):
    # Clear current editable form values first.
    for key in REPOSITORY_KEYS:
        if key in st.session_state:
            del st.session_state[key]

    for key, value in state.items():
        if key == "broadcast_template":
            st.session_state["broadcast_template"] = value
        elif key in REPOSITORY_KEYS:
            st.session_state[key] = deserialize_value(value)

    st.session_state["form_cleared"] = False
    st.session_state["blank_start"] = False
    st.session_state["preview_only"] = False


def repository_metadata(template_type):
    if template_type == "Local Maintenance Advisory":
        ticket = st.session_state.get("local_ticket", "")
        title = st.session_state.get("local_summary", "") or st.session_state.get("local_activity", "")
        search_parts = [
            ticket,
            st.session_state.get("local_summary", ""),
            st.session_state.get("local_activity", ""),
            st.session_state.get("local_objective", ""),
            st.session_state.get("local_affected", ""),
            st.session_state.get("local_impact", ""),
            st.session_state.get("local_workaround", ""),
        ]

    elif template_type == "ISP Maintenance Advisory":
        ticket = st.session_state.get("isp_ticket", "")
        title = st.session_state.get("isp_activity", "") or st.session_state.get("isp_summary", "")
        search_parts = [
            ticket,
            st.session_state.get("isp_activity", ""),
            st.session_state.get("isp_summary", ""),
            st.session_state.get("isp_objective", ""),
            st.session_state.get("isp_impact", ""),
            st.session_state.get("isp_workaround", ""),
        ]

    elif template_type == "DD Approval Template":
        ticket = st.session_state.get("dd_ticket", "")
        title = st.session_state.get("dd_background", "") or st.session_state.get("dd_objective", "")
        search_parts = [
            ticket,
            st.session_state.get("dd_requestor", ""),
            st.session_state.get("dd_background", ""),
            st.session_state.get("dd_objective", ""),
            st.session_state.get("dd_scope", ""),
            st.session_state.get("dd_impact", ""),
            st.session_state.get("dd_other_url", ""),
            st.session_state.get("dd_other_users", ""),
        ]

    elif template_type == "Global Maintenance Advisory":
        ticket = st.session_state.get("global_ticket", "")
        title = (
            st.session_state.get("global_activity", "")
            or st.session_state.get("global_summary", "")
            or st.session_state.get("global_objective", "")
        )
        search_parts = [
            ticket,
            st.session_state.get("global_activity", ""),
            st.session_state.get("global_summary", ""),
            st.session_state.get("global_objective", ""),
            st.session_state.get("global_impact", ""),
            st.session_state.get("global_workaround", ""),
        ]

    elif template_type == "Emergency Maintenance Advisory":
        ticket = st.session_state.get("emergency_ticket", "")
        title = (
            st.session_state.get("emergency_activity", "")
            or st.session_state.get("emergency_summary", "")
            or st.session_state.get("emergency_objective", "")
        )
        search_parts = [
            ticket,
            st.session_state.get("emergency_activity", ""),
            st.session_state.get("emergency_summary", ""),
            st.session_state.get("emergency_objective", ""),
            st.session_state.get("emergency_downtime", ""),
            st.session_state.get("emergency_impact", ""),
            st.session_state.get("emergency_workaround", ""),
        ]

    elif template_type == "Incident Advisory":
        ticket = st.session_state.get("incident_ticket", "")
        title = (
            st.session_state.get("incident_summary", "")
            or st.session_state.get("incident_background", "")
        )
        search_parts = [
            ticket,
            st.session_state.get("incident_summary", ""),
            st.session_state.get("incident_impact", ""),
            st.session_state.get("incident_background", ""),
            st.session_state.get("incident_workaround", ""),
            st.session_state.get("incident_update", ""),
            st.session_state.get("incident_root_cause", ""),
        ]

    elif template_type == "Bulletin Advisory":
        ticket = ""
        title = st.session_state.get("bulletin_content", "") or "Bulletin Advisory"
        search_parts = [
            st.session_state.get("bulletin_greeting", ""),
            st.session_state.get("bulletin_content", ""),
            st.session_state.get("bulletin_closing", ""),
            st.session_state.get("bulletin_team_1", ""),
            st.session_state.get("bulletin_team_2", ""),
        ]

    else:
        ticket = st.session_state.get("global_incident_ticket", "")
        title = (
            st.session_state.get("global_incident_summary", "")
            or st.session_state.get("global_incident_background", "")
        )
        search_parts = [
            ticket,
            st.session_state.get("global_incident_summary", ""),
            st.session_state.get("global_incident_impact", ""),
            st.session_state.get("global_incident_background", ""),
            st.session_state.get("global_incident_workaround", ""),
            st.session_state.get("global_incident_update", ""),
            st.session_state.get("global_incident_root_cause", ""),
        ]

    title = title.strip() or ticket.strip() or template_type
    searchable = " ".join(str(x) for x in search_parts if x).strip()
    return title, ticket.strip(), searchable


def save_repository_entry(template_type, html_output, record_id=None):
    state = capture_form_state(template_type)
    title, ticket, searchable = repository_metadata(template_type)
    now = datetime.now().isoformat(timespec="seconds")
    payload = json.dumps(state, ensure_ascii=False)

    with sqlite3.connect(DB_PATH) as conn:
        if record_id:
            conn.execute(
                """
                UPDATE broadcasts
                SET template_type=?, title=?, ticket=?, searchable_text=?,
                    state_json=?, html_output=?, updated_at=?
                WHERE id=?
                """,
                (
                    template_type, title, ticket, searchable,
                    payload, html_output, now, record_id,
                ),
            )
        else:
            cursor = conn.execute(
                """
                INSERT INTO broadcasts
                (template_type, title, ticket, searchable_text,
                 state_json, html_output, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    template_type, title, ticket, searchable,
                    payload, html_output, now, now,
                ),
            )
            record_id = cursor.lastrowid
        conn.commit()

    st.session_state["repository_loaded_id"] = record_id
    st.session_state["repository_message"] = (
        "Repository entry updated."
        if record_id and st.session_state.get("_repo_was_update")
        else "Broadcast saved to repository."
    )
    st.session_state["_repo_was_update"] = False


def search_repository(query="", template_filter="All"):
    sql = """
        SELECT id, template_type, title, ticket, created_at, updated_at
        FROM broadcasts
        WHERE 1=1
    """
    params = []

    if template_filter != "All":
        sql += " AND template_type = ?"
        params.append(template_filter)

    if query.strip():
        q = f"%{query.strip()}%"
        sql += """
            AND (
                title LIKE ? OR
                ticket LIKE ? OR
                searchable_text LIKE ?
            )
        """
        params.extend([q, q, q])

    sql += " ORDER BY updated_at DESC, id DESC LIMIT 50"

    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(sql, params).fetchall()


def get_repository_entry(record_id):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT state_json FROM broadcasts WHERE id = ?",
            (record_id,),
        ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def load_repository_entry(record_id, duplicate=False):
    state = get_repository_entry(record_id)
    if not state:
        st.session_state["repository_message"] = "Repository entry was not found."
        return

    restore_form_state(state)
    st.session_state["repository_loaded_id"] = None if duplicate else record_id
    st.session_state["repository_message"] = (
        "Loaded as a new copy. Edit it and save when ready."
        if duplicate
        else "Previous broadcast loaded into the editor."
    )


def delete_repository_entry(record_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM broadcasts WHERE id = ?", (record_id,))
        conn.commit()

    if st.session_state.get("repository_loaded_id") == record_id:
        st.session_state["repository_loaded_id"] = None

    st.session_state["repository_message"] = "Repository entry deleted."


init_repository()


# =========================================================
# LOCAL / ISP SHARED TEMPLATE CSS
# =========================================================

def maintenance_css(theme_color):
    return f"""
<style>
html,body{{margin:0;padding:0;background:#fff}}
*{{box-sizing:border-box}}
.broadcast-wrap{{
    width:572px;
    margin:0 auto;
    background:#fff;
    border:1px solid #000;
}}
.broadcast-table{{
    width:570px;
    border-collapse:collapse;
    table-layout:fixed;
    font-family:Arial,Helvetica,sans-serif;
    font-size:9px;
    line-height:1.08;
    color:#000;
}}
.broadcast-table col.label-col{{width:153px}}
.broadcast-table col.value-col{{width:417px}}
.broadcast-table th,.broadcast-table td{{
    border-right:1px solid #000;
    border-bottom:1px solid #000;
    vertical-align:middle;
}}
.broadcast-table tr>*:last-child{{border-right:0}}
.broadcast-table tr:last-child>*{{border-bottom:0}}
.broadcast-table .title{{
    height:52px;background:{theme_color};color:#fff;text-align:center;
    font-size:12px;font-weight:700;padding:0 8px;
}}
.broadcast-table .label{{
    width:153px;background:{theme_color};color:#fff;font-weight:700;
    padding:7px 8px;font-size:9px;line-height:10px;
}}
.broadcast-table .value{{
    width:417px;background:#fff;color:#000;padding:7px 9px;
    font-size:9px;line-height:10px;
}}
.broadcast-table .ticket td{{height:38px}}
.broadcast-table .normal td{{height:46px}}
.broadcast-table .medium td{{height:54px}}
.broadcast-table .large td{{height:62px}}
@media print{{
 body{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
 .broadcast-wrap{{margin:0}}
 @page{{margin:0}}
}}
</style>
"""


def make_row(label, value, row_class="normal"):
    return (
        f'<tr class="{row_class}">'
        f'<td class="label">{label}</td>'
        f'<td class="value">{value}</td>'
        f'</tr>'
    )


def local_html(ticket, summary, activity, objective,
               maintenance_date, start_time, end_time,
               add_second, maintenance_date2, start_time2, end_time2,
               timezone_label,
               affected_service, impact, workaround, options):

    duration1 = calculate_duration(start_time, end_time)
    duration2 = calculate_duration(start_time2, end_time2) if add_second else ""

    schedule_lines = []
    if add_second:
        if maintenance_date and start_time and end_time:
            schedule_lines.append(
                f"1st Maintenance: {format_date(maintenance_date)} from "
                f"{format_time(start_time)} to {format_time(end_time)} "
                f"({timezone_label})"
            )
        if maintenance_date2 and start_time2 and end_time2:
            schedule_lines.append(
                f"2nd Maintenance: {format_date(maintenance_date2)} from "
                f"{format_time(start_time2)} to {format_time(end_time2)} "
                f"({timezone_label})"
            )
    elif maintenance_date and start_time and end_time:
        schedule_lines.append(
            f"{format_date(maintenance_date)} from "
            f"{format_time(start_time)} to {format_time(end_time)} "
            f"({timezone_label})"
        )

    duration_lines = []
    if add_second:
        if duration1:
            duration_lines.append(f"<b>1st Maintenance:</b>&nbsp;&nbsp;{escape(duration1)}")
        if duration2:
            duration_lines.append(f"<b>2nd Maintenance:</b>&nbsp;&nbsp;{escape(duration2)}")
    elif duration1:
        duration_lines.append(escape(duration1))

    rows = [make_row("Ticket:", escape(ticket), "ticket")]

    if options["summary"]:
        rows.append(make_row("Summary:", escape(summary), "normal"))
    if options["activity"]:
        rows.append(make_row("Activity:", escape(activity), "medium"))
    if options["objective"]:
        rows.append(make_row("Objective:", escape(objective), "medium"))
    if options["schedule"]:
        rows.append(
            make_row(
                "Scheduled Maintenance Date /<br>Time:",
                "<br>".join(schedule_lines),
                "medium" if add_second else "normal"
            )
        )
    if options["duration"]:
        rows.append(
            make_row(
                "Duration:",
                "<br>".join(duration_lines),
                "normal" if add_second else "ticket"
            )
        )
    if options["affected"]:
        rows.append(make_row("Affected Service:", escape(affected_service), "normal"))
    if options["impact"]:
        rows.append(make_row("Service / Module Impact:", escape(impact), "medium"))
    if options["workaround"]:
        rows.append(make_row("Workaround:", escape(workaround), "normal"))

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Local Maintenance Advisory</title>{maintenance_css(LOCAL_BLUE)}</head>
<body><div class="broadcast-wrap"><table class="broadcast-table">
<colgroup><col class="label-col"><col class="value-col"></colgroup>
<tr><th colspan="2" class="title">Local Maintenance Advisory</th></tr>
{''.join(rows)}
</table></div></body></html>"""


def isp_html(ticket, activity, summary, objective, date1, start1, end1,
             add_second, date2, start2, end2,
             down_date1, down_start1, down_end1,
             down_date2, down_start2, down_end2,
             timezone_label,
             impact, workaround, options):

    duration1 = calculate_duration(start1, end1)
    duration2 = calculate_duration(start2, end2) if add_second else ""

    schedules = []
    if add_second:
        if date1 and start1 and end1:
            schedules.append(
                f"1st Maintenance: {format_date(date1)} from "
                f"{format_time(start1)} – {format_time(end1)} ({timezone_label})"
            )
        if date2 and start2 and end2:
            schedules.append(
                f"2nd Maintenance: {format_date(date2)} from "
                f"{format_time(start2)} – {format_time(end2)} ({timezone_label})"
            )
    elif date1 and start1 and end1:
        schedules.append(
            f"{format_date(date1)} from "
            f"{format_time(start1)} – {format_time(end1)} ({timezone_label})"
        )

    durations = []
    if add_second:
        if duration1:
            durations.append(f"<b>1st Maintenance:</b>&nbsp;&nbsp;{escape(duration1)}")
        if duration2:
            durations.append(f"<b>2nd Maintenance:</b>&nbsp;&nbsp;{escape(duration2)}")
    elif duration1:
        durations.append(escape(duration1))

    downtime = []
    if add_second:
        if down_date1 and down_start1 and down_end1:
            downtime.append(
                f"1st Maintenance: {format_date(down_date1)} from "
                f"{format_time(down_start1)} – {format_time(down_end1)} ({timezone_label})"
            )
        if down_date2 and down_start2 and down_end2:
            downtime.append(
                f"2nd Maintenance: {format_date(down_date2)} from "
                f"{format_time(down_start2)} – {format_time(down_end2)} ({timezone_label})"
            )
    elif down_date1 and down_start1 and down_end1:
        downtime.append(
            f"{format_date(down_date1)} from "
            f"{format_time(down_start1)} – {format_time(down_end1)} ({timezone_label})"
        )

    rows = [make_row("For Ticket Number:", escape(ticket), "ticket")]

    if options["activity"]:
        rows.append(make_row("Activity Name:", escape(activity), "normal"))
    if options["summary"]:
        rows.append(make_row("Summary:", escape(summary), "normal"))
    if options["objective"]:
        rows.append(make_row("Objective:", escape(objective), "medium"))
    if options["schedule"]:
        rows.append(make_row("Scheduled Maintenance Date / Time:", "<br>".join(schedules), "medium"))
    if options["duration"]:
        rows.append(make_row("Duration:", "<br>".join(durations), "normal"))
    if options["downtime"]:
        rows.append(make_row("Scheduled Downtime Date / Time:", "<br>".join(downtime), "medium"))
    if options["impact"]:
        rows.append(make_row("Service Module Impact:", escape(impact), "normal"))
    if options["workaround"]:
        rows.append(make_row("Workaround:", escape(workaround), "medium"))

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>ISP Maintenance Advisory</title>{maintenance_css(ISP_GREEN)}</head>
<body><div class="broadcast-wrap"><table class="broadcast-table">
<colgroup><col class="label-col"><col class="value-col"></colgroup>
<tr><th colspan="2" class="title">ISP Maintenance Advisory</th></tr>
{''.join(rows)}
</table></div></body></html>"""



# =========================================================
# GLOBAL MAINTENANCE TEMPLATE
# =========================================================

GLOBAL_PEACH = "#F4C7A8"

def global_html(
    ticket,
    activity,
    summary,
    objective,
    ph_date,
    ph_start,
    ph_end,
    timezone_1,
    sl_date,
    sl_start,
    sl_end,
    timezone_2,
    impact,
    workaround,
    options,
):
    # Duration is calculated from the PH schedule if available.
    duration = calculate_duration(ph_start, ph_end)

    schedule_lines = []
    if ph_date and ph_start and ph_end:
        schedule_lines.append(
            f"{format_date(ph_date)} {format_time(ph_start)} to "
            f"{format_time(ph_end)} ({timezone_1})"
        )
    if sl_date and sl_start and sl_end:
        schedule_lines.append(
            f"{format_date(sl_date)} {format_time(sl_start)} to "
            f"{format_time(sl_end)} ({timezone_2})"
        )

    rows = [
        make_row("Ticket No.", f"Ticket No. {escape(ticket)}", "ticket")
    ]

    if options["activity"]:
        rows.append(make_row("Activity Name:", escape(activity), "normal"))

    if options["summary"]:
        rows.append(make_row("Summary:", escape(summary), "normal"))

    if options["objective"]:
        rows.append(make_row("Objective:", escape(objective), "normal"))

    if options["schedule"]:
        rows.append(
            make_row(
                "Scheduled Maintenance Date / Time:",
                "<br>".join(escape(x) for x in schedule_lines),
                "medium",
            )
        )

    if options["duration"]:
        rows.append(make_row("Duration:", escape(duration), "ticket"))

    if options["impact"]:
        rows.append(make_row("Service / Module Impact:", escape(impact), "medium"))

    if options["workaround"]:
        rows.append(make_row("Workaround:", escape(workaround), "normal"))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Global Maintenance Advisory</title>
{maintenance_css(GLOBAL_PEACH)}
<style>
.broadcast-table .title {{
    color:#000000;
}}
.broadcast-table .label {{
    color:#000000;
}}
</style>
</head>
<body>
<div class="broadcast-wrap">
<table class="broadcast-table">
<colgroup><col class="label-col"><col class="value-col"></colgroup>
<tr><th colspan="2" class="title">Global Maintenance Advisory</th></tr>
{''.join(rows)}
</table>
</div>
</body>
</html>"""



# =========================================================
# EMERGENCY MAINTENANCE TEMPLATE
# =========================================================

EMERGENCY_RED = "#CF2417"

def emergency_html(
    ticket,
    activity,
    summary,
    objective,
    maintenance_date,
    start_time,
    end_time,
    timezone_label,
    downtime,
    impact,
    workaround,
    options,
):
    duration = calculate_duration(start_time, end_time)

    schedule = ""
    if maintenance_date and start_time and end_time:
        schedule = (
            f"{format_date(maintenance_date)}, from "
            f"{format_time(start_time)} to {format_time(end_time)} "
            f"({timezone_label})"
        )

    rows = [
        make_row("Ticket No.:", escape(ticket), "ticket")
    ]

    if options["activity"]:
        rows.append(make_row("Activity Name:", escape(activity), "normal"))

    if options["summary"]:
        rows.append(make_row("Summary:", escape(summary), "medium"))

    if options["objective"]:
        rows.append(make_row("Objective:", escape(objective), "medium"))

    if options["schedule"]:
        rows.append(
            make_row(
                "Scheduled Maintenance Date / Time:",
                escape(schedule),
                "normal",
            )
        )

    if options["duration"]:
        rows.append(make_row("Duration:", escape(duration), "ticket"))

    if options["downtime"]:
        rows.append(
            make_row(
                "Scheduled Downtime Date / Time:",
                escape(downtime),
                "normal",
            )
        )

    if options["impact"]:
        rows.append(
            make_row(
                "Service / Module Impact:",
                escape(impact),
                "normal",
            )
        )

    if options["workaround"]:
        rows.append(
            make_row(
                "Workaround:",
                escape(workaround),
                "normal",
            )
        )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Emergency Maintenance Advisory</title>
{maintenance_css(EMERGENCY_RED)}
<style>
.broadcast-table .title {{
    color:#FFFFFF;
}}
.broadcast-table .label {{
    color:#FFFFFF;
}}
</style>
</head>
<body>
<div class="broadcast-wrap">
<table class="broadcast-table">
<colgroup><col class="label-col"><col class="value-col"></colgroup>
<tr><th colspan="2" class="title">Emergency Maintenance Advisory</th></tr>
{''.join(rows)}
</table>
</div>
</body>
</html>"""



# =========================================================
# INCIDENT ADVISORY TEMPLATE
# =========================================================

INCIDENT_RED = "#CF2417"

def incident_html(
    ticket,
    summary,
    incident_date,
    incident_time,
    incident_resolved,
    incident_resolved_time,
    impact,
    background,
    workaround,
    update,
    root_cause,
    show_workaround=True,
    show_update=True,
    show_root_cause=True,
):
    incident_dt = ""

    if incident_date:
        # Example: August 13, 2026
        incident_date_text = incident_date.strftime("%B %d, %Y")
    else:
        incident_date_text = ""

    if incident_resolved:
        if incident_date_text and incident_time and incident_resolved_time:
            incident_dt = (
                f"{incident_date_text}, {format_time(incident_time)} – "
                f"{format_time(incident_resolved_time)} (SL Time) - Resolved"
            )
        elif incident_date_text and incident_time:
            incident_dt = (
                f"{incident_date_text}, {format_time(incident_time)} "
                f"(SL Time) - Resolved"
            )
        elif incident_date_text:
            incident_dt = f"{incident_date_text} (SL Time) - Resolved"
    else:
        if incident_date_text and incident_time:
            incident_dt = (
                f"{incident_date_text}, {format_time(incident_time)} "
                f"(SL Time) – Ongoing"
            )
        elif incident_date_text:
            incident_dt = f"{incident_date_text} (SL Time) – Ongoing"

    rows = [
        make_row("Ticket No.:", escape(ticket), "ticket"),
        make_row("Summary:", escape(summary), "normal"),
        make_row("Date / Time of Incident:", escape(incident_dt), "normal"),
        make_row("Service / Module Impact:", escape(impact), "normal"),
        make_row("Incident Background:", escape(background), "medium"),
    ]

    if show_workaround:
        rows.append(make_row("Workaround:", escape(workaround), "normal"))
    if show_update:
        rows.append(make_row("Update:", escape(update), "normal"))
    if show_root_cause:
        rows.append(make_row("Root Cause:", escape(root_cause), "normal"))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Incident Advisory</title>
{maintenance_css(INCIDENT_RED)}
<style>
.broadcast-table .title {{ color:#FFFFFF; }}
.broadcast-table .label {{ color:#FFFFFF; }}
</style>
</head>
<body>
<div class="broadcast-wrap">
<table class="broadcast-table">
<colgroup><col class="label-col"><col class="value-col"></colgroup>
<tr><th colspan="2" class="title">Incident Advisory</th></tr>
{''.join(rows)}
</table>
</div>
</body>
</html>"""



# =========================================================
# GLOBAL INCIDENT BROADCAST NOTIFICATION
# =========================================================

GLOBAL_INCIDENT_RED = "#CF2417"

def global_incident_html(
    ticket,
    summary,
    incident_date,
    incident_time,
    incident_resolved,
    incident_resolved_time,
    impact,
    background,
    workaround,
    update,
    root_cause,
    show_workaround=True,
    show_update=True,
    show_root_cause=True,
):
    incident_dt = ""

    if incident_date:
        incident_date_text = incident_date.strftime("%B %d, %Y")
    else:
        incident_date_text = ""

    if incident_resolved:
        if incident_date_text and incident_time and incident_resolved_time:
            incident_dt = (
                f"{incident_date_text}, from {format_time(incident_time)} "
                f"to {format_time(incident_resolved_time)} "
                f"(GMT +5:30 SL Time) – Resolved"
            )
        elif incident_date_text and incident_time:
            incident_dt = (
                f"{incident_date_text}, from {format_time(incident_time)} "
                f"(GMT +5:30 SL Time) – Resolved"
            )
        elif incident_date_text:
            incident_dt = f"{incident_date_text} (GMT +5:30 SL Time) – Resolved"
    else:
        if incident_date_text and incident_time:
            incident_dt = (
                f"{incident_date_text}, from {format_time(incident_time)} "
                f"(GMT +5:30 SL Time) – Ongoing"
            )
        elif incident_date_text:
            incident_dt = f"{incident_date_text} (GMT +5:30 SL Time) – Ongoing"

    rows = [
        make_row("Ticket No:", escape(ticket), "ticket"),
        make_row("Summary:", escape(summary), "normal"),
        make_row("Date/Time of Incident:", escape(incident_dt), "normal"),
        make_row("Service / Module Impact:", escape(impact), "normal"),
        make_row("Incident Background:", escape(background), "medium"),
    ]

    if show_workaround:
        rows.append(make_row("Workaround:", escape(workaround), "normal"))

    if show_update:
        rows.append(make_row("Update:", escape(update), "medium"))

    if show_root_cause:
        rows.append(make_row("Root Cause:", escape(root_cause), "normal"))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Global Incident Broadcast Notification</title>
{maintenance_css(GLOBAL_INCIDENT_RED)}
<style>
.broadcast-table .title {{
    color:#FFFFFF;
}}
.broadcast-table .label {{
    color:#FFFFFF;
}}
</style>
</head>
<body>
<div class="broadcast-wrap">
<table class="broadcast-table">
<colgroup><col class="label-col"><col class="value-col"></colgroup>
<tr>
    <th colspan="2" class="title">Global Incident Broadcast Notification</th>
</tr>
{''.join(rows)}
</table>
</div>
</body>
</html>"""


# =========================================================
# DD APPROVAL TEMPLATE
# =========================================================

def dd_html(ticket, requestor, background, objective, scope, impact, duration,
            gict_text, gict_image, other_url, other_users, other_hardware,
            manager_text, manager_image, options):

    def row(label, value, row_class="dd-normal"):
        return (
            f'<tr class="{row_class}">'
            f'<td class="dd-label">{label}</td>'
            f'<td class="dd-value">{value}</td>'
            f'</tr>'
        )

    rows = [row("Ticket Reference Number :", escape(ticket), "dd-normal")]

    if options["requestor"]:
        rows.append(row("Requestor :", escape(requestor)))
    if options["background"]:
        rows.append(row("Background :", escape(background), "dd-medium"))
    if options["objective"]:
        rows.append(row("Objective :", escape(objective), "dd-medium"))
    if options["scope"]:
        rows.append(row("Scope :", escape(scope)))
    if options["impact"]:
        rows.append(row("Service / Module Impact :", escape(impact)))
    if options["duration"]:
        rows.append(row("Duration :", escape(duration)))

    if options["gict"]:
        content = escape(gict_text).replace("\n", "<br>")
        image_html = uploaded_image_html(gict_image, 430)
        if image_html:
            content += image_html
        rows.append(row("GICT Clearance :", content, "dd-clearance"))

    if options["other"]:
        details = []
        if other_url.strip():
            safe_url = escape(other_url)
            details.append(f"<b>URL:</b> {safe_url}")
        if other_users.strip():
            details.append(f"<b>Users:</b> {escape(other_users)}")
        if other_hardware.strip():
            details.append(f"<b>Hardware:</b> {escape(other_hardware)}")
        rows.append(
            row(
                "Other Details :<br><br>[URL / Application /<br>Hardware]",
                "<br>".join(details),
                "dd-other",
            )
        )

    if options["manager"]:
        content = escape(manager_text).replace("\n", "<br>")
        image_html = uploaded_image_html(manager_image, 430)
        if image_html:
            content += image_html
        rows.append(row("Line Manager Approval:", content, "dd-manager"))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>DD Approval Template</title>
<style>
html,body{{margin:0;padding:0;background:#fff}}
*{{box-sizing:border-box}}
.dd-wrap{{
    width:604px;
    margin:0 auto;
    padding:0;
    position:relative;
    background:#fff;

    /* guaranteed outer border */
    outline:1px solid #000000;
    outline-offset:-1px;
}}

.dd-wrap::after{{
    content:"";
    position:absolute;
    top:0;
    left:0;
    width:604px;
    height:100%;
    border:1px solid #000000;
    box-sizing:border-box;
    pointer-events:none;
    z-index:10;
}}
.dd-table{{
    width:602px;
    border-collapse:collapse;
    table-layout:fixed;
    border:1px solid #000000;
    font-family:Arial,Helvetica,sans-serif;
    font-size:9px;
    line-height:1.15;
    color:#000;
}}
.dd-table col.dd-label-col{{width:130px}}
.dd-table col.dd-value-col{{width:472px}}
.dd-table th,.dd-table td{{
    border-right:1px solid #000000;
    border-bottom:1px solid #000000;
    vertical-align:middle;
}}
.dd-table tr>*:last-child{{border-right:1px solid #000000}}
.dd-table tr:last-child>*{{border-bottom:1px solid #000000}}
.dd-title{{
    height:52px;
    background:{DD_YELLOW};
    text-align:center;
    font-weight:700;
    padding:0 8px;
}}
.dd-label{{
    width:130px;
    background:{DD_YELLOW};
    font-weight:700;
    padding:6px 5px;
}}
.dd-value{{
    width:472px;
    background:#fff;
    padding:7px 7px;
}}
.dd-normal td{{height:34px}}
.dd-medium td{{height:38px}}
.dd-clearance td{{height:235px;vertical-align:top;padding-top:12px}}
.dd-clearance .dd-label{{vertical-align:middle}}
.dd-other td{{height:67px}}
.dd-manager td{{height:145px;vertical-align:top;padding-top:12px}}
.dd-manager .dd-label{{vertical-align:middle}}
a{{color:#0563C1}}
@media print{{
 body{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
 .dd-wrap{{margin:0}}
 @page{{margin:0}}
}}
</style>
</head>
<body>
<div class="dd-wrap">
<table class="dd-table">
<colgroup><col class="dd-label-col"><col class="dd-value-col"></colgroup>
<tr><th colspan="2" class="dd-title">Approval Request Details</th></tr>
{''.join(rows)}
</table>
</div>
</body>
</html>"""



def bulletin_html(greeting, content, closing, regards, team_1, team_2):
    def text(value):
        return escape(value or "").replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Bulletin Advisory</title>
<style>
html,body{{margin:0;padding:0;background:#fff}}
*{{box-sizing:border-box}}
.announcement{{
    width:572px;margin:0 auto;padding:10px 8px 20px;
    border:3px double #4F7FD8;background:#fff;color:#111;
    font-family:Arial,Helvetica,sans-serif;font-size:9px;line-height:1.35;
}}
.brand{{font-size:29px;line-height:1;color:#2F5597;margin:8px 0 18px}}
p{{margin:0 0 10px}}
.strong{{font-weight:700}}
.content{{white-space:normal;margin-bottom:12px}}
.signature{{margin-top:15px}}
@media print{{
 body{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
 .announcement{{margin:0}}
 @page{{margin:0}}
}}
</style>
</head>
<body>
<div class="announcement">
  <div class="brand">GICT</div>
  <p>{text(greeting)}</p>
  <div class="content">{text(content)}</div>
  <p>{text(closing)}</p>
  <div class="signature">
    <div class="strong">{text(regards)}</div>
    <div>{text(team_1)}</div>
    <div>{text(team_2)}</div>
  </div>
</div>
</body>
</html>"""


def has_meaningful_content(template_name):
    if template_name == "Local Maintenance Advisory":
        keys = [
            "local_ticket", "local_summary", "local_activity", "local_objective",
            "local_affected", "local_impact", "local_workaround",
        ]
    elif template_name == "ISP Maintenance Advisory":
        keys = [
            "isp_ticket", "isp_activity", "isp_summary", "isp_objective",
            "isp_impact", "isp_workaround",
        ]
    elif template_name == "Global Maintenance Advisory":
        keys = [
            "global_ticket", "global_activity", "global_summary",
            "global_objective", "global_impact", "global_workaround",
        ]
    elif template_name == "Emergency Maintenance Advisory":
        keys = [
            "emergency_ticket", "emergency_activity", "emergency_summary",
            "emergency_objective", "emergency_downtime",
            "emergency_impact", "emergency_workaround",
        ]
    elif template_name == "Incident Advisory":
        keys = [
            "incident_ticket", "incident_summary", "incident_impact",
            "incident_background", "incident_workaround",
            "incident_update", "incident_root_cause",
        ]
    elif template_name == "Global Incident Broadcast Notification":
        keys = [
            "global_incident_ticket", "global_incident_summary",
            "global_incident_impact", "global_incident_background",
            "global_incident_workaround", "global_incident_update",
            "global_incident_root_cause",
        ]
    elif template_name == "Bulletin Advisory":
        keys = ["bulletin_content"]
    else:
        keys = [
            "dd_ticket", "dd_requestor", "dd_background", "dd_objective",
            "dd_scope", "dd_impact", "dd_duration", "dd_gict_text",
            "dd_other_url", "dd_other_users", "dd_other_hardware",
            "dd_line_manager_text",
        ]

    return any(str(st.session_state.get(k, "") or "").strip() for k in keys)


def blank_preview_html():
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
html,body{
    margin:0;
    padding:0;
    background:#FFFFFF;
    font-family:Arial,Helvetica,sans-serif;
}
.empty-preview{
    height:180px;
    display:flex;
    align-items:center;
    justify-content:center;
    color:#94A3B8;
    font-size:13px;
    border:1px dashed #CBD5E1;
    background:#FFFFFF;
}
</style>
</head>
<body>
<div class="empty-preview">Enter broadcast details or load a saved broadcast from the repository.</div>
</body>
</html>"""


# =========================================================
# APP STYLE
# =========================================================

st.markdown("""
<style>
html,body,[data-testid="stAppViewContainer"]{background:#F5F7FB}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1450px;padding-top:1.2rem;padding-bottom:2rem}
.app-hero{
 background:linear-gradient(135deg,#4F7FD8 0%,#315EA8 100%);
 border-radius:18px;padding:22px 26px;margin-bottom:18px;color:#fff
}
.app-hero h1{margin:0;font-size:28px}
.app-hero p{margin:7px 0 0;opacity:.9;font-size:14px}
.section-title{font-size:18px;font-weight:800;color:#172033;margin-bottom:10px}
.repo-card{
    border:1px solid #D9E0EA;
    border-radius:12px;
    padding:10px 12px;
    margin:8px 0;
    background:#FFFFFF;
}
.repo-title{font-weight:700;font-size:13px;color:#172033}
.repo-meta{font-size:11px;color:#64748B;margin-top:3px}

.stButton>button,.stDownloadButton>button{
 border-radius:10px!important;min-height:42px;font-weight:700!important
}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input{border-radius:10px!important}
</style>
""", unsafe_allow_html=True)

if "preview_only" not in st.session_state:
    st.session_state.preview_only = False

if "blank_start" not in st.session_state:
    st.session_state.blank_start = True

st.markdown("""
<div class="app-hero">
<h1>📢 IT Broadcast Notification Generator</h1>
<p>Create maintenance, incident, bulletin, and DD Approval templates.</p>
</div>
""", unsafe_allow_html=True)

template = st.selectbox(
    "Broadcast Template",
    [
        "Local Maintenance Advisory",
        "ISP Maintenance Advisory",
        "Global Maintenance Advisory",
        "Emergency Maintenance Advisory",
        "Incident Advisory",
        "Global Incident Broadcast Notification",
        "Bulletin Advisory",
        "DD Approval Template",
    ],
    key="broadcast_template",
)

if not st.session_state.preview_only:
    left, right = st.columns([0.95, 1.35], gap="large")

    with left:
        st.markdown('<div class="section-title">Enter Details</div>', unsafe_allow_html=True)
        cleared = st.session_state.get("blank_start", True)

        # =====================================================
        # LOCAL
        # =====================================================
        if template == "Local Maintenance Advisory":
            with st.expander("⚙ Optional Fields", expanded=False):
                st.caption("Uncheck any row you do not want in the output.")
                show_summary = st.checkbox("Summary", True, key="local_show_summary")
                show_activity = st.checkbox("Activity", True, key="local_show_activity")
                show_objective = st.checkbox("Objective", True, key="local_show_objective")
                show_schedule = st.checkbox("Scheduled Maintenance Date / Time", True, key="local_show_schedule")
                show_duration = st.checkbox("Duration", True, key="local_show_duration")
                show_affected = st.checkbox("Affected Service", True, key="local_show_affected")
                show_impact = st.checkbox("Service / Module Impact", True, key="local_show_impact")
                show_workaround = st.checkbox("Workaround", True, key="local_show_workaround")

            ticket = st.text_input("Ticket", "" if cleared else "GCM-10877", key="local_ticket")
            summary = st.text_area("Summary", "" if cleared else "Provisioning and Testing of New Network Backup Link", key="local_summary")
            activity = st.text_area("Activity", "" if cleared else "Provisioning and Testing of New Network Backup Link between SL Office and TW New Data Center", key="local_activity")
            objective = st.text_area("Objective", "" if cleared else "To establish a new backup connection between SL Office and TW New Data Center prior to the migration of services to the New Data Center", key="local_objective")
            st.markdown("**1st Maintenance**")
            maintenance_date = st.date_input(
                "1st Maintenance Date",
                value=None if cleared else datetime(2026,8,20).date(),
                key="local_date"
            )
            c1,c2 = st.columns(2)
            with c1:
                start_time = st.time_input(
                    "1st Start Time",
                    value=None if cleared else datetime.strptime("11:00","%H:%M").time(),
                    key="local_start"
                )
            with c2:
                end_time = st.time_input(
                    "1st End Time",
                    value=None if cleared else datetime.strptime("12:40","%H:%M").time(),
                    key="local_end"
                )

            timezone_label = st.selectbox(
                "Time Zone",
                [
                    "GMT +8 (PH Time)",
                    "GMT +5:30 (SL Time)",
                ],
                key="local_timezone",
            )

            add_second = st.checkbox(
                "➕ Add 2nd Maintenance",
                value=False,
                key="local_add_second"
            )

            if add_second:
                st.markdown("**2nd Maintenance**")
                maintenance_date2 = st.date_input(
                    "2nd Maintenance Date",
                    value=None if cleared else datetime(2026,8,21).date(),
                    key="local_date2"
                )
                c1,c2 = st.columns(2)
                with c1:
                    start_time2 = st.time_input(
                        "2nd Start Time",
                        value=None if cleared else datetime.strptime("11:00","%H:%M").time(),
                        key="local_start2"
                    )
                with c2:
                    end_time2 = st.time_input(
                        "2nd End Time",
                        value=None if cleared else datetime.strptime("12:40","%H:%M").time(),
                        key="local_end2"
                    )
            else:
                maintenance_date2 = None
                start_time2 = None
                end_time2 = None

            duration1 = calculate_duration(start_time, end_time)
            duration2 = calculate_duration(start_time2, end_time2) if add_second else ""

            if add_second:
                st.text_area(
                    "Duration",
                    value=(
                        f"1st Maintenance: {duration1}\n"
                        f"2nd Maintenance: {duration2}"
                    ),
                    disabled=True,
                    height=75
                )
            else:
                st.text_input("Duration", value=duration1, disabled=True)
            affected = st.text_input("Affected Service", "" if cleared else "No service impact is expected", key="local_affected")
            impact = st.text_area("Service / Module Impact", "" if cleared else "In worst case scenario, maximum of 3 minutes network interruption might occur during the testing", key="local_impact")
            workaround = st.text_area("Workaround", "" if cleared else "No workaround is required.", key="local_workaround")

            options = {
                "summary":show_summary,"activity":show_activity,"objective":show_objective,
                "schedule":show_schedule,"duration":show_duration,"affected":show_affected,
                "impact":show_impact,"workaround":show_workaround
            }
            html_output = local_html(
                ticket, summary, activity, objective,
                maintenance_date, start_time, end_time,
                add_second, maintenance_date2, start_time2, end_time2,
                timezone_label,
                affected, impact, workaround, options
            )
            filename = "Local_Maintenance_Advisory.html"
            preview_height = 620

        # =====================================================
        # ISP
        # =====================================================
        elif template == "ISP Maintenance Advisory":
            with st.expander("⚙ Optional Fields", expanded=False):
                st.caption("Uncheck any row you do not want in the output.")
                show_activity = st.checkbox("Activity Name", True, key="isp_show_activity")
                show_summary = st.checkbox("Summary", True, key="isp_show_summary")
                show_objective = st.checkbox("Objective", True, key="isp_show_objective")
                show_schedule = st.checkbox("Scheduled Maintenance Date / Time", True, key="isp_show_schedule")
                show_duration = st.checkbox("Duration", True, key="isp_show_duration")
                show_downtime = st.checkbox("Scheduled Downtime Date / Time", True, key="isp_show_downtime")
                show_impact = st.checkbox("Service Module Impact", True, key="isp_show_impact")
                show_workaround = st.checkbox("Workaround", True, key="isp_show_workaround")

            ticket = st.text_input("For Ticket Number", "" if cleared else "GCM-10867", key="isp_ticket")
            activity = st.text_input("Activity Name", "" if cleared else "IPLC06 (CMI) Emergency Maintenance", key="isp_activity")
            summary = st.text_input("Summary", "" if cleared else "IPLC06 Emergency Maintenance by ISP Provider", key="isp_summary")
            objective = st.text_area("Objective", "" if cleared else "To perform urgent maintenance on our IPLC06 service to ensure continued service reliability and minimize the risk of unexpected disruptions.", key="isp_objective")

            st.markdown("**1st Maintenance**")
            date1 = st.date_input("1st Maintenance Date", value=None if cleared else datetime(2026,8,12).date(), key="isp_date1")
            c1,c2 = st.columns(2)
            with c1:
                start1 = st.time_input("1st Start Time", value=None if cleared else datetime.strptime("10:00","%H:%M").time(), key="isp_start1")
            with c2:
                end1 = st.time_input("1st End Time", value=None if cleared else datetime.strptime("18:00","%H:%M").time(), key="isp_end1")

            timezone_label = st.selectbox(
                "Time Zone",
                ["GMT +8 (PH Time)", "GMT +5:30 (SL Time)"],
                key="isp_timezone",
            )

            add_second = st.checkbox("➕ Add 2nd Maintenance", False, key="isp_add_second")
            if add_second:
                date2 = st.date_input("2nd Maintenance Date", value=None if cleared else datetime(2026,8,13).date(), key="isp_date2")
                c1,c2 = st.columns(2)
                with c1:
                    start2 = st.time_input("2nd Start Time", value=None if cleared else datetime.strptime("07:30","%H:%M").time(), key="isp_start2")
                with c2:
                    end2 = st.time_input("2nd End Time", value=None if cleared else datetime.strptime("11:30","%H:%M").time(), key="isp_end2")
            else:
                date2=start2=end2=None

            st.markdown("**Scheduled Downtime**")
            down_date1 = st.date_input("1st Downtime Date", value=None if cleared else datetime(2026,8,12).date(), key="isp_down_date1")
            c1,c2 = st.columns(2)
            with c1:
                down_start1 = st.time_input("1st Downtime Start", value=None if cleared else datetime.strptime("10:00","%H:%M").time(), key="isp_down_start1")
            with c2:
                down_end1 = st.time_input("1st Downtime End", value=None if cleared else datetime.strptime("18:00","%H:%M").time(), key="isp_down_end1")
            if add_second:
                down_date2 = st.date_input("2nd Downtime Date", value=None if cleared else datetime(2026,8,13).date(), key="isp_down_date2")
                c1,c2 = st.columns(2)
                with c1:
                    down_start2 = st.time_input("2nd Downtime Start", value=None if cleared else datetime.strptime("07:30","%H:%M").time(), key="isp_down_start2")
                with c2:
                    down_end2 = st.time_input("2nd Downtime End", value=None if cleared else datetime.strptime("11:30","%H:%M").time(), key="isp_down_end2")
            else:
                down_date2=down_start2=down_end2=None

            impact = st.text_input("Service Module Impact", "" if cleared else "No service impact is expected", key="isp_impact")
            workaround = st.text_area("Workaround", "" if cleared else "Network traffic will automatically swing to alternative network paths during the maintenance.", key="isp_workaround")

            options = {
                "activity":show_activity,"summary":show_summary,"objective":show_objective,
                "schedule":show_schedule,"duration":show_duration,"downtime":show_downtime,
                "impact":show_impact,"workaround":show_workaround
            }
            html_output = isp_html(ticket,activity,summary,objective,date1,start1,end1,
                                   add_second,date2,start2,end2,down_date1,down_start1,
                                   down_end1,down_date2,down_start2,down_end2,timezone_label,
                                   impact,workaround,options)
            filename = "ISP_Maintenance_Advisory.html"
            preview_height = 620

        # =====================================================
        # GLOBAL MAINTENANCE
        # =====================================================
        elif template == "Global Maintenance Advisory":
            with st.expander("⚙ Optional Fields", expanded=False):
                st.caption("Uncheck any row you do not want in the output.")
                show_activity = st.checkbox("Activity Name", True, key="global_show_activity")
                show_summary = st.checkbox("Summary", True, key="global_show_summary")
                show_objective = st.checkbox("Objective", True, key="global_show_objective")
                show_schedule = st.checkbox("Scheduled Maintenance Date / Time", True, key="global_show_schedule")
                show_duration = st.checkbox("Duration", True, key="global_show_duration")
                show_impact = st.checkbox("Service / Module Impact", True, key="global_show_impact")
                show_workaround = st.checkbox("Workaround", True, key="global_show_workaround")

            ticket = st.text_input(
                "Ticket No.",
                "" if cleared else "GCM-10858",
                key="global_ticket",
            )

            activity = st.text_input(
                "Activity Name",
                "" if cleared else "",
                key="global_activity",
            )

            summary = st.text_area(
                "Summary",
                "" if cleared else "Zscaler Authentication Service Maintenance",
                key="global_summary",
            )

            objective = st.text_area(
                "Objective",
                "" if cleared else "To improve platform reliability and apply bug fixes",
                key="global_objective",
            )

            st.markdown("**PH Schedule**")
            ph_date = st.date_input(
                "PH Maintenance Date",
                value=None if cleared else datetime(2026,6,19).date(),
                key="global_ph_date",
            )
            c1,c2 = st.columns(2)
            with c1:
                ph_start = st.time_input(
                    "PH Start Time",
                    value=None if cleared else datetime.strptime("19:30","%H:%M").time(),
                    key="global_ph_start",
                )
            with c2:
                ph_end = st.time_input(
                    "PH End Time",
                    value=None if cleared else datetime.strptime("23:30","%H:%M").time(),
                    key="global_ph_end",
                )

            timezone_1 = st.selectbox(
                "PH Schedule Time Zone",
                ["GMT +8 (PH Time)", "GMT +5:30 (SL Time)"],
                index=0,
                key="global_timezone_1",
            )

            st.markdown("**SL Schedule**")
            sl_date = st.date_input(
                "SL Maintenance Date",
                value=None if cleared else datetime(2026,6,19).date(),
                key="global_sl_date",
            )
            c1,c2 = st.columns(2)
            with c1:
                sl_start = st.time_input(
                    "SL Start Time",
                    value=None if cleared else datetime.strptime("17:00","%H:%M").time(),
                    key="global_sl_start",
                )
            with c2:
                sl_end = st.time_input(
                    "SL End Time",
                    value=None if cleared else datetime.strptime("19:00","%H:%M").time(),
                    key="global_sl_end",
                )

            timezone_2 = st.selectbox(
                "SL Schedule Time Zone",
                ["GMT +8 (PH Time)", "GMT +5:30 (SL Time)"],
                index=1,
                key="global_timezone_2",
            )

            st.text_input(
                "Duration",
                value=calculate_duration(ph_start, ph_end),
                disabled=True,
            )

            impact = st.text_area(
                "Service / Module Impact",
                "" if cleared else (
                    "Users attempting to establish a new connection to Zscaler may be "
                    "unable to authenticate during this period. Existing authenticated "
                    "sessions will remain active and should continue to operate normally."
                ),
                height=95,
                key="global_impact",
            )

            workaround = st.text_input(
                "Workaround",
                "" if cleared else "Not Applicable",
                key="global_workaround",
            )

            options = {
                "activity": show_activity,
                "summary": show_summary,
                "objective": show_objective,
                "schedule": show_schedule,
                "duration": show_duration,
                "impact": show_impact,
                "workaround": show_workaround,
            }

            html_output = global_html(
                ticket, activity, summary, objective,
                ph_date, ph_start, ph_end, timezone_1,
                sl_date, sl_start, sl_end, timezone_2,
                impact, workaround, options
            )

            filename = "Global_Maintenance_Advisory.html"
            preview_height = 620

        # =====================================================
        # EMERGENCY MAINTENANCE
        # =====================================================
        elif template == "Emergency Maintenance Advisory":
            with st.expander("⚙ Optional Fields", expanded=False):
                st.caption("Uncheck any row you do not want in the output.")
                show_activity = st.checkbox("Activity Name", True, key="emergency_show_activity")
                show_summary = st.checkbox("Summary", True, key="emergency_show_summary")
                show_objective = st.checkbox("Objective", True, key="emergency_show_objective")
                show_schedule = st.checkbox("Scheduled Maintenance Date / Time", True, key="emergency_show_schedule")
                show_duration = st.checkbox("Duration", True, key="emergency_show_duration")
                show_downtime = st.checkbox("Scheduled Downtime Date / Time", True, key="emergency_show_downtime")
                show_impact = st.checkbox("Service / Module Impact", True, key="emergency_show_impact")
                show_workaround = st.checkbox("Workaround", True, key="emergency_show_workaround")

            ticket = st.text_input(
                "Ticket No.",
                "" if cleared else "GCM-10855",
                key="emergency_ticket",
            )

            activity = st.text_input(
                "Activity Name",
                "" if cleared else "Exchange Server Service Refresh and Restart",
                key="emergency_activity",
            )

            summary = st.text_area(
                "Summary",
                "" if cleared else (
                    "The RCBC on-premises Exchange Server is in a hung state. "
                    "A proactive restart is scheduled to refresh services and prevent potential issues."
                ),
                height=85,
                key="emergency_summary",
            )

            objective = st.text_area(
                "Objective",
                "" if cleared else (
                    "To restore the Exchange Server to a healthy operational state by restarting "
                    "the server and refreshing its services, ensuring continued email service stability "
                    "and preventing anticipated disruptions."
                ),
                height=95,
                key="emergency_objective",
            )

            maintenance_date = st.date_input(
                "Scheduled Maintenance Date",
                value=None if cleared else datetime(2026,6,15).date(),
                key="emergency_date",
            )

            c1,c2 = st.columns(2)
            with c1:
                start_time = st.time_input(
                    "Start Time",
                    value=None if cleared else datetime.strptime("12:00","%H:%M").time(),
                    key="emergency_start",
                )
            with c2:
                end_time = st.time_input(
                    "End Time",
                    value=None if cleared else datetime.strptime("13:00","%H:%M").time(),
                    key="emergency_end",
                )

            timezone_label = st.selectbox(
                "Time Zone",
                ["GMT +8 (PH Time)", "GMT +5:30 (SL Time)"],
                key="emergency_timezone",
            )

            st.text_input(
                "Duration",
                value=calculate_duration(start_time, end_time),
                disabled=True,
            )

            downtime = st.text_input(
                "Scheduled Downtime Date / Time",
                "" if cleared else "No downtime",
                key="emergency_downtime",
            )

            impact = st.text_area(
                "Service / Module Impact",
                "" if cleared else "SLAOC and IT SBK team scan to email",
                height=80,
                key="emergency_impact",
            )

            workaround = st.text_area(
                "Workaround",
                "" if cleared else "Not Applicable",
                height=75,
                key="emergency_workaround",
            )

            options = {
                "activity": show_activity,
                "summary": show_summary,
                "objective": show_objective,
                "schedule": show_schedule,
                "duration": show_duration,
                "downtime": show_downtime,
                "impact": show_impact,
                "workaround": show_workaround,
            }

            html_output = emergency_html(
                ticket,
                activity,
                summary,
                objective,
                maintenance_date,
                start_time,
                end_time,
                timezone_label,
                downtime,
                impact,
                workaround,
                options,
            )

            filename = "Emergency_Maintenance_Advisory.html"
            preview_height = 620

        # =====================================================
        # INCIDENT ADVISORY
        # =====================================================
        elif template == "Incident Advisory":
            with st.expander("⚙ Optional Fields", expanded=False):
                st.caption("Uncheck a row if the information is not available yet.")
                show_workaround = st.checkbox(
                    "Workaround",
                    value=True,
                    key="incident_show_workaround",
                )
                show_update = st.checkbox(
                    "Update",
                    value=True,
                    key="incident_show_update",
                )
                show_root_cause = st.checkbox(
                    "Root Cause",
                    value=True,
                    key="incident_show_root_cause",
                )

            ticket = st.text_input(
                "Ticket No.",
                "",
                key="incident_ticket",
            )

            summary = st.text_area(
                "Summary",
                "",
                height=72,
                key="incident_summary",
            )

            c1, c2 = st.columns(2)
            with c1:
                incident_date = st.date_input(
                    "Date of Incident",
                    value=None,
                    key="incident_date",
                )
            with c2:
                incident_time = st.time_input(
                    "Incident Start Time (SL Time)",
                    value=None,
                    key="incident_time",
                )

            incident_resolved = st.checkbox(
                "✅ Incident Resolved",
                value=False,
                key="incident_resolved",
            )

            if incident_resolved:
                incident_resolved_time = st.time_input(
                    "Resolved Time (SL Time)",
                    value=None,
                    key="incident_resolved_time",
                )
            else:
                incident_resolved_time = None

            impact = st.text_area(
                "Service / Module Impact",
                "",
                height=76,
                key="incident_impact",
            )

            background = st.text_area(
                "Incident Background",
                "",
                height=90,
                key="incident_background",
            )

            workaround = st.text_area(
                "Workaround",
                "",
                height=76,
                key="incident_workaround",
            )

            update = st.text_area(
                "Update",
                "",
                height=76,
                key="incident_update",
            )

            root_cause = st.text_area(
                "Root Cause",
                "",
                height=76,
                key="incident_root_cause",
            )

            html_output = incident_html(
                ticket=ticket,
                summary=summary,
                incident_date=incident_date,
                incident_time=incident_time,
                incident_resolved=incident_resolved,
                incident_resolved_time=incident_resolved_time,
                impact=impact,
                background=background,
                workaround=workaround,
                update=update,
                root_cause=root_cause,
                show_workaround=show_workaround,
                show_update=show_update,
                show_root_cause=show_root_cause,
            )

            filename = "Incident_Advisory.html"
            preview_height = 620

        # =====================================================
        # GLOBAL INCIDENT BROADCAST NOTIFICATION
        # =====================================================
        elif template == "Global Incident Broadcast Notification":
            with st.expander("⚙ Optional Fields", expanded=False):
                st.caption("Uncheck a row if the information is not available yet.")
                show_workaround = st.checkbox(
                    "Workaround",
                    value=True,
                    key="global_incident_show_workaround",
                )
                show_update = st.checkbox(
                    "Update",
                    value=True,
                    key="global_incident_show_update",
                )
                show_root_cause = st.checkbox(
                    "Root Cause",
                    value=True,
                    key="global_incident_show_root_cause",
                )

            ticket = st.text_input(
                "Ticket No.",
                "",
                key="global_incident_ticket",
            )

            summary = st.text_area(
                "Summary",
                "",
                height=72,
                key="global_incident_summary",
            )

            c1, c2 = st.columns(2)

            with c1:
                incident_date = st.date_input(
                    "Date of Incident",
                    value=None,
                    key="global_incident_date",
                )

            with c2:
                incident_time = st.time_input(
                    "Incident Start Time (SL Time)",
                    value=None,
                    key="global_incident_time",
                )

            incident_resolved = st.checkbox(
                "✅ Incident Resolved",
                value=False,
                key="global_incident_resolved",
            )

            if incident_resolved:
                incident_resolved_time = st.time_input(
                    "Resolved Time (SL Time)",
                    value=None,
                    key="global_incident_resolved_time",
                )
            else:
                incident_resolved_time = None

            impact = st.text_area(
                "Service / Module Impact",
                "",
                height=75,
                key="global_incident_impact",
            )

            background = st.text_area(
                "Incident Background",
                "",
                height=95,
                key="global_incident_background",
            )

            workaround = st.text_area(
                "Workaround",
                "",
                height=75,
                key="global_incident_workaround",
            )

            update = st.text_area(
                "Update",
                "",
                height=90,
                key="global_incident_update",
            )

            root_cause = st.text_area(
                "Root Cause",
                "",
                height=75,
                key="global_incident_root_cause",
            )

            html_output = global_incident_html(
                ticket=ticket,
                summary=summary,
                incident_date=incident_date,
                incident_time=incident_time,
                incident_resolved=incident_resolved,
                incident_resolved_time=incident_resolved_time,
                impact=impact,
                background=background,
                workaround=workaround,
                update=update,
                root_cause=root_cause,
                show_workaround=show_workaround,
                show_update=show_update,
                show_root_cause=show_root_cause,
            )

            filename = "Global_Incident_Broadcast_Notification.html"
            preview_height = 650

        # =====================================================
        # BULLETIN ADVISORY
        # =====================================================
        elif template == "Bulletin Advisory":
            st.caption("Create a plain, letter-style GICT bulletin using one editable content field.")

            greeting = st.text_input(
                "Greeting", "" if cleared else "Dear All,",
                placeholder="Dear All,", key="bulletin_greeting",
            )
            content = st.text_area(
                "Bulletin Content", "",
                placeholder="Enter or paste the complete bulletin message here. Use blank lines to separate paragraphs.",
                height=360, key="bulletin_content",
            )
            closing = st.text_input(
                "Closing", "", placeholder="Thank you for your cooperation.", key="bulletin_closing"
            )
            regards = st.text_input("Sign-off", "Regards,", key="bulletin_regards")
            team_1 = st.text_input("Team / Department 1", "Global Helpdesk Operations", key="bulletin_team_1")
            team_2 = st.text_input("Team / Department 2", "IT Operations", key="bulletin_team_2")

            html_output = bulletin_html(greeting, content, closing, regards, team_1, team_2)
            filename = "Bulletin_Advisory.html"
            preview_height = 740

        # =====================================================
        # DD APPROVAL
        # =====================================================
        else:
            with st.expander("⚙ Optional Fields", expanded=False):
                st.caption("Uncheck any row you do not need in the approval template.")
                show_requestor = st.checkbox("Requestor", True, key="dd_show_requestor")
                show_background = st.checkbox("Background", True, key="dd_show_background")
                show_objective = st.checkbox("Objective", True, key="dd_show_objective")
                show_scope = st.checkbox("Scope", True, key="dd_show_scope")
                show_impact = st.checkbox("Service / Module Impact", True, key="dd_show_impact")
                show_duration = st.checkbox("Duration", True, key="dd_show_duration")
                show_gict = st.checkbox("GICT Clearance", True, key="dd_show_gict")
                show_other = st.checkbox("Other Details", True, key="dd_show_other")
                show_manager = st.checkbox("Line Manager Approval", True, key="dd_show_manager")

            ticket = st.text_input("Ticket Reference Number", "" if cleared else "NEO-1575 | GSEP-5128", key="dd_ticket")
            requestor = st.text_input("Requestor", "" if cleared else "Boon Liat Tay", key="dd_requestor")
            background = st.text_area("Background", "" if cleared else "Request to access https://www.chanceliga.cz/", key="dd_background")
            objective = st.text_area("Objective", "" if cleared else "To confirm the schedule and result of a match for trading operations purposes", key="dd_objective")
            scope = st.text_input("Scope", "" if cleared else "PCBPO & GGMC | Straight Team", key="dd_scope")
            impact = st.text_input("Service / Module Impact", "" if cleared else "N/A", key="dd_impact")
            duration = st.text_input("Duration", "" if cleared else "Permanent", key="dd_duration")

            st.markdown("**GICT Clearance**")
            gict_text = st.text_area("GICT Clearance Details", "" if cleared else "Cleared\nApproved", height=90, key="dd_gict_text")
            gict_image = st.file_uploader("GICT Clearance Screenshot (optional)", type=["png","jpg","jpeg"], key="dd_gict_image")

            st.markdown("**Other Details**")
            other_url = st.text_input("URL / Application", "" if cleared else "https://www.chanceliga.cz/", key="dd_other_url")
            other_users = st.text_input("Users", "" if cleared else "SL and PH - ST users", key="dd_other_users")
            other_hardware = st.text_input("Hardware (optional)", "", key="dd_other_hardware")

            st.markdown("**Line Manager Approval**")
            manager_text = st.text_area("Line Manager Approval Details", "" if cleared else "Approved by Line Manager", height=80, key="dd_line_manager_text")
            manager_image = st.file_uploader("Line Manager Approval Screenshot (optional)", type=["png","jpg","jpeg"], key="dd_manager_image")

            options = {
                "requestor":show_requestor,"background":show_background,
                "objective":show_objective,"scope":show_scope,"impact":show_impact,
                "duration":show_duration,"gict":show_gict,"other":show_other,
                "manager":show_manager
            }

            html_output = dd_html(
                ticket,requestor,background,objective,scope,impact,duration,
                gict_text,gict_image,other_url,other_users,other_hardware,
                manager_text,manager_image,options
            )
            filename = "DD_Approval_Template.html"
            preview_height = 820

        if not has_meaningful_content(template):
            html_output = blank_preview_html()
            preview_height = 200

        b1,b2 = st.columns(2)
        with b1:
            if st.button("💾 Save to Repository", use_container_width=True):
                if has_meaningful_content(template):
                    st.session_state["_repo_was_update"] = False
                    save_repository_entry(template, html_output, record_id=None)
                    st.rerun()
                else:
                    st.warning("Enter broadcast details before saving.")
        with b2:
            loaded_id = st.session_state.get("repository_loaded_id")
            if st.button(
                "♻ Update Saved" if loaded_id else "↻ Reset Form",
                use_container_width=True,
                disabled=False,
            ):
                if loaded_id:
                    st.session_state["_repo_was_update"] = True
                    save_repository_entry(template, html_output, record_id=loaded_id)
                else:
                    clear_form()
                st.rerun()

        b3,b4 = st.columns(2)
        with b3:
            if st.button("🖥 Preview Only", use_container_width=True):
                st.session_state.preview_only = True
                st.session_state.last_html = html_output
                st.session_state.last_filename = filename
                st.session_state.last_preview_height = preview_height
                st.rerun()
        with b4:
            if st.button("🧹 Clear Form", use_container_width=True):
                clear_form()
                st.session_state["repository_loaded_id"] = None
                st.rerun()

    with right:
        st.markdown('<div class="section-title">Broadcast Preview</div>', unsafe_allow_html=True)
        st.components.v1.html(html_output, height=preview_height, scrolling=False)
        st.download_button(
            "⬇ Download Standalone Template",
            data=html_output.encode("utf-8"),
            file_name=filename,
            mime="text/html",
            use_container_width=True,
        )


    # =====================================================
    # REPOSITORY SIDEBAR
    # =====================================================
    with st.sidebar:
        st.markdown("## 📚 Broadcast Repository")
        st.caption(
            "Search previous broadcasts and load them back into the form."
        )

        repo_query = st.text_input(
            "Search",
            placeholder="Ticket, activity, summary, URL...",
            key="repository_search",
        )

        repo_filter = st.selectbox(
            "Template Type",
            [
                "All",
                "Local Maintenance Advisory",
                "ISP Maintenance Advisory",
                "Global Maintenance Advisory",
                "Emergency Maintenance Advisory",
                "Incident Advisory",
                "Global Incident Broadcast Notification",
                "Bulletin Advisory",
                "DD Approval Template",
            ],
            key="repository_filter",
        )

        results = search_repository(repo_query, repo_filter)

        if st.session_state.get("repository_message"):
            st.success(st.session_state["repository_message"])
            st.session_state["repository_message"] = ""

        if not results:
            st.info("No saved broadcasts found.")
        else:
            st.caption(f"{len(results)} result(s)")

            for rec_id, rec_template, rec_title, rec_ticket, created_at, updated_at in results:
                short_title = rec_title if len(rec_title) <= 55 else rec_title[:52] + "..."
                st.markdown(
                    f"""
                    <div class="repo-card">
                        <div class="repo-title">{escape(short_title)}</div>
                        <div class="repo-meta">
                            {escape(rec_template)}<br>
                            {escape(rec_ticket or "No ticket")} · Saved {escape(updated_at[:16].replace("T"," "))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                r1, r2, r3 = st.columns(3)

                with r1:
                    st.button(
                        "Load",
                        key=f"repo_load_{rec_id}",
                        on_click=load_repository_entry,
                        args=(rec_id, False),
                        use_container_width=True,
                    )

                with r2:
                    st.button(
                        "Duplicate",
                        key=f"repo_dup_{rec_id}",
                        on_click=load_repository_entry,
                        args=(rec_id, True),
                        use_container_width=True,
                    )

                with r3:
                    st.button(
                        "Delete",
                        key=f"repo_delete_{rec_id}",
                        on_click=delete_repository_entry,
                        args=(rec_id,),
                        use_container_width=True,
                    )

        st.divider()
        st.caption(
            f"Database: {DB_PATH.name}\\n\\n"
            "Uploaded screenshots/icons are not stored in the repository; "
            "text fields and template settings are saved."
        )


else:
    html_output = st.session_state.get("last_html","")
    filename = st.session_state.get("last_filename","Broadcast.html")
    preview_height = st.session_state.get("last_preview_height",700)

    c1,c2 = st.columns(2)
    with c1:
        if st.button("← Back to Editor", use_container_width=True):
            st.session_state.preview_only = False
            st.rerun()
    with c2:
        st.download_button(
            "⬇ Download Template",
            data=html_output.encode("utf-8"),
            file_name=filename,
            mime="text/html",
            use_container_width=True,
        )

    st.components.v1.html(html_output, height=preview_height, scrolling=False)
