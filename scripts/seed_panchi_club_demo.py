#!/usr/bin/env python3
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHUNYA OS — Panchi Club 2.0 Demo Seed Script
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Idempotent seed script for Panchi Club 2.0 Demo.

Populates:
  1. NISHESH PERSONAL WORKSPACE — notes, commitments, timeline, conversations
  2. PANCHI CLUB SCENARIOS A-F — leads, tasks, commitments, outcomes
  3. CONTENT STUDIO — content_generations

Safe to re-run. Uses pre-checks + ON CONFLICT DO NOTHING for idempotency.

Usage:
  python3 scripts/seed_panchi_club_demo.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
from datetime import datetime, timezone

import psycopg2

# ── Database connection ────────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "shunya",
    "password": "IX-Mby1Phdtom1gEEeScNvw8QZOgHqzHVNdT_2B5EsA",
    "dbname": "shunya_os",
}

# ── Constants ──────────────────────────────────────────────────────────
IDENTITY_ID = "sid_a3cd655b1e6f4b0f9c1113ba7ec26d41"
PERSONAL_SPACE_ID = "spc_personal_a3cd655b1e6f4b0f"
PANCHI_SPACE_ID = "spc_c395aee038bc4d40"
TENANT_ID = 89  # Panchi Club tenant
ASSIGNED_TO = IDENTITY_ID

NOW = datetime.now(timezone.utc)


def connect():
    return psycopg2.connect(**DB_CONFIG)


def exec_sql(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params or {})
        return cur


# ── Idempotent insert helpers (return (id_or_None, created_bool)) ──────

def insert_founder_object(conn, object_id, space_id, object_type, name, content=None, status="active"):
    """Idempotent via unique object_id + ON CONFLICT DO NOTHING."""
    sql = """
        INSERT INTO founder_objects (object_id, space_id, object_type, name, content, status, created_by, created_at, updated_at)
        VALUES (%(object_id)s, %(space_id)s, %(object_type)s, %(name)s, %(content)s, %(status)s, %(created_by)s, %(created_at)s, %(updated_at)s)
        ON CONFLICT (object_id) DO NOTHING
    """
    params = {
        "object_id": object_id,
        "space_id": space_id,
        "object_type": object_type,
        "name": name,
        "content": content,
        "status": status,
        "created_by": IDENTITY_ID,
        "created_at": NOW,
        "updated_at": NOW,
    }
    cur = exec_sql(conn, sql, params)
    return cur.rowcount > 0  # True = was inserted


def insert_lead(conn, code, customer_name, status, source, notes=None, destination=None, assigned_to=None):
    """Idempotent via unique code + ON CONFLICT DO NOTHING. Returns (id, created)."""
    sql = """
        INSERT INTO leads (code, customer_name, status, source, notes, destination, assigned_to, created_at, updated_at)
        VALUES (%(code)s, %(customer_name)s, %(status)s, %(source)s, %(notes)s, %(destination)s, %(assigned_to)s, %(created_at)s, %(updated_at)s)
        ON CONFLICT (code) DO NOTHING
        RETURNING id
    """
    params = {
        "code": code,
        "customer_name": customer_name,
        "status": status,
        "source": source,
        "notes": notes,
        "destination": destination,
        "assigned_to": assigned_to or IDENTITY_ID,
        "created_at": NOW,
        "updated_at": NOW,
    }
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        if row:
            return row[0], True
        # Already existed — get existing id
        cur.execute("SELECT id FROM leads WHERE code = %s", (code,))
        row = cur.fetchone()
        return (row[0], False) if row else (None, False)


