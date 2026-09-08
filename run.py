from app import app
import os

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"==================================================")
    print(f"       CONTRU ESTOQUE - SERVIDOR INICIADO         ")
    print(f"   Acesse no navegador: http://localhost:{port}   ")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
