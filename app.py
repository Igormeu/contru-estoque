import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from database import init_db, SessionLocal, Product
from seed_data import populate_database
from routes.api_routes import api_bp
from routes.pdv_routes import pdv_bp
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "contru-estoque-secret-key-2026")

    try:
        init_db()
        db = SessionLocal()
        if db.query(Product).count() == 0:
            print("Base vazia detectada. Populando dados demonstrativos...")
            populate_database()
        db.close()
    except Exception as e:
        print(f"Aviso durante inicialização do banco: {e}")

    # Registra Blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(pdv_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
        return response

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health():
        return jsonify({
            "status": "healthy",
            "system": "CONTRU ESTOQUE",
            "version": "2.1.0-auth-admin",
            "database": "Supabase/PostgreSQL ready"
        })

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Iniciando CONTRU ESTOQUE na porta {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