def insert_task_list(conn, name, lead_id, tenant_id=None):
    """Idempotent via pre-check on (lead_id, name). Returns (id, created)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM task_lists WHERE lead_id = %s AND name = %s",
            (lead_id, name)
        )
        row = cur.fetchone()
        if row:
            return row[0], False

    sql = """
        INSERT INTO task_lists (name, lead_id, tenant_id, created_by, created_at)
        VALUES (%(name)s, %(lead_id)s, %(tenant_id)s, %(created_by)s, %(created_at)s)
        RETURNING id
    """
    params = {
        "name": name,
        "lead_id": lead_id,
        "tenant_id": tenant_id,
        "created_by": IDENTITY_ID,
        "created_at": NOW,
    }
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0], True


def insert_task(conn, task_list_id, title, assigned_to, status="pending", priority=None, lead_id=None, sort_order=0):
    """Idempotent via pre-check on (task_list_id, title). Returns (id, created)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM tasks WHERE task_list_id = %s AND title = %s",
            (task_list_id, title)
        )
        row = cur.fetchone()
        if row:
            return row[0], False

    sql = """
        INSERT INTO tasks (task_list_id, title, assigned_to, status, priority, lead_id, sort_order, created_at)
        VALUES (%(task_list_id)s, %(title)s, %(assigned_to)s, %(status)s, %(priority)s, %(lead_id)s, %(sort_order)s, %(created_at)s)
        RETURNING id
    """
    params = {
        "task_list_id": task_list_id,
        "title": title,
        "assigned_to": assigned_to,
        "status": status,
        "priority": priority,
        "lead_id": lead_id,
        "sort_order": sort_order,
        "created_at": NOW,
    }
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0], True


def insert_commitment(conn, title, owner, status="active", due_at=None, meta=None, tenant_id=None):
    """Idempotent via pre-check on (title, owner). Returns (id, created)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM commitments WHERE title = %s AND owner = %s",
            (title, owner)
        )
        row = cur.fetchone()
        if row:
            return row[0], False

    sql = """
        INSERT INTO commitments (title, owner, status, meta, due_at, tenant_id, created_at, updated_at)
        VALUES (%(title)s, %(owner)s, %(status)s, %(meta)s, %(due_at)s, %(tenant_id)s, %(created_at)s, %(updated_at)s)
        RETURNING id
    """
    params = {
        "title": title,
        "owner": owner,
        "status": status,
        "meta": meta,
        "due_at": due_at,
        "tenant_id": tenant_id,
        "created_at": NOW,
        "updated_at": NOW,
    }
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return (row[0], True) if row else (None, False)


def insert_outcome(conn, tenant_id, subject_type, subject_id, actual_outcome, result="success",
                   goal=None, customer_impact=None, business_impact=None, financial_impact=None):
    """Idempotent via pre-check on (tenant_id, subject_type, subject_id, actual_outcome). Returns (id, created)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM outcomes WHERE tenant_id = %s AND subject_type = %s AND subject_id = %s AND actual_outcome = %s",
            (tenant_id, subject_type, subject_id, actual_outcome)
        )
        row = cur.fetchone()
        if row:
            return row[0], False

    sql = """
        INSERT INTO outcomes (tenant_id, subject_type, subject_id, goal, actual_outcome, result,
                              customer_impact, business_impact, financial_impact, created_at, updated_at)
        VALUES (%(tenant_id)s, %(subject_type)s, %(subject_id)s, %(goal)s, %(actual_outcome)s, %(result)s,
                %(customer_impact)s, %(business_impact)s, %(financial_impact)s, %(created_at)s, %(updated_at)s)
        RETURNING id
    """
    params = {
        "tenant_id": tenant_id,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "goal": goal,
        "actual_outcome": actual_outcome,
        "result": result,
        "customer_impact": customer_impact,
        "business_impact": business_impact,
        "financial_impact": financial_impact,
        "created_at": NOW,
        "updated_at": NOW,
    }
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return (row[0], True) if row else (None, False)


