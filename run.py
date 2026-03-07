# run.py
#!/usr/bin/env python3
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Para desarrollo con HTTPS (recomendado)
    # app.run(ssl_context='adhoc', host='0.0.0.0', port=5000, debug=True)
    
    # Para desarrollo sin HTTPS (solo pruebas locales)
    app.run(host='0.0.0.0', port=5000, debug=True)