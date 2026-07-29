import os
from app import create_app
app = create_app()
if __name__=='__main__':
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')),debug=debug)