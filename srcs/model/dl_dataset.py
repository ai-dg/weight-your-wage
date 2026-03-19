import kagglehub
import shutil
import os

# 1. Download the latest version of the 2025 Stack Overflow Survey
print("Downloading dataset from Kaggle...")
tmp_path = kagglehub.dataset_download("edoardogalli/stack-overflow-annual-developer-survey-2025")

# 2. Define your local target folder
target_folder = "srcs/model/datasets"

# 3. Create the folder if it doesn't exist
if not os.path.exists(target_folder):
    os.makedirs(target_folder)
    print(f"Created directory: {target_folder}")

# 4. Move files from the cache to your local folder
print(f"Moving files to ./{target_folder}...")
files = os.listdir(tmp_path)

for file_name in files:
    source = os.path.join(tmp_path, file_name)
    destination = os.path.join(target_folder, file_name)
    
    # Using move (or copy if you want to keep the cache version)
    if os.path.isdir(source):
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)

print("✅ Done! Your data is ready in the 'dataset' folder.")