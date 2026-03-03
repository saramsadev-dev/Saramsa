import json
import os

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api-registry.json")

with open(REGISTRY_PATH) as f:
    reg = json.load(f)

seen = set()
deduped = []
for ep in reg["endpoints"]:
    key = f"{ep['method']} {ep['path']}"
    if key not in seen:
        seen.add(key)
        deduped.append(ep)

removed = len(reg["endpoints"]) - len(deduped)
reg["endpoints"] = deduped

with open(REGISTRY_PATH, "w") as f:
    json.dump(reg, f, indent=2)
    f.write("\n")

print(f"Removed {removed} duplicates. {len(deduped)} endpoints remain.")
