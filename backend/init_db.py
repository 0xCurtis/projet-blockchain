from app import create_app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        from models import db

        db.create_all()
        print("Database initialized successfully!")
