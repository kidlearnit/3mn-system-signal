import os

def load_config(app):
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
    app.config['REDIS_URL'] = os.getenv('REDIS_URL')
    app.config['TG_TOKEN'] = os.getenv('TG_TOKEN')
    app.config['TG_CHAT_ID'] = os.getenv('TG_CHAT_ID')
    app.config['TIMEZONE'] = os.getenv('TIMEZONE', 'Asia/Ho_Chi_Minh')
    
    # Dashboard configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['TEMPLATES_AUTO_RELOAD'] = True