def insert_content_generation(conn, identity_id, content_type, prompt, platform=None,
                              generated_content=None, target_audience=None, tone=None, word_count=None):
    """Idempotent via pre-check on (identity_id, content_type, prompt). Returns (id, created)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM m6_content_generations WHERE identity_id = %s AND content_type = %s AND prompt = %s",
            (identity_id, content_type, prompt)
        )
        row = cur.fetchone()
        if row:
            return row[0], False

    sql = """
        INSERT INTO m6_content_generations (identity_id, content_type, platform, prompt, generated_content,
                                            target_audience, tone, word_count, created_at)
        VALUES (%(identity_id)s, %(content_type)s, %(platform)s, %(prompt)s, %(generated_content)s,
                %(target_audience)s, %(tone)s, %(word_count)s, %(created_at)s)
        RETURNING id
    """
    params = {
        "identity_id": identity_id,
        "content_type": content_type,
        "platform": platform,
        "prompt": prompt,
        "generated_content": generated_content,
        "target_audience": target_audience,
        "tone": tone,
        "word_count": word_count,
        "created_at": NOW,
    }
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return (row[0], True) if row else (None, False)


def insert_founder_conversation(conn, conv_id, object_id, title, status="active"):
    """Idempotent via unique conv_id + ON CONFLICT DO NOTHING."""
    sql = """
        INSERT INTO founder_conversations (conv_id, object_id, title, identity_id, status, created_at, updated_at)
        VALUES (%(conv_id)s, %(object_id)s, %(title)s, %(identity_id)s, %(status)s, %(created_at)s, %(updated_at)s)
        ON CONFLICT (conv_id) DO NOTHING
    """
    params = {
        "conv_id": conv_id,
        "object_id": object_id,
        "title": title,
        "identity_id": IDENTITY_ID,
        "status": status,
        "created_at": NOW,
        "updated_at": NOW,
    }
    exec_sql(conn, sql, params)


# ═══════════════════════════════════════════════════════════════════════
# SEED FUNCTIONS (each commits independently)
# ═══════════════════════════════════════════════════════════════════════

def seed_personal_workspace(conn):
    """Seed Nishesh's personal workspace with founder_objects."""
    print("\n─── 1. NISHESH PERSONAL WORKSPACE ───")
    counts = {"notes": 0, "commitments": 0, "timeline_events": 0, "conversations": 0}

    notes = [
        ("fo_personal_note_1", "SHUNYA Launch Strategy Notes",
         "Strategic launch plan for SHUNYA OS. Target markets: SMBs in Southeast Asia. "
         "Key differentiators: AI-native operations, unified workspace, zero-config onboarding. "
         "Launch date target: Q1 2027. Budget allocation: 40% engineering, 30% marketing, "
         "20% sales, 10% operations. Referral program to drive early adoption."),
        ("fo_personal_note_2", "Founder Strategic Review — Q4 2026",
         "Q4 2026 strategic review: Panchi Club revenue up 34% YoY. Customer acquisition cost "
         "down 18% due to referral program. Net Promoter Score improved to 72 (from 65). "
         "Key risks: supplier capacity constraints in Bali, rising airfare costs. "
         "Opportunities: Vietnam market expansion, corporate travel partnerships."),
        ("fo_personal_note_3", "Personal Research — AI in Travel Industry",
         "Research notes on AI applications in travel: 1) AI-powered itinerary optimization "
         "reducing planning time by 60%. 2) Predictive pricing models improving yield by 22%. "
         "3) Chat-based concierge services seeing 4.8* satisfaction. 4) Computer vision for "
         "luggage handling and check-in. Key vendors: OpenAI, Anthropic, Google Vertex AI. "
         "Implementation priority: AI concierge for Panchi Club members."),
    ]
    for oid, name, content in notes:
        if insert_founder_object(conn, oid, PERSONAL_SPACE_ID, "note", name, content):
            counts["notes"] += 1
    print(f"  Notes: 3 ({counts['notes']} new)")

    commitments = [
        ("fo_personal_commit_1", "Prepare for Board Demo",
         "Board presentation preparation: finalize Panchi Club 2.0 demo flow, prepare Q&A "
         "document, rehearse key talking points, ensure all demo data is loaded. "
         "Stakeholders: Nishesh (presenter), Rohan (technical backup), Priya (financials)."),
        ("fo_personal_commit_2", "Review Panchi Club Partnership Agreement",
         "Review the partnership agreement with Bali Eco Lodge and Vietnam Tourism Board. "
         "Key terms: revenue share (15% commission), exclusivity clause (12 months), "
         "minimum volume commitment (50 bookings/quarter). Legal review needed before signing."),
        ("fo_personal_commit_3", "Complete M2C Milestone Review",
         "M2C review for Q3 2026. Evaluate all active commitments against targets. "
         "Identify at-risk items. Prepare remediation plan for board review. "
         "Focus areas: customer loyalty program, carbon-neutral certification, Vietnam expansion."),
    ]
    for oid, name, content in commitments:
        if insert_founder_object(conn, oid, PERSONAL_SPACE_ID, "commitment", name, content):
            counts["commitments"] += 1
    print(f"  Commitments: 3 ({counts['commitments']} new)")

    timeline = [
        ("fo_personal_timeline_1", "Incorporated SHUNYA OS",
         "SHUNYA OS officially incorporated on 15 March 2026. Vision: democratize business "
         "operations through AI-native software. Initial team: 3 founders, 2 engineers. "
         "Seed funding: $500K from angel investors."),
        ("fo_personal_timeline_2", "First Panchi Club meeting",
         "First Panchi Club strategy meeting held on 1 June 2026. Defined mission: premium "
         "travel and lifestyle club for Southeast Asia. Initial focus: Bali, Thailand, Vietnam. "
         "Target: 100 members by end of year."),
    ]
    for oid, name, content in timeline:
        if insert_founder_object(conn, oid, PERSONAL_SPACE_ID, "timeline_event", name, content):
            counts["timeline_events"] += 1
    print(f"  Timeline events: 2 ({counts['timeline_events']} new)")

    conversations = [
        ("fo_personal_conv_1", "Meeting with design team",
         "Design team meeting discussing Panchi Club 2.0 UI/UX overhaul. Key decisions: "
         "adopt Mantine v9, implement dark mode, redesign booking flow for mobile-first. "
         "Timeline: wireframes by 15 Sep, prototype by 1 Oct."),
        ("fo_personal_conv_2", "Vendor discussion — Bali logistics",
         "Discussion with Bali logistics vendors about ground transport, hotel partnerships, "
         "and activity booking APIs. Shortlisted: Bali Transfers, Eco Lodge Network, "
         "AdventureHub. Negotiating 15% commission for 50+ bookings/month."),
    ]
    for oid, name, content in conversations:
        if insert_founder_object(conn, oid, PERSONAL_SPACE_ID, "conversation", name, content):
            counts["conversations"] += 1
            insert_founder_conversation(conn, f"c_{oid}", oid, name)
    print(f"  Conversations: 2 ({counts['conversations']} new)")

    conn.commit()
    total = sum(counts.values())
    print(f"  Total: {total} new personal workspace objects")
    return counts


