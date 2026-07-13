from app import create_app

app = create_app()
print('App created successfully')
print('Template loaders:', [l.searchpath for l in app.jinja_loader.loaders])
print('Static folder:', app.static_folder)