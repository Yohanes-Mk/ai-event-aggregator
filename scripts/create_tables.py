import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import engine
from app.db.models import Base

Base.metadata.create_all(engine)
print("Tables created: youtube_videos, events, digests")
