from app import create_app
app = create_app()
with app.test_client() as c:
    r = c.get('/')
    print('GET / status', r.status_code)
    print('Location:', r.headers.get('Location'))
    print('Body head:', r.data.decode('utf-8', 'ignore')[:200])

    r2 = c.post('/leads/new', data={
        'customer_name': 'Nishesh',
        'destination': 'Kashmir',
        'pax': '3 adults',
        'dates': '10-08-2025',
        'source': 'manual',
        'status': 'new'
    }, follow_redirects=True)
    print('POST /leads/new status', r2.status_code)
    body = r2.data.decode('utf-8', 'ignore')
    print('Has PC code:', 'PC' in body)
    print('Body head:', body[:300])
