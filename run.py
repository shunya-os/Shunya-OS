from app import create_app
from app.monitoring import init_monitoring
app = create_app()
init_monitoring(app)
if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
