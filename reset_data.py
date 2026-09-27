import os
import glob

# Folders to clean
folders = ['raw', 'confirmed', 'ranked']

print("Resetting all system data...")

for folder in folders:
    if os.path.exists(folder):
        files = glob.glob(os.path.join(folder, '*.json'))
        for file in files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"Error removing {file}: {e}")
        print(f"Cleared {len(files)} files from {folder}/")
    else:
        print(f"Folder {folder}/ does not exist, skipping.")

print("\nSystem data successfully reset! The dashboard will now be empty.")
print("To generate new data for the demo, run:")
print("python demo_verification.py")
