import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.bootstrap import ensure_tables

table_names = ensure_tables()
print(f"Tables created: {table_names}")
