from pathlib import Path

from app.integrations.synthetic import atlas_feed, meridian_feed

root = Path(__file__).resolve().parents[1] / "fixtures"
(root / "atlaspm" / "snapshot.csv").write_bytes(atlas_feed())
(root / "meridianrent" / "events.json").write_bytes(meridian_feed())
print("Generated deterministic synthetic CSV/JSON fixtures")