# ── Scenario A: Priya Mehta (new lead) ─────────────────────────────────

def seed_scenario_a_priya(conn):
    print("\n─── Scenario A: New Lead — Priya Mehta ───")
    counts = {}
    lead_id, created = insert_lead(
        conn, code="L-PC-A-001", customer_name="Priya Mehta",
        status="new", source="referral",
        notes="Referred by Rohan Kapoor. Interested in Bali honeymoon package. "
              "Looking for 7-day itinerary with luxury accommodations. "
              "Budget: $3,000-$5,000. Travel dates: February 2027.",
        destination="Bali")
    if lead_id:
        if created:
            counts["lead"] = 1
        print(f"  Lead: Priya Mehta (id={lead_id}){' (new)' if created else ' (existing)'}")
        tl_id, _ = insert_task_list(conn, name="Priya Mehta — Onboarding", lead_id=lead_id, tenant_id=TENANT_ID)
        _, task_created = insert_task(conn, task_list_id=tl_id, title="Send Priya Mehta Bali brochure",
                                      assigned_to=ASSIGNED_TO, status="pending", lead_id=lead_id, sort_order=1)
        if task_created:
            counts["task"] = counts.get("task", 0) + 1
        print(f"  Task: Send Bali brochure{' (new)' if task_created else ' (existing)'}")
    else:
        print("  Lead already exists, skipping")
    conn.commit()
    return counts


# ── Scenario B: Rohan Kapoor (active trip planning) ────────────────────

