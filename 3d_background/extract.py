import json
import os

with open("strands.json", "r") as f:
    d = json.load(f)

os.makedirs("src/components/Strands", exist_ok=True)
for file_data in d["files"]:
    name = file_data.get("name") or file_data.get("path")
    # if it's a relative path like something/file.js, get the basename
    name = os.path.basename(name)
    content = file_data["content"]
    with open(os.path.join("src/components/Strands", name), "w") as out:
        out.write(content)

print("Files created.")
