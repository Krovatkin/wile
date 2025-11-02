#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

# Create test images
colors = [
    ('red', (220, 53, 69)),
    ('blue', (13, 110, 253)),
    ('green', (25, 135, 84)),
    ('orange', (253, 126, 20)),
    ('purple', (111, 66, 193)),
    ('teal', (32, 201, 151))
]

output_dir = 'tmp_test'
os.makedirs(output_dir, exist_ok=True)

for i, (name, color) in enumerate(colors, 1):
    # Create image
    img = Image.new('RGB', (800, 600), color=color)
    draw = ImageDraw.Draw(img)

    # Add text
    text = f"Image {i}\n({name})"

    # Try to use a larger font, fall back to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
    except:
        font = ImageFont.load_default()

    # Get text bounding box to center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = ((800 - text_width) // 2, (600 - text_height) // 2)

    # Draw white text with black outline for visibility
    outline_color = (0, 0, 0)
    text_color = (255, 255, 255)

    # Draw outline
    for adj_x in range(-2, 3):
        for adj_y in range(-2, 3):
            draw.text((position[0]+adj_x, position[1]+adj_y), text, font=font, fill=outline_color)

    # Draw main text
    draw.text(position, text, font=font, fill=text_color)

    # Save
    filename = os.path.join(output_dir, f'test_image_{i}.png')
    img.save(filename)
    print(f'✓ Created {filename} ({name})')

print(f'\n✓ Successfully created {len(colors)} test images in {output_dir}/')
