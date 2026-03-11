from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# المسار الافتراضي لقاعدة البيانات على الديسك
DEFAULT_DB_PATH = "/opt/render/project/src/data/srca.db"

# استخدام المتغير البيئي إذا كان موجوداً، وإلا استخدام مسار الديسك
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# التأكد من وجود المجلد لقاعدة البيانات
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()