import os
import json

input_dir = "data/raw"
output_dir = "data/processed"
output_file = os.path.join(output_dir, "combined.json")

all_data = []

# Loop through all JSON files
for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        file_path = os.path.join(input_dir, filename)
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # If file contains a list → extend
            if isinstance(data, list):
                all_data.extend(data)
            else:
                all_data.append(data)

# Create output directory if not exists
os.makedirs(output_dir, exist_ok=True)

# Save combined file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print("✅ Combined JSON saved to:", output_file)