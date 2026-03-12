import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.db.session import engine
from app.db.models import Base

Base.metadata.create_all(engine)

if engine.dialect.name == "postgresql":
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS git_sha VARCHAR"))
        connection.execute(text("ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS config_version VARCHAR"))

table_names = ", ".join(sorted(Base.metadata.tables.keys()))
print(f"Tables created: {table_names}")