def seed_scenario_b_rohan(conn):
    print("\n─── Scenario B: Active Trip Planning — Rohan Kapoor ───")
    counts = {}
    lead_id, created = insert_lead(
        conn, code="L-PC-B-001", customer_name="Rohan Kapoor",
        status="qualified", source="repeat_customer",
        notes="Returning customer planning Bali family trip. Family of 4 (2 adults, "
              "2 children). Interested in cultural experiences, beach activities, "
              "and kid-friendly excursions. Travel window: June 2027. Budget: $6,000-$8,000.",
        destination="Bali")
    if lead_id:
        if created:
            counts["lead"] = 1
        print(f"  Lead: Rohan Kapoor (id={lead_id}){' (new)' if created else ' (existing)'}")
        tl_id, _ = insert_task_list(conn, name="Rohan Kapoor — Bali Family Trip", lead_id=lead_id, tenant_id=TENANT_ID)
        tasks_data = [
            ("Prepare Bali itinerary for Rohan", 1),
            ("Quote 5-night package", 2),
            ("Check villa availability for June", 3),
        ]
        for title, sort_order in tasks_data:
            _, tc = insert_task(conn, task_list_id=tl_id, title=title, assigned_to=ASSIGNED_TO,
                                status="pending", lead_id=lead_id, sort_order=sort_order)
            if tc:
                counts["tasks"] = counts.get("tasks", 0) + 1
        print(f"  Tasks: 3 ({counts.get('tasks', 0)} new)")
        meta = '{"lead_id": ' + str(lead_id) + ', "customer": "Rohan Kapoor", "type": "proposal"}'
        _, cc = insert_commitment(conn, title="Deliver Bali family package proposal by 5 Sep",
                                  owner="Nishesh", status="active",
                                  due_at="2026-09-05T18:00:00+00:00",
                                  meta=meta, tenant_id=TENANT_ID)
        if cc:
            counts["commitment"] = counts.get("commitment", 0) + 1
        print(f"  Commitment: Deliver Bali family package proposal by 5 Sep{' (new)' if cc else ' (existing)'}")
    else:
        print("  Lead already exists, skipping")
    conn.commit()
    return counts


# ── Scenario C: Aarav Sharma (confirmed customer) ─────────────────────

def seed_scenario_c_aarav(conn):
    print("\n─── Scenario C: Confirmed Customer — Aarav Sharma ───")
    counts = {}
    lead_id, created = insert_lead(
        conn, code="L-PC-C-001", customer_name="Aarav Sharma",
        status="won", source="website",
        notes="Booked Bali Eco Honeymoon package via website. "
              "Package: 7 nights at Bali Eco Lodge, airport transfers, "
              "spa package, guided eco-tours. Total: $4,200.",
        destination="Bali")
    if lead_id:
        if created:
            counts["lead"] = 1
        print(f"  Lead: Aarav Sharma (id={lead_id}){' (new)' if created else ' (existing)'}")
        tl_id, _ = insert_task_list(conn, name="Aarav Sharma — Bali Eco Honeymoon", lead_id=lead_id, tenant_id=TENANT_ID)
        tasks_data = [
            ("Book Bali Eco Lodge", 1),
            ("Arrange airport transfer", 2),
            ("Confirm spa appointment", 3),
        ]
        for title, sort_order in tasks_data:
            _, tc = insert_task(conn, task_list_id=tl_id, title=title, assigned_to=ASSIGNED_TO,
                                status="pending", lead_id=lead_id, sort_order=sort_order)
            if tc:
                counts["tasks"] = counts.get("tasks", 0) + 1
        print(f"  Tasks: 3 ({counts.get('tasks', 0)} new)")
        meta = '{"lead_id": ' + str(lead_id) + ', "customer": "Aarav Sharma", "package": "Bali Eco Honeymoon"}'
        _, cc = insert_commitment(conn, title="Bali Eco Honeymoon — Confirmed",
                                  owner="Nishesh", status="active", meta=meta, tenant_id=TENANT_ID)
        if cc:
            counts["commitment"] = counts.get("commitment", 0) + 1
        print(f"  Commitment: Bali Eco Honeymoon — Confirmed{' (new)' if cc else ' (existing)'}")
        _, oc = insert_outcome(conn, tenant_id=TENANT_ID, subject_type="lead", subject_id=lead_id,
                               goal="Close Bali Eco Honeymoon package sale",
                               actual_outcome="Aarav Sharma honeymoon package sold — $4,200",
                               result="success",
                               customer_impact="Premium honeymoon experience with eco-friendly accommodations",
                               business_impact="Revenue: $4,200. Positive review expected to drive referrals",
                               financial_impact="Full payment received. Net margin: 32%")
        if oc:
            counts["outcome"] = counts.get("outcome", 0) + 1
        print(f"  Outcome: Aarav Sharma honeymoon package sold — $4,200{' (new)' if oc else ' (existing)'}")
    else:
        print("  Lead already exists, skipping")
    conn.commit()
    return counts


