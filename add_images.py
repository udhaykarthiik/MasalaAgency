# add_images.py
import os
import shutil
from pathlib import Path

# Create images directory if it doesn't exist
images_dir = Path('static/images')
images_dir.mkdir(parents=True, exist_ok=True)

# List of expected images
expected_images = [
    'everest-chicken.jpg',
    'mdh-chicken.jpg',
    'badshah-chicken.jpg',
    'shan-chicken.jpg',
    'everest-garam.jpg',
    'mdh-garam.jpg',
    'badshah-garam.jpg',
    'everest-meat.jpg',
    'mdh-meat.jpg',
    'everest-kitchen.jpg'
]

print(f"✅ Images directory: {images_dir.absolute()}")
print("Expected images:", expected_images)

# Check what's actually there
existing_images = list(images_dir.glob('*.jpg'))
print(f"\nFound {len(existing_images)} images:")
for img in existing_images:
    print(f"  - {img.name}")

# Create a .gitkeep file to ensure folder is tracked
gitkeep = images_dir / '.gitkeep'
gitkeep.touch()
print(f"\n✅ Created {gitkeep}")