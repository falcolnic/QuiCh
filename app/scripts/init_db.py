import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.database import init_db

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