# ── Scenario D: Vikram Singh (near-future departure) ───────────────────

def seed_scenario_d_vikram(conn):
    print("\n─── Scenario D: Near-future Departure — Vikram Singh ───")
    counts = {}
    lead_id, created = insert_lead(
        conn, code="L-PC-D-001", customer_name="Vikram Singh",
        status="won", source="referral",
        notes="Referred by Ananya Patel. Booked Bali Adventure package. "
              "Departure: 12 November 2026. Solo traveler. Budget: $3,500.",
        destination="Bali")
    if lead_id:
        if created:
            counts["lead"] = 1
        print(f"  Lead: Vikram Singh (id={lead_id}){' (new)' if created else ' (existing)'}")
        tl_id, _ = insert_task_list(conn, name="Vikram Singh — Bali Adventure Pre-departure",
                                   lead_id=lead_id, tenant_id=TENANT_ID)
        tasks_data = [
            ("Vikram — confirm vegetarian meals", 1),
            ("Vikram — print travel documents", 2),
            ("Vikram — final payment reminder", 3),
        ]
        for title, sort_order in tasks_data:
            _, tc = insert_task(conn, task_list_id=tl_id, title=title, assigned_to=ASSIGNED_TO,
                                status="pending", lead_id=lead_id, sort_order=sort_order)
            if tc:
                counts["tasks"] = counts.get("tasks", 0) + 1
        print(f"  Tasks: 3 ({counts.get('tasks', 0)} new)")
        meta = '{"lead_id": ' + str(lead_id) + ', "customer": "Vikram Singh", "departure": "2026-11-12"}'
        _, cc = insert_commitment(conn, title="Vikram Singh Bali Adventure — Departing 12 Nov",
                                  owner="Nishesh", status="active", meta=meta, tenant_id=TENANT_ID)
        if cc:
            counts["commitment"] = counts.get("commitment", 0) + 1
        print(f"  Commitment: Vikram Singh Bali Adventure — Departing 12 Nov{' (new)' if cc else ' (existing)'}")
    else:
        print("  Lead already exists, skipping")
    conn.commit()
    return counts


# ── Scenario E: Ananya Patel (completed trip) ─────────────────────────

def seed_scenario_e_ananya(conn):
    print("\n─── Scenario E: Completed Trip — Ananya Patel ───")
    counts = {}
    lead_id, created = insert_lead(
        conn, code="L-PC-E-001", customer_name="Ananya Patel",
        status="won", source="referral",
        notes="Completed Bali trip August 2026. Excellent feedback. "
              "Referred 2 new customers (Vikram Singh and Neha Gupta). "
              "Package: Bali Explorer 10-day. Total: $5,800.",
        destination="Bali")
    if lead_id:
        if created:
            counts["lead"] = 1
        print(f"  Lead: Ananya Patel (id={lead_id}){' (new)' if created else ' (existing)'}")
        meta = '{"lead_id": ' + str(lead_id) + ', "customer": "Ananya Patel", "trip_dates": "Aug 2026"}'
        _, cc = insert_commitment(conn, title="Ananya Patel Bali Trip — Completed Aug 2026",
                                  owner="Nishesh", status="completed", meta=meta, tenant_id=TENANT_ID)
        if cc:
            counts["commitment"] = counts.get("commitment", 0) + 1
        print(f"  Commitment: Ananya Patel Bali Trip — Completed Aug 2026{' (new)' if cc else ' (existing)'}")
        outcomes_data = [
            ("Excellent feedback — 5* review",
             "Ananya rated her Bali experience 5 out of 5 stars. "
             "Exceptional guide service, seamless logistics, personalized attention."),
            ("Ananya referred 2 new customers",
             "Ananya referred Vikram Singh and Neha Gupta. Both have booked packages. "
             "Referral credit applied. Referral program driving 34% of new business."),
        ]
        for outcome_text, impact in outcomes_data:
            _, oc = insert_outcome(conn, tenant_id=TENANT_ID, subject_type="lead", subject_id=lead_id,
                                   goal="Deliver exceptional Bali experience leading to referrals",
                                   actual_outcome=outcome_text, result="success",
                                   customer_impact=impact,
                                   business_impact="Referral-driven growth: 2 new customers acquired",
                                   financial_impact="Combined revenue from referrals: $7,700")
            if oc:
                counts["outcomes"] = counts.get("outcomes", 0) + 1
        print(f"  Outcomes: 2 ({counts.get('outcomes', 0)} new)")
    else:
        print("  Lead already exists, skipping")
    conn.commit()
    return counts


