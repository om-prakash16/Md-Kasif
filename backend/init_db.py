from app.database import engine
from app import models_db

print('Creating database tables...')
models_db.Base.metadata.create_all(bind=engine)
print('Tables created successfully!')
