"""AI Capability Validation Test Script for SHUNYA OS Intelligence Runtime."""
import os, json, sys

os.environ['DATABASE_URL'] = 'postgresql://shunya:shunya_os_2024@127.0.0.1:5433/shunya_db'
os.environ['SECRET_KEY'] = 'shunya-club-secret-key-2024'
os.environ['FLASK_ENV'] = 'production'
os.environ['DISABLE_RATE_LIMIT'] = 'true'

project_dir = '/home/shunya-deploy/shunya_os'
sys.path.insert(0, project_dir)
os.chdir(project_dir)

from app import create_app, db
app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL']})

with app.app_context():
    from core.intelligence_runtime.integration import ask, ensure_runtime, health, get_history, store_memory, suggest, navigate
    ensure_runtime()
    
    session_id = "validation_test_session"
    
    results = []
    
    def test(name, query, **kwargs):
        result = ask(query=query, session_id=session_id, **kwargs)
        trace = result.get('trace', {})
        intent = trace.get('intent', {})
        strategy = trace.get('strategy', 'unknown')
        confidence = trace.get('confidence', 0)
        evidence_sources = [e.get('source') for e in trace.get('evidence', [])]
        content = result.get('content', '')
        actions = result.get('actions', [])
        results.append({
            'test': name,
            'query': query,
            'intent_category': intent.get('category'),
            'strategy': strategy,
            'confidence': confidence,
            'evidence_sources': evidence_sources,
            'content_preview': content[:200],
            'latency_ms': result.get('latency_ms', 0),
            'actions': [a.get('description') for a in actions],
            'requires_clarification': result.get('requires_clarification', False),
        })
        print(f"[{name:20s}] intent={intent.get('category'):12s} strategy={strategy:15s} conf={confidence:.2f} evidence={evidence_sources} latency={result.get('latency_ms')}ms")
        print(f"  Response: {content[:120]}...")
        print()
    
    # ============================================================
    # TEST 1: Health Check
    # ============================================================
    print("=" * 70)
    print("TEST 1: Health Check")
    print("=" * 70)
    h = health()
    print(f"Status: {h['status']}")
    print(f"Memory: {h['memory_count']}")
    print(f"Sessions: {h['active_sessions']}")
    print(f"Initialized: {h['initialized']}")
    print(f"Telemetry: {json.dumps(h.get('telemetry', {}), indent=2)}")
    print()
    
    # ============================================================
    # TEST 2: Company Context Understanding
    # ============================================================
    print("=" * 70)
    print("TEST 2: Company Context Understanding")
    print("=" * 70)
    test("Org Name", "What is the name of my organization?")
    test("Dept List", "What departments do we have?")
    test("Members", "Who are our team members?")
    test("Key People", "Who are the directors?")
    test("Founder Info", "Who is the founder of XYZ Company?")
    
    # ============================================================
    # TEST 3: User Identity & Role
    # ============================================================
    print("=" * 70)
    print("TEST 3: User Identity & Role Awareness")
    print("=" * 70)
    test("Who Am I", "Who am I?")
    test("My Role", "What is my role in the organization?")
    test("My Permissions", "What can I do in this system?")
    
    # ============================================================
    # TEST 4: Conversation Continuity
    # ============================================================
    print("=" * 70)
    print("TEST 4: Conversation Continuity")
    print("=" * 70)
    test("Turn 1", "What are our open tasks?")
    test("Turn 2", "Can you tell me more about the first one?")
    test("Turn 3", "What about the second one?")
    test("Context Check", "What were we just talking about?")
    
    # ============================================================
    # TEST 5: Business Data Explanation
    # ============================================================
    print("=" * 70)
    print("TEST 5: Business Data Explanation")
    print("=" * 70)
    test("Explain Data", "Can you explain our sales data?")
    test("Trend Analysis", "What are our business trends?")
    
    # ============================================================
    # TEST 6: Recommendations
    # ============================================================
    print("=" * 70)
    print("TEST 6: Recommendations")
    print("=" * 70)
    test("Suggest Action", "What should I do next?")
    test("Recommend", "Can you recommend some actions for the Sales team?")
    
    # ============================================================
    # TEST 7: Q&A
    # ============================================================
    print("=" * 70)
    print("TEST 7: Q&A")
    print("=" * 70)
    test("General Q", "What is a professional services firm?")
    test("Business Q", "How can we improve our sales process?")
    
    # ============================================================
    # TEST 8: Summarize Work
    # ============================================================
    print("=" * 70)
    print("TEST 8: Summarize Work")
    print("=" * 70)
    test("Summary", "Summarize what we've discussed so far.")
    
    # ============================================================
    # TEST 9: Planning Assistance
    # ============================================================
    print("=" * 70)
    print("TEST 9: Planning Assistance")
    print("=" * 70)
    test("Plan", "Create a plan for launching a new product")
    test("Task List", "List the steps for onboarding a new client")
    
    # ============================================================
    # TEST 10: Document Generation
    # ============================================================
    print("=" * 70)
    print("TEST 10: Document Generation")
    print("=" * 70)
    test("Generate Doc", "Generate a meeting agenda for our weekly sales review")
    test("Write Email", "Draft an email to the team about quarterly goals")
    
    # ============================================================
    # TEST 11: Internet Intelligence
    # ============================================================
    print("=" * 70)
    print("TEST 11: Internet Intelligence")
    print("=" * 70)
    test("Industry News", "What are the latest trends in professional services?")
    test("Competitor Intel", "Who are our competitors in the professional services space?")
    test("Regulations", "What regulations apply to professional services firms?")
    test("General Knowledge", "What is the difference between a manager and a director?")
    
    # ============================================================
    # TEST 12: Source Attribution
    # ============================================================
    print("=" * 70)
    print("TEST 12: Source Attribution & Distinction")
    print("=" * 70)
    test("Source Distinction", "Explain how you distinguish between organizational knowledge, internet knowledge, reasoning, and assumptions")

    # ============================================================
    # TEST 13: Conversation History
    # ============================================================
    print("=" * 70)
    print("TEST 13: Conversation History")
    print("=" * 70)
    history = get_history(session_id, 20)
    print(f"History entries: {len(history)}")
    for i, msg in enumerate(history):
        print(f"  [{i}] {msg.get('role'):10s}: {msg.get('content')[:80]}...")
    
    # ============================================================
    # TEST 14: Suggestions
    # ============================================================
    print("=" * 70)
    print("TEST 14: Suggestions")
    print("=" * 70)
    try:
        suggs = suggest(session_id=session_id, module_key="")
        print(f"Suggestions: {len(suggs)}")
        for s in suggs:
            print(f"  - {s.get('title')}: {s.get('description')[:100]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # ============================================================
    # TEST 15: Navigation Context
    # ============================================================
    print("=" * 70)
    print("TEST 15: Navigation Context Continuity")
    print("=" * 70)
    nav = navigate(session_id=session_id, workspace="sales", module="", object_type="lead", object_id="")
    print(f"Navigation: {json.dumps(nav, indent=2)}")
    test("Post-Nav Q", "What leads are in my pipeline?")
    
    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    print("\n" + "=" * 70)
    print("FINAL SUMMARY - AI CAPABILITY VALIDATION")
    print("=" * 70)
    print(f"\nTotal tests run: {len(results)}")
    passed = sum(1 for r in results if r['confidence'] > 0)
    print(f"Tests with confidence > 0: {passed}/{len(results)}")
    print(f"\nDetailed Results:")
    print(f"{'Test Name':22s} {'Intent':12s} {'Strategy':15s} {'Conf':6s} {'Evidence':25s} {'Latency':8s}")
    print("-" * 90)
    for r in results:
        print(f"{r['test']:22s} {r['intent_category']:12s} {r['strategy']:15s} {r['confidence']:.2f}  {str(r['evidence_sources']):25s} {r['latency_ms']}ms")

    # Save results to file
    output = {
        'health_check': {'status': h['status'], 'sessions': h['active_sessions'], 'memory': h['memory_count']},
        'tests': results,
        'summary': {'total': len(results), 'with_confidence': passed}
    }
    os.makedirs('/home/shunya-deploy/shunya_os/test_results', exist_ok=True)
    with open('/home/shunya-deploy/shunya_os/test_results/validation_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to test_results/validation_results.json")