# ── Scenario F: Kavya Reddy (high-value complex) ──────────────────────

def seed_scenario_f_kavya(conn):
    print("\n─── Scenario F: High-value Complex — Kavya Reddy ───")
    counts = {}
    lead_id, created = insert_lead(
        conn, code="L-PC-F-001", customer_name="Kavya Reddy",
        status="negotiation", source="agent",
        notes="High-value multi-destination inquiry via travel agent. "
              "Group of 6. Destinations: Bali (5 nights) + Vietnam (7 nights). "
              "Estimated budget: $15,000-$20,000. Travel: March 2027. "
              "Agent commission: 12%. High priority.",
        destination="Bali + Vietnam")
    if lead_id:
        if created:
            counts["lead"] = 1
        print(f"  Lead: Kavya Reddy (id={lead_id}){' (new)' if created else ' (existing)'}")
        tl_id, _ = insert_task_list(conn, name="Kavya Reddy — Bali + Vietnam Executive Tour",
                                   lead_id=lead_id, tenant_id=TENANT_ID)
        tasks_data = [
            ("Coordinate multi-city itinerary", 1),
            ("Book 3 hotels across 2 countries", 2),
            ("Arrange inter-island flights", 3),
            ("Finalize Vietnam add-on package", 4),
        ]
        for title, sort_order in tasks_data:
            _, tc = insert_task(conn, task_list_id=tl_id, title=title, assigned_to=ASSIGNED_TO,
                                status="pending", lead_id=lead_id, sort_order=sort_order)
            if tc:
                counts["tasks"] = counts.get("tasks", 0) + 1
        print(f"  Tasks: 4 ({counts.get('tasks', 0)} new)")
        meta = ('{"lead_id": ' + str(lead_id) + ', "customer": "Kavya Reddy", '
                '"destinations": ["Bali", "Vietnam"], "travelers": 6, "type": "executive_tour"}')
        _, cc = insert_commitment(conn, title="Kavya Reddy — Bali + Vietnam Executive Tour",
                                  owner="Nishesh", status="active", meta=meta, tenant_id=TENANT_ID)
        if cc:
            counts["commitment"] = counts.get("commitment", 0) + 1
        print(f"  Commitment: Kavya Reddy — Bali + Vietnam Executive Tour{' (new)' if cc else ' (existing)'}")
    else:
        print("  Lead already exists, skipping")
    conn.commit()
    return counts


# ── Content Studio ─────────────────────────────────────────────────────

