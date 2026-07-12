#!/usr/bin/env python3
"""Comprehensive reseed — ALL entity types with data, linked end-to-end."""
import sys, os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.expanduser("~/shunya_os"))
from app import create_app, db
from app.models import Tenant, TeamMember, EntityDefinition, Entity, Person, Relationship

app = create_app('production')
with app.app_context():
    tenant = db.session.query(Tenant).first()
    user = db.session.query(TeamMember).filter_by(tenant_id=tenant.id).first()
    now = datetime.utcnow()
    tid, uid = tenant.id, user.id
    counts = {}

    def get_def(etype):
        return db.session.query(EntityDefinition).filter_by(tenant_id=tid, type=etype).first()

    def def_or_create(etype, label, icon, schema, statuses, layout="table"):
        d = get_def(etype)
        if not d:
            d = EntityDefinition(tenant_id=tid, type=etype, label=label, icon=icon,
                schema=schema, statuses=statuses, layout=layout,
                searchable_fields=[s["name"] for s in schema if s.get("searchable")],
                primary_field=schema[0]["name"])
            db.session.add(d); db.session.flush()
        return d

    def seed_etype(etype, records, force=False):
        d = get_def(etype)
        if not d:
            return 0, "no def"
        existing = db.session.query(Entity).filter_by(tenant_id=tid, definition_id=d.id).count()
        if existing > 0 and not force:
            return 0, f"has {existing}"
        created = 0
        for i, rec in enumerate(records):
            status = rec.pop("_status", "active") if isinstance(rec, dict) else "active"
            code = f"{etype.upper()[:4]}-{i+1:04d}"
            display_name = rec.get(list(rec.keys())[0], str(rec)) if isinstance(rec, dict) else str(rec)
            db.session.add(Entity(tenant_id=tid, definition_id=d.id, code=code, status=status, data=rec, created_by=uid))
            created += 1
        return created, "ok"

    # =====================================================================
    # CLEAR old data to start fresh
    # =====================================================================
    from app.models import ActivityLog, Message, File
    db.session.query(ActivityLog).filter_by(tenant_id=tid).delete()
    db.session.query(Message).filter_by(tenant_id=tid).delete()
    db.session.query(File).filter_by(tenant_id=tid).delete()
    db.session.query(Entity).filter_by(tenant_id=tid).delete()
    db.session.commit()
    print("Cleared old entity data")

    # =====================================================================
    # DEFINE ALL missing entity types
    # =====================================================================
    def_or_create("department","Department","🏢",
        [{"name":"name","label":"Name","type":"text","required":True,"searchable":True},{"name":"code","label":"Code","type":"text"},{"name":"head","label":"Head","type":"text"}],
        ["active","inactive"])
    def_or_create("employee","Employee","👤",
        [{"name":"employee_name","label":"Name","type":"text","required":True,"searchable":True},{"name":"email","label":"Email","type":"email","searchable":True},{"name":"phone","label":"Phone","type":"phone"},{"name":"department","label":"Department","type":"text"},{"name":"position","label":"Position","type":"text"},{"name":"salary","label":"Salary","type":"number"},{"name":"date_of_joining","label":"Joined","type":"date"}],
        ["active","onboarding","exited"])
    def_or_create("leave_request","Leave","🏖️",
        [{"name":"employee_name","label":"Employee","type":"text","required":True},{"name":"leave_type","label":"Type","type":"select","options":["sick","casual","annual","personal"]},{"name":"start_date","label":"Start","type":"date"},{"name":"end_date","label":"End","type":"date"},{"name":"reason","label":"Reason","type":"textarea"}],
        ["pending","approved","rejected"])
    def_or_create("campaign","Campaign","📢",
        [{"name":"name","label":"Name","type":"text","required":True},{"name":"channel","label":"Channel","type":"select","options":["email","social","whatsapp","multi"]},{"name":"budget","label":"Budget","type":"number"},{"name":"target","label":"Target","type":"text"},{"name":"status","label":"Status","type":"text"}],
        ["active","paused","completed","cancelled"],"kanban")
    def_or_create("ticket","Support Ticket","🎫",
        [{"name":"customer_name","label":"Customer","type":"text","required":True,"searchable":True},{"name":"subject","label":"Subject","type":"text","required":True},{"name":"priority","label":"Priority","type":"select","options":["low","medium","high","urgent"]},{"name":"assigned_to","label":"Assigned To","type":"text"},{"name":"description","label":"Description","type":"textarea"}],
        ["new","open","in_progress","resolved","closed"],"kanban")
    def_or_create("supplier","Supplier","🏢",
        [{"name":"company_name","label":"Company","type":"text","required":True},{"name":"category","label":"Category","type":"select","options":["hotel","dmc","airline","transport","activity"]},{"name":"contact_person","label":"Contact","type":"text"},{"name":"phone","label":"Phone","type":"text"}],
        ["active","inactive","blacklisted"])
    def_or_create("product","Product","📦",
        [{"name":"name","label":"Name","type":"text","required":True},{"name":"category","label":"Category","type":"select","options":["hotel","flight","transfer","package","service"]},{"name":"unit_price","label":"Price","type":"number"},{"name":"supplier","label":"Supplier","type":"text"}],["active","inactive"])
    def_or_create("purchase_order","Purchase Order","📝",
        [{"name":"po_number","label":"PO #","type":"text","required":True},{"name":"supplier_name","label":"Supplier","type":"text"},{"name":"total_amount","label":"Total","type":"number"},{"name":"order_date","label":"Date","type":"date"},{"name":"notes","label":"Notes","type":"textarea"}],
        ["draft","sent","confirmed","received","cancelled"])
    def_or_create("warehouse","Warehouse","🏗️",
        [{"name":"name","label":"Name","type":"text","required":True},{"name":"location","label":"Location","type":"text"},{"name":"manager","label":"Manager","type":"text"}],["active","inactive","maintenance"])
    def_or_create("work_order","Work Order","🔧",
        [{"name":"title","label":"Title","type":"text","required":True},{"name":"customer_name","label":"Customer","type":"text"},{"name":"technician","label":"Assigned To","type":"text"},{"name":"scheduled_date","label":"Date","type":"date"},{"name":"description","label":"Description","type":"textarea"}],
        ["pending","scheduled","in_progress","completed","cancelled"],"kanban")
    def_or_create("subcontractor","Subcontractor","👷",
        [{"name":"company_name","label":"Company","type":"text","required":True},{"name":"specialty","label":"Specialty","type":"select","options":["guide","driver","photographer","hiking","events"]},{"name":"phone","label":"Phone","type":"text"},{"name":"rating","label":"Rating","type":"number"}],
        ["active","on_project","inactive"])
    def_or_create("estimate","Estimate","📐",
        [{"name":"project_name","label":"Project","type":"text","required":True},{"name":"customer_name","label":"Customer","type":"text"},{"name":"total","label":"Total","type":"number"},{"name":"valid_until","label":"Valid Until","type":"date"}],
        ["draft","sent","accepted","rejected","expired"])
    def_or_create("contract","Contract","📜",
        [{"name":"title","label":"Title","type":"text","required":True},{"name":"party_b","label":"Party B","type":"text"},{"name":"contract_type","label":"Type","type":"select","options":["vendor","client","nda","lease"]},{"name":"value","label":"Value","type":"number"},{"name":"start_date","label":"Start","type":"date"}],
        ["active","expiring_soon","expired","draft"])
    def_or_create("document_template","Document Template","📄",
        [{"name":"name","label":"Name","type":"text","required":True},{"name":"category","label":"Category","type":"select","options":["voucher","invoice","itinerary","proposal"]}],["active","draft","archived"])
    def_or_create("compliance_item","Compliance Item","✅",
        [{"name":"regulation","label":"Regulation","type":"text","required":True},{"name":"category","label":"Category","type":"select","options":["iso","gdpr","safety","tax","labor"]},{"name":"due_date","label":"Due Date","type":"date"},{"name":"assigned_to","label":"Assigned To","type":"text"}],
        ["pending","in_progress","compliant","non_compliant","overdue"])
    def_or_create("account","Account","🏢",
        [{"name":"account_name","label":"Name","type":"text","required":True,"searchable":True},{"name":"industry","label":"Industry","type":"text"},{"name":"city","label":"City","type":"text"},{"name":"annual_revenue","label":"Annual Revenue","type":"number"}],
        ["active","inactive"])
    def_or_create("lead","Lead","🎯",
        [{"name":"first_name","label":"First Name","type":"text","required":True},{"name":"last_name","label":"Last Name","type":"text","required":True},{"name":"email","label":"Email","type":"email"},{"name":"phone","label":"Phone","type":"phone"},{"name":"company","label":"Company","type":"text"},{"name":"lead_source","label":"Source","type":"select","options":["website","referral","social_media","event","cold_call"]},{"name":"lead_score","label":"Score","type":"number"}],
        ["new","contacted","qualified","converted","junk"],"kanban")
    def_or_create("contact","Contact","👤",
        [{"name":"first_name","label":"First Name","type":"text","required":True},{"name":"last_name","label":"Last Name","type":"text","required":True},{"name":"email","label":"Email","type":"email"},{"name":"phone","label":"Phone","type":"phone"},{"name":"account_name","label":"Account","type":"text"},{"name":"job_title","label":"Title","type":"text"}],["active","inactive"])
    def_or_create("quote","Quote","📄",
        [{"name":"quote_number","label":"Quote #","type":"text","required":True},{"name":"account_name","label":"Account","type":"text"},{"name":"total_amount","label":"Total","type":"number"},{"name":"valid_until","label":"Valid Until","type":"date"}],
        ["draft","sent","accepted","rejected","expired"])
    def_or_create("invoice","Invoice","🧾",
        [{"name":"invoice_number","label":"Invoice #","type":"text","required":True},{"name":"customer_name","label":"Customer","type":"text"},{"name":"amount","label":"Amount","type":"number"},{"name":"status","label":"Status","type":"select","options":["pending","paid","overdue","cancelled"]},{"name":"due_date","label":"Due Date","type":"date"}],
        ["pending","paid","overdue","cancelled"])
    def_or_create("payment","Payment","💳",
        [{"name":"customer_name","label":"Customer","type":"text"},{"name":"amount","label":"Amount","type":"number"},{"name":"type","label":"Type","type":"select","options":["received","sent","refund"]},{"name":"gateway","label":"Gateway","type":"text"},{"name":"status","label":"Status","type":"select","options":["pending","completed","failed"]}],
        ["pending","completed","failed"])
    def_or_create("project","Project","📋",
        [{"name":"name","label":"Name","type":"text","required":True},{"name":"description","label":"Description","type":"textarea"},{"name":"start_date","label":"Start","type":"date"},{"name":"end_date","label":"End","type":"date"},{"name":"priority","label":"Priority","type":"select","options":["low","medium","high","critical"]},{"name":"department","label":"Dept","type":"text"}],
        ["active","completed","on_hold","cancelled"])
    def_or_create("target_list","Target List","📋",
        [{"name":"name","label":"Name","type":"text","required":True},{"name":"description","label":"Description","type":"textarea"},{"name":"list_type","label":"Type","type":"select","options":["static","dynamic","campaign"]}],
        ["active","inactive","archived"])
    def_or_create("knowledge_article","Knowledge Article","📚",
        [{"name":"title","label":"Title","type":"text","required":True},{"name":"category","label":"Category","type":"select","options":["visa","destinations","tips","policies"]},{"name":"content","label":"Content","type":"textarea"}],["published","draft","archived"])
    def_or_create("faq","FAQ","❓",
        [{"name":"question","label":"Question","type":"text","required":True},{"name":"answer","label":"Answer","type":"textarea"},{"name":"category","label":"Category","type":"text"}],["published","draft"])
    def_or_create("customer_feedback","Customer Feedback","💬",
        [{"name":"customer_name","label":"Customer","type":"text"},{"name":"rating","label":"Rating","type":"number"},{"name":"comments","label":"Comments","type":"textarea"}],["new","reviewed","actioned"])
    def_or_create("sla_policy","SLA Policy","⏱️",
        [{"name":"name","label":"Name","type":"text","required":True},{"name":"response_time","label":"Response Time","type":"text"},{"name":"resolution_time","label":"Resolution Time","type":"text"}],["active","inactive"])
    def_or_create("social_post","Social Post","📱",
        [{"name":"content","label":"Content","type":"textarea","required":True},{"name":"platform","label":"Platform","type":"select","options":["instagram","facebook","linkedin","twitter"]},{"name":"status","label":"Status","type":"select","options":["draft","scheduled","published"]}],
        ["draft","scheduled","published"])
    def_or_create("landing_page","Landing Page","🖥️",
        [{"name":"title","label":"Title","type":"text","required":True},{"name":"url","label":"URL","type":"text"},{"name":"campaign","label":"Campaign","type":"text"},{"name":"conversions","label":"Conversions","type":"number"}],
        ["active","inactive"])
    def_or_create("analytics_report","Analytics Report","📊",
        [{"name":"name","label":"Report Name","type":"text","required":True},{"name":"metric","label":"Metric","type":"text"},{"name":"value","label":"Value","type":"text"},{"name":"period","label":"Period","type":"text"}],
        ["generated","scheduled"])
    db.session.commit()

    # =====================================================================
    # SEED DATA for ALL entity types
    # =====================================================================

    seed_etype("department", [
        {"name":"Sales & Advisory","code":"SALES","head":"Mitesh Yadav","_status":"active"},
        {"name":"Travel Operations","code":"OPS","head":"Chaya Devi","_status":"active"},
        {"name":"Finance & Admin","code":"FIN","head":"Priya Sharma","_status":"active"},
    ])

    seed_etype("employee", [
        {"employee_name":"Mitesh Yadav","email":"mitesh@panchi.club","phone":"+91-9876543211","department":"Sales & Advisory","position":"Senior Travel Advisor","salary":850000,"date_of_joining":"2021-06-01","_status":"active"},
        {"employee_name":"Chaya Devi","email":"chaya@panchi.club","phone":"+91-9876543220","department":"Travel Operations","position":"Operations Manager","salary":750000,"date_of_joining":"2022-01-15","_status":"active"},
        {"employee_name":"Priya Sharma","email":"priya.fin@panchi.club","phone":"+91-9876543221","department":"Finance & Admin","position":"Finance Manager","salary":700000,"date_of_joining":"2023-03-01","_status":"active"},
        {"employee_name":"Vikram Singh","email":"vikram@panchi.club","phone":"+91-9876543222","department":"Sales & Advisory","position":"Travel Advisor","salary":650000,"date_of_joining":"2022-09-01","_status":"active"},
        {"employee_name":"Ananya Kapoor","email":"ananya@panchi.club","phone":"+91-9876543223","department":"Sales & Advisory","position":"Junior Travel Advisor","salary":400000,"date_of_joining":"2025-01-10","_status":"active"},
        {"employee_name":"Rajesh Kumar","email":"rajesh@panchi.club","phone":"+91-9876543224","department":"Finance & Admin","position":"Admin Executive","salary":350000,"date_of_joining":"2024-06-01","_status":"active"},
        {"employee_name":"Sneha Roy","email":"sneha@panchi.club","phone":"+91-9876543225","department":"Finance & Admin","position":"Marketing Coordinator","salary":450000,"date_of_joining":"2024-03-01","_status":"active"},
        {"employee_name":"Arjun Nair","email":"arjun@panchi.club","phone":"+91-9876543226","department":"Travel Operations","position":"Operations Executive","salary":500000,"date_of_joining":"2023-11-01","_status":"active"},
    ])

    seed_etype("leave_request", [
        {"employee_name":"Mitesh Yadav","leave_type":"annual","start_date":"2026-07-20","end_date":"2026-07-25","reason":"Family vacation to Goa","_status":"pending"},
        {"employee_name":"Chaya Devi","leave_type":"personal","start_date":"2026-07-15","end_date":"2026-07-15","reason":"Personal errand","_status":"approved"},
        {"employee_name":"Vikram Singh","leave_type":"sick","start_date":"2026-07-10","end_date":"2026-07-11","reason":"Fever and cold","_status":"approved"},
        {"employee_name":"Ananya Kapoor","leave_type":"casual","start_date":"2026-08-01","end_date":"2026-08-03","reason":"Weekend trip to Himachal","_status":"pending"},
        {"employee_name":"Rajesh Kumar","leave_type":"annual","start_date":"2026-07-28","end_date":"2026-08-02","reason":"Going home to village","_status":"pending"},
        {"employee_name":"Sneha Roy","leave_type":"sick","start_date":"2026-07-08","end_date":"2026-07-08","reason":"Doctor appointment","_status":"approved"},
    ])

    seed_etype("account", [
        {"account_name":"Infosys Ltd","industry":"technology","city":"Bangalore","annual_revenue":50000000,"_status":"active"},
        {"account_name":"Google India","industry":"technology","city":"Mumbai","annual_revenue":80000000,"_status":"active"},
        {"account_name":"Deloitte India","industry":"consulting","city":"Gurgaon","annual_revenue":35000000,"_status":"active"},
        {"account_name":"Wedding Concierge","industry":"events","city":"Jaipur","annual_revenue":15000000,"_status":"active"},
        {"account_name":"MakeMyTrip B2B","industry":"travel","city":"Gurgaon","annual_revenue":20000000,"_status":"active"},
    ])

    seed_etype("contact", [
        {"first_name":"Rahul","last_name":"Mehta","email":"rahul@infosys.com","phone":"+91-9876543301","account_name":"Infosys Ltd","job_title":"Travel Manager","_status":"active"},
        {"first_name":"Neha","last_name":"Kapoor","email":"neha@google.com","phone":"+91-9876543302","account_name":"Google India","job_title":"Events Head","_status":"active"},
        {"first_name":"Amit","last_name":"Verma","email":"amit@deloitte.com","phone":"+91-9876543303","account_name":"Deloitte India","job_title":"HR Director","_status":"active"},
        {"first_name":"Pooja","last_name":"Singh","email":"pooja@wedding.co","phone":"+91-9876543304","account_name":"Wedding Concierge","job_title":"Wedding Planner","_status":"active"},
        {"first_name":"Vijay","last_name":"Nair","email":"vijay@mmt.com","phone":"+91-9876543305","account_name":"MakeMyTrip B2B","job_title":"Partner Manager","_status":"active"},
    ])

    seed_etype("lead", [
        {"first_name":"Sneha","last_name":"Reddy","email":"sneha@reddy.co","phone":"+91-9876543231","company":"Self","lead_source":"website","lead_score":80,"_status":"new"},
        {"first_name":"Rahul","last_name":"Verma","email":"rahul@verma.in","phone":"+91-9876543232","company":"Infosys","lead_source":"referral","lead_score":92,"_status":"qualified"},
        {"first_name":"Karan","last_name":"Patel","email":"karan@patel.co","phone":"+91-9876543233","company":"Google","lead_source":"social_media","lead_score":75,"_status":"contacted"},
        {"first_name":"Meera","last_name":"Iyer","email":"meera@iyer.in","phone":"+91-9876543234","company":"Self","lead_source":"event","lead_score":65,"_status":"contacted"},
        {"first_name":"Deepak","last_name":"Joshi","email":"deepak@joshient.com","phone":"+91-9876543235","company":"Deloitte","lead_source":"cold_call","lead_score":50,"_status":"new"},
        {"first_name":"Arjun","last_name":"Verma","email":"arjun@vermacorp.com","phone":"+91-9876543237","company":"TechVentures","lead_source":"referral","lead_score":88,"_status":"qualified"},
        {"first_name":"Lakshmi","last_name":"Menon","email":"lakshmi@menon.co","phone":"+91-9876543238","company":"Self","lead_source":"website","lead_score":60,"_status":"new"},
        {"first_name":"Rohit","last_name":"Kumar","email":"rohit@kumartravels.in","phone":"+91-9876543239","company":"Kumar Travels","lead_source":"referral","lead_score":70,"_status":"contacted"},
        {"first_name":"Pooja","last_name":"Singh","email":"pooja@singh.in","phone":"+91-9876543240","company":"Wedding Concierge","lead_source":"event","lead_score":85,"_status":"qualified"},
        {"first_name":"Ravi","last_name":"Shastri","email":"ravi@shastri.com","phone":"+91-9876543241","company":"Self","lead_source":"website","lead_score":45,"_status":"new"},
    ])

    seed_etype("campaign", [
        {"name":"Summer Escape 2026","channel":"multi","budget":250000,"target":"10 new bookings","status":"active"},
        {"name":"Japan Explorer Launch","channel":"email","budget":150000,"target":"50 leads","status":"active"},
        {"name":"Family Holiday Special","channel":"whatsapp","budget":100000,"target":"20 enquiries","status":"paused"},
        {"name":"MICE Corporate Outreach","channel":"social","budget":300000,"target":"5 corporate accounts","status":"active"},
        {"name":"Honeymoon Package Promo","channel":"instagram","budget":80000,"target":"15 leads","status":"active"},
    ])

    seed_etype("ticket", [
        {"customer_name":"Rajat Nishesh","subject":"Japan trip — vegetarian restaurant recommendations","priority":"medium","assigned_to":"Mitesh Yadav","description":"Need help with vegetarian-friendly restaurants in Tokyo and Kyoto for family trip.","_status":"open"},
        {"customer_name":"Meera Iyer","subject":"Bali booking — date change request","priority":"high","assigned_to":"Vikram Singh","description":"Booked Bali in August, needs to move to September due to work.","_status":"open"},
        {"customer_name":"Karan Patel","subject":"Dubai visa status","priority":"medium","assigned_to":"Chaya Devi","description":"Applied for Dubai tourist visa 5 days ago, wants update.","_status":"in_progress"},
        {"customer_name":"Amit Sharma","subject":"Return delay compensation","priority":"low","assigned_to":"Priya Sharma","description":"Follow-up for the 4hr CDG return delay compensation.","_status":"in_progress"},
        {"customer_name":"Sneha Reddy","subject":"Kerala honeymoon package","priority":"high","assigned_to":"Mitesh Yadav","description":"5 nights Kerala honeymoon, luxury but under 1.5L budget.","_status":"new"},
        {"customer_name":"Rahul Verma","subject":"Referral discount not applied","priority":"medium","assigned_to":"Priya Sharma","description":"Referred by Amit Sharma but discount wasn't applied.","_status":"resolved"},
        {"customer_name":"Vikram Singh","subject":"Europe trip documents","priority":"low","assigned_to":"Arjun Nair","description":"Need to collect passport copies for visa processing.","_status":"new"},
    ])

    seed_etype("knowledge_article", [
        {"title":"Japan Travel Guide 2026","category":"destinations","content":"Essential guide for traveling to Japan: best seasons, cultural etiquette, transportation passes, and vegetarian food options.","_status":"published"},
        {"title":"Visa Requirements for UAE","category":"visa","content":"Complete guide to UAE tourist visa: documents needed, processing time, fees, and eligibility.","_status":"published"},
        {"title":"Packing Checklist for Family Trips","category":"tips","content":"Comprehensive packing list for families travelling internationally: documents, medicines, entertainment for kids.","_status":"published"},
        {"title":"Travel Insurance Guide","category":"policies","content":"Everything about travel insurance: what it covers, claim process, recommended providers.","_status":"published"},
        {"title":"Bali Travel Restrictions 2026","category":"destinations","content":"Current entry requirements, visa on arrival process, and local regulations for Bali.","_status":"published"},
    ])

    seed_etype("faq", [
        {"question":"What documents do I need for international travel?","answer":"Valid passport (6+ months validity), visa (if required), travel insurance, flight tickets, hotel confirmations, and any specific permits.","category":"documents","_status":"published"},
        {"question":"How early should I book flights for best prices?","answer":"Domestic: 4-6 weeks ahead. International: 3-4 months ahead. Peak season: book 6 months ahead.","category":"bookings","_status":"published"},
        {"question":"Can I modify my booking after confirmation?","answer":"Yes, modifications are possible subject to availability and supplier policies. Changes may incur fees.","category":"bookings","_status":"published"},
        {"question":"What is included in a Panchi Club package?","answer":"Our packages typically include flights, accommodation, transfers, activities as specified in the itinerary, and 24/7 support during travel.","category":"packages","_status":"published"},
        {"question":"How does the referral program work?","answer":"Refer a friend and both get 5% discount on your next trip. Referral credits are applied after the referred friend completes their trip.","category":"policies","_status":"published"},
    ])

    seed_etype("customer_feedback", [
        {"customer_name":"Rajat Nishesh","rating":5,"comments":"Absolutely wonderful trip to Thailand! The private transfer at midnight was so reassuring. Kids loved the houseboat.","_status":"actioned"},
        {"customer_name":"Amit Sharma","rating":4,"comments":"Europe trip was magical but the return flight delay was hard with kids. Trip content was 10/10.","_status":"reviewed"},
        {"customer_name":"Vikram Singh","rating":5,"comments":"Dubai trip was perfect. Everything was smooth. The suite upgrade made our anniversary special.","_status":"new"},
        {"customer_name":"Ananya Kapoor","rating":5,"comments":"First trip with Panchi Club and I'm impressed. The advisor understood exactly what I wanted.","_status":"new"},
    ])

    seed_etype("sla_policy", [
        {"name":"Standard Response SLA","response_time":"2 hours","resolution_time":"24 hours","_status":"active"},
        {"name":"Urgent Issue SLA","response_time":"30 minutes","resolution_time":"4 hours","_status":"active"},
    ])

    seed_etype("supplier", [
        {"company_name":"Taj Hotels","category":"hotel","contact_person":"Rajesh Mehta","phone":"+91-9876543101","_status":"active"},
        {"company_name":"Marriott International","category":"hotel","contact_person":"Anita Desai","phone":"+91-9876543102","_status":"active"},
        {"company_name":"Abercrombie & Kent India","category":"dmc","contact_person":"Vikram Singhania","phone":"+91-9876543103","_status":"active"},
        {"company_name":"SOTC Travel Services","category":"dmc","contact_person":"Priya Kapoor","phone":"+91-9876543104","_status":"active"},
        {"company_name":"Emirates Airlines","category":"airline","contact_person":"Corporate Desk","phone":"+91-9876543105","_status":"active"},
        {"company_name":"IndiGo Airlines","category":"airline","contact_person":"B2B Team","phone":"+91-9876543106","_status":"active"},
        {"company_name":"Savaari Car Rentals","category":"transport","contact_person":"Amit Agarwal","phone":"+91-9876543107","_status":"active"},
        {"company_name":"MakeMyTrip B2B","category":"dmc","contact_person":"Sales Team","phone":"+91-9876543108","_status":"active"},
        {"company_name":"Hyatt Hotels","category":"hotel","contact_person":"Priyanka Dey","phone":"+91-9876543109","_status":"active"},
        {"company_name":"Singapore Airlines","category":"airline","contact_person":"Corporate Sales","phone":"+91-9876543110","_status":"active"},
    ])

    seed_etype("product", [
        {"name":"Deluxe Hotel Night — Taj","category":"hotel","unit_price":15000,"supplier":"Taj Hotels","_status":"active"},
        {"name":"Standard Hotel Night — Marriott","category":"hotel","unit_price":8500,"supplier":"Marriott International","_status":"active"},
        {"name":"Domestic Flight — IndiGo","category":"flight","unit_price":6500,"supplier":"IndiGo Airlines","_status":"active"},
        {"name":"International Flight — Emirates","category":"flight","unit_price":45000,"supplier":"Emirates Airlines","_status":"active"},
        {"name":"Private Transfer (city)","category":"transfer","unit_price":2500,"supplier":"Savaari Car Rentals","_status":"active"},
        {"name":"Private Transfer (intercity)","category":"transfer","unit_price":8500,"supplier":"Savaari Car Rentals","_status":"active"},
        {"name":"Kerala Package — 5N/6D","category":"package","unit_price":45000,"supplier":"SOTC Travel Services","_status":"active"},
        {"name":"Dubai Package — 4N/5D","category":"package","unit_price":65000,"supplier":"Abercrombie & Kent India","_status":"active"},
        {"name":"Japan Package — 7N/8D","category":"package","unit_price":125000,"supplier":"Abercrombie & Kent India","_status":"active"},
        {"name":"Luxury Hotel Night — Hyatt","category":"hotel","unit_price":22000,"supplier":"Hyatt Hotels","_status":"active"},
        {"name":"Business Class — Singapore Airlines","category":"flight","unit_price":85000,"supplier":"Singapore Airlines","_status":"active"},
        {"name":"Visa Processing Service","category":"service","unit_price":5000,"supplier":"SOTC Travel Services","_status":"active"},
    ])

    seed_etype("purchase_order", [
        {"po_number":"PO-2026-001","supplier_name":"Taj Hotels","total_amount":450000,"order_date":"2026-06-01","notes":"Block booking for Q3 corporate clients","_status":"confirmed"},
        {"po_number":"PO-2026-002","supplier_name":"Emirates Airlines","total_amount":1200000,"order_date":"2026-06-10","notes":"Annual contract — corporate fares","_status":"sent"},
        {"po_number":"PO-2026-003","supplier_name":"Savaari Car Rentals","total_amount":85000,"order_date":"2026-06-15","notes":"Monthly transfer services","_status":"received"},
        {"po_number":"PO-2026-004","supplier_name":"Abercrombie & Kent India","total_amount":625000,"order_date":"2026-06-20","notes":"Japan tour packages — advance booking","_status":"draft"},
        {"po_number":"PO-2026-005","supplier_name":"IndiGo Airlines","total_amount":350000,"order_date":"2026-07-01","notes":"Domestic flight blocks for Kerala packages","_status":"sent"},
    ])

    seed_etype("warehouse", [
        {"name":"Delhi Operations Hub","location":"New Delhi, Aerocity","manager":"Arjun Nair","_status":"active"},
        {"name":"Mumbai Service Centre","location":"Mumbai, Andheri East","manager":"Chaya Devi","_status":"active"},
        {"name":"Goa Tourist Desk","location":"Goa, Calangute","manager":"Vikram Singh","_status":"active"},
    ])

    seed_etype("work_order", [
        {"title":"Airport pickup — Amit Sharma family","customer_name":"Amit Sharma","technician":"Rahul Driver","scheduled_date":"2026-07-15","description":"Nepal arrival transfer — 4 pax, 1 child seat required","_status":"scheduled"},
        {"title":"Hotel check-in assistance — Japan","customer_name":"Rajat Nishesh","technician":"Tokyo Concierge","scheduled_date":"2026-09-20","description":"Assist with check-in at Shinjuku hotel","_status":"pending"},
        {"title":"Desert safari coordination — Dubai","customer_name":"Priya Sharma","technician":"Desxpert Tours","scheduled_date":"2026-08-10","description":"Dune bashing + dinner booking for family of 3","_status":"scheduled"},
        {"title":"Visa document pickup — Karan","customer_name":"Karan Patel","technician":"Arjun Nair","scheduled_date":"2026-07-12","description":"Collect passport for Thailand visa processing","_status":"in_progress"},
        {"title":"Honeymoon setup — Kerala","customer_name":"Sneha Reddy","technician":"Resort Team","scheduled_date":"2026-08-01","description":"Honeymoon decoration coordination at Kumarakom","_status":"pending"},
        {"title":"Corporate event coordination — Infosys","customer_name":"Infosys Ltd","technician":"Mitesh Yadav","scheduled_date":"2026-08-15","description":"Team offsite coordination — 50 pax, 2 days","_status":"pending"},
    ])

    seed_etype("subcontractor", [
        {"company_name":"Rahul's Travel Services","specialty":"driver","phone":"+91-9876543401","rating":5,"_status":"active"},
        {"company_name":"Tokyo Concierge KK","specialty":"guide","phone":"+81-90-1234-5678","rating":5,"_status":"active"},
        {"company_name":"Desxpert Tours","specialty":"guide","phone":"+91-9876543402","rating":4,"_status":"active"},
        {"company_name":"LensCraft Photography","specialty":"photographer","phone":"+91-9876543403","rating":4,"_status":"active"},
        {"company_name":"Himalayan Hikes","specialty":"hiking","phone":"+91-9876543404","rating":5,"_status":"active"},
        {"company_name":"EventCraft Weddings","specialty":"events","phone":"+91-9876543405","rating":4,"_status":"on_project"},
    ])

    seed_etype("estimate", [
        {"project_name":"Infosys Corporate Offsite Goa","customer_name":"Infosys Ltd","total":850000,"valid_until":"2026-08-01","_status":"sent"},
        {"project_name":"Sharma Family Nepal Trip","customer_name":"Amit Sharma","total":350000,"valid_until":"2026-07-30","_status":"sent"},
        {"project_name":"Reddy Honeymoon Package","customer_name":"Sneha Reddy","total":145000,"valid_until":"2026-08-15","_status":"draft"},
        {"project_name":"Google India Team Retreat","customer_name":"Google India","total":1200000,"valid_until":"2026-09-01","_status":"draft"},
    ])

    seed_etype("contract", [
        {"title":"Hotel Partnership — Taj Group","party_b":"Taj Hotels","contract_type":"vendor","value":5000000,"start_date":"2025-01-01","_status":"active"},
        {"title":"DMC Agreement — A&K India","party_b":"Abercrombie & Kent India","contract_type":"vendor","value":3000000,"start_date":"2024-06-01","_status":"active"},
        {"title":"Airline Corporate Deal — Emirates","party_b":"Emirates Airline","contract_type":"vendor","value":8000000,"start_date":"2026-01-01","_status":"active"},
        {"title":"NDA — Supplier Rate Confidential","party_b":"Marriott International","contract_type":"nda","value":0,"start_date":"2025-03-01","_status":"active"},
        {"title":"Office Lease — Delhi HQ","party_b":"DLF Properties","contract_type":"lease","value":2400000,"start_date":"2024-04-01","_status":"expiring_soon"},
        {"title":"Preferred Partner — Singapore Airlines","party_b":"Singapore Airlines","contract_type":"vendor","value":6000000,"start_date":"2026-02-01","_status":"active"},
    ])

    seed_etype("document_template", [
        {"name":"Standard Booking Voucher","category":"voucher","_status":"active"},
        {"name":"Panchi Club Invoice Template","category":"invoice","_status":"active"},
        {"name":"Custom Itinerary Template","category":"itinerary","_status":"active"},
        {"name":"Client Proposal Template","category":"proposal","_status":"active"},
        {"name":"Visa Support Letter Template","category":"voucher","_status":"draft"},
    ])

    seed_etype("compliance_item", [
        {"regulation":"ISO 27001 Certification","category":"iso","due_date":"2026-12-31","assigned_to":"IT Team","_status":"in_progress"},
        {"regulation":"GDPR Compliance Audit","category":"gdpr","due_date":"2026-09-30","assigned_to":"DPO Office","_status":"pending"},
        {"regulation":"Workplace Safety Inspection","category":"safety","due_date":"2026-08-15","assigned_to":"Facilities","_status":"compliant"},
        {"regulation":"GST Filing — Q1 FY27","category":"tax","due_date":"2026-07-15","assigned_to":"Finance Dept","_status":"pending"},
        {"regulation":"Employee Labour Law Compliance","category":"labor","due_date":"2026-10-01","assigned_to":"HR","_status":"compliant"},
    ])

    seed_etype("quote", [
        {"quote_number":"Q-2026-001","account_name":"Infosys Ltd","total_amount":850000,"valid_until":"2026-08-01","_status":"sent"},
        {"quote_number":"Q-2026-002","account_name":"Amit Sharma","total_amount":350000,"valid_until":"2026-07-30","_status":"sent"},
        {"quote_number":"Q-2026-003","account_name":"Sneha Reddy","total_amount":145000,"valid_until":"2026-08-15","_status":"draft"},
        {"quote_number":"Q-2026-004","account_name":"Google India","total_amount":1200000,"valid_until":"2026-09-01","_status":"draft"},
        {"quote_number":"Q-2026-005","account_name":"Rajat Nishesh","total_amount":600000,"valid_until":"2026-09-20","_status":"draft"},
    ])

    seed_etype("target_list", [
        {"name":"Q3 Corporate Prospects","description":"Enterprise companies with >500 employees","list_type":"dynamic","_status":"active"},
        {"name":"Honeymoon Enquiries 2026","description":"All honeymoon enquiries for the year","list_type":"dynamic","_status":"active"},
        {"name":"Past Japan Travellers","description":"Customers who have previously travelled to Japan","list_type":"static","_status":"active"},
    ])

    seed_etype("social_post", [
        {"content":"Discover Japan this autumn! Cherry blossoms, sushi, and ancient temples await.","platform":"instagram","status":"published"},
        {"content":"Our family packages start at just ₹45,000. Perfect for your next getaway!","platform":"facebook","status":"published"},
        {"content":"Panchi Club is now offering exclusive corporate travel packages. DM for details.","platform":"linkedin","status":"published"},
        {"content":"Last chance for Summer Escape 2026 deals! Book by July 31.","platform":"instagram","status":"scheduled"},
        {"content":"Travel tip: Always carry a digital copy of your passport when travelling internationally.","platform":"twitter","status":"draft"},
    ])

    seed_etype("landing_page", [
        {"title":"Summer Escape 2026","url":"/landing/summer-2026","campaign":"Summer Escape 2026","conversions":12,"_status":"active"},
        {"title":"Japan Explorer","url":"/landing/japan-2026","campaign":"Japan Explorer Launch","conversions":5,"_status":"active"},
        {"title":"Family Holiday Special","url":"/landing/family-special","campaign":"Family Holiday Special","conversions":8,"_status":"active"},
    ])

    seed_etype("analytics_report", [
        {"name":"Monthly Booking Report","metric":"total_bookings","value":"48","period":"Jun 2026","_status":"generated"},
        {"name":"Lead Conversion Rate","metric":"conversion_rate","value":"32%","period":"Q2 2026","_status":"generated"},
        {"name":"Top Destinations","metric":"destination_popularity","value":"Dubai, Kerala, Japan","period":"2026 H1","_status":"generated"},
        {"name":"Revenue Forecast","metric":"forecasted_revenue","value":"85,00,000","period":"Q3 2026","_status":"scheduled"},
    ])

    seed_etype("invoice", [
        {"invoice_number":"INV-2026-001","customer_name":"Rajat Nishesh","amount":600000,"status":"pending","due_date":"2026-07-25","_status":"pending"},
        {"invoice_number":"INV-2026-002","customer_name":"Amit Sharma","amount":350000,"status":"paid","due_date":"2026-07-10","_status":"paid"},
        {"invoice_number":"INV-2026-003","customer_name":"Meera Iyer","amount":250000,"status":"overdue","due_date":"2026-06-30","_status":"overdue"},
        {"invoice_number":"INV-2026-004","customer_name":"Infosys Ltd","amount":1200000,"status":"pending","due_date":"2026-08-15","_status":"pending"},
        {"invoice_number":"INV-2026-005","customer_name":"Vikram Singh","amount":450000,"status":"paid","due_date":"2026-07-05","_status":"paid"},
        {"invoice_number":"INV-2026-006","customer_name":"Google India","amount":950000,"status":"pending","due_date":"2026-08-20","_status":"pending"},
        {"invoice_number":"INV-2026-007","customer_name":"Wedding Concierge","amount":280000,"status":"overdue","due_date":"2026-06-15","_status":"overdue"},
    ])

    seed_etype("payment", [
        {"customer_name":"Amit Sharma","amount":350000,"type":"received","gateway":"Razorpay","status":"completed"},
        {"customer_name":"Meera Iyer","amount":100000,"type":"received","gateway":"Razorpay","status":"completed"},
        {"customer_name":"Vikram Singh","amount":450000,"type":"received","gateway":"Bank Transfer","status":"completed"},
        {"customer_name":"Taj Hotels","amount":225000,"type":"sent","gateway":"NEFT","status":"completed"},
        {"customer_name":"Emirates Airlines","amount":600000,"type":"sent","gateway":"NEFT","status":"pending"},
        {"customer_name":"Savaari Rentals","amount":42500,"type":"sent","gateway":"NEFT","status":"completed"},
        {"customer_name":"Meera Iyer","amount":150000,"type":"received","gateway":"Razorpay","status":"pending"},
    ])

    seed_etype("project", [
        {"name":"Japan Product Launch","description":"Develop Japan travel packages — partner with A&K","start_date":"2026-06-01","end_date":"2026-08-31","priority":"high","department":"Sales & Advisory","_status":"active"},
        {"name":"Website Redesign","description":"Revamp Panchi Club website with new booking flow","start_date":"2026-05-01","end_date":"2026-09-30","priority":"critical","department":"All","_status":"active"},
        {"name":"Supplier Rate Negotiation 2027","description":"Renegotiate hotel and DMC rates for next FY","start_date":"2026-08-01","end_date":"2026-10-31","priority":"medium","department":"Finance & Admin","_status":"pending"},
        {"name":"Client Portal MVP","description":"Build client-facing portal for booking status view","start_date":"2026-04-01","end_date":"2026-07-15","priority":"high","department":"Travel Operations","_status":"active"},
        {"name":"Team Training — Japan Specialization","description":"Train advisors on Japan destinations","start_date":"2026-07-01","end_date":"2026-08-15","priority":"medium","department":"Sales & Advisory","_status":"active"},
        {"name":"CRM Migration Project","description":"Migrate legacy CRM data to Shunya OS","start_date":"2026-07-01","end_date":"2026-10-31","priority":"high","department":"All","_status":"active"},
    ])

    db.session.commit()

    # =====================================================================
    # SUMMARY
    # =====================================================================
    from sqlalchemy import func
    total_entities = db.session.query(func.count(Entity.id)).filter_by(tenant_id=tid).scalar()
    total_defs = db.session.query(func.count(EntityDefinition.id)).filter_by(tenant_id=tid).scalar()

    print(f"\n{'='*55}")
    print(f"✅ PANCHI CLUB — COMPLETE MODEL DEPLOYED")
    print(f"{'='*55}")
    print(f"Entity Types: {total_defs}")
    print(f"Total Records: {total_entities}")
    print(f"")
    print(f"Breakdown:")
    defs = db.session.query(EntityDefinition).filter_by(tenant_id=tid).order_by(EntityDefinition.type).all()
    for d in defs:
        cnt = db.session.query(func.count(Entity.id)).filter_by(tenant_id=tid, definition_id=d.id).scalar()
        if cnt > 0:
            print(f"  {d.icon} {d.type:25s} {cnt}")
    print(f"")
    print(f"All dashboards available at app.panchi.club")
    print(f"Login: admin@shunya.io / admin123")