def seed_content_studio(conn):
    print("\n─── 3. CONTENT STUDIO DATA ───")
    content_items = [
        {
            "content_type": "social",
            "platform": "Instagram",
            "prompt": "Create an Instagram post for the Bali Honeymoon Package. "
                      "Target: newly engaged couples (25-35). "
                      "Style: romantic, aspirational, tropical.",
            "generated_content": "Forever starts here. Imagine waking up to the sound of "
                                 "waves at our private Bali Eco Lodge. "
                                 "Bali Honeymoon Package starting at $3,200. "
                                 "DM us to plan your perfect honeymoon!",
            "target_audience": "Newly engaged couples (25-35)",
            "tone": "romantic_aspirational",
            "word_count": 85,
        },
        {
            "content_type": "campaign",
            "platform": "Multi-channel",
            "prompt": "Design a seasonal travel campaign for Panchi Club. "
                      "Theme: 'Winter Escape to Southeast Asia'. "
                      "Target: premium travelers (30-55). "
                      "Offer: 15% off on bookings before 30 Nov.",
            "generated_content": "Winter Escape Collection. Escape the cold with Panchi Club. "
                                 "Bali from $2,800. Thailand from $2,500. Vietnam from $2,200. "
                                 "Early Bird Offer: Save 15% when you book before 30 Nov.",
            "target_audience": "Premium travelers (30-55)",
            "tone": "luxury_warm",
            "word_count": 105,
        },
        {
            "content_type": "blog",
            "platform": "Website",
            "prompt": "Write a blog concept featuring Bali Eco Lodge customer testimonial. "
                      "Style: authentic, inspiring. Include customer journey highlights. "
                      "Target: eco-conscious travelers.",
            "generated_content": "Bali Eco Lodge: A Honeymoon Story. "
                                 "From the moment we arrived, everything was perfect. "
                                 "Ready for your own Bali story? Panchi Club makes it effortless.",
            "target_audience": "Eco-conscious travelers, honeymoon couples",
            "tone": "authentic_inspiring",
            "word_count": 180,
        },
    ]

    created = 0
    for item in content_items:
        _, is_new = insert_content_generation(
            conn, identity_id=IDENTITY_ID,
            content_type=item["content_type"],
            platform=item["platform"],
            prompt=item["prompt"],
            generated_content=item["generated_content"],
            target_audience=item["target_audience"],
            tone=item["tone"],
            word_count=item["word_count"],
        )
        if is_new:
            created += 1
    print(f"  Content generations: 3 ({created} new)")
    conn.commit()
    return {"content_generations": created}


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  SHUNYA OS — Panchi Club 2.0 Demo Seed Script          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Identity: {IDENTITY_ID}")
    print(f"  Tenant: Panchi Club (id={TENANT_ID})")
    print(f"  Personal Space: {PERSONAL_SPACE_ID}")
    print(f"  Panchi Space: {PANCHI_SPACE_ID}")

    conn = connect()
    try:
        total_counts = {}
        total_counts["personal"] = seed_personal_workspace(conn)
        total_counts["scenario_a"] = seed_scenario_a_priya(conn)
        total_counts["scenario_b"] = seed_scenario_b_rohan(conn)
        total_counts["scenario_c"] = seed_scenario_c_aarav(conn)
        total_counts["scenario_d"] = seed_scenario_d_vikram(conn)
        total_counts["scenario_e"] = seed_scenario_e_ananya(conn)
        total_counts["scenario_f"] = seed_scenario_f_kavya(conn)
        total_counts["content_studio"] = seed_content_studio(conn)

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        personal_total = sum(total_counts["personal"].values())
        print(f"\n  1. Personal Workspace:     {personal_total} new objects")

        scenario_keys = ["scenario_a", "scenario_b", "scenario_c", "scenario_d", "scenario_e", "scenario_f"]
        scenario_labels = ["A: Priya Mehta", "B: Rohan Kapoor", "C: Aarav Sharma",
                           "D: Vikram Singh", "E: Ananya Patel", "F: Kavya Reddy"]
        scenario_total = 0
        for key, label in zip(scenario_keys, scenario_labels):
            sc = total_counts[key]
            sc_total = sum(sc.values())
            scenario_total += sc_total
            if sc_total > 0:
                print(f"  2.{key[-1].upper()}  {label}:         {sc_total} new records")
            else:
                print(f"  2.{key[-1].upper()}  {label}:         (all existing, no new records)")

        content_total = sum(total_counts["content_studio"].values())
        all_total = personal_total + scenario_total + content_total
        print(f"\n  Total new records:         {all_total}")
        print(f"\n  Script is idempotent — re-run safely (0 new records on re-run).")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\n  ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()