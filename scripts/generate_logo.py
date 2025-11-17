#!/usr/bin/env python3
"""
Generate Career Navigator logo.

Creates multiple logo sizes and formats for different use cases.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path


def create_logo(size=(512, 512), output_path=None):
    """
    Create Career Navigator logo.
    
    Args:
        size: Tuple of (width, height) for logo size
        output_path: Path to save the logo (default: logo_{size[0]}x{size[1]}.png)
    """
    width, height = size
    
    # Create image with transparent background
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Color scheme - Professional blue and orange
    primary_blue = (41, 98, 255)  # #2962FF
    accent_orange = (255, 152, 0)  # #FF9800
    dark_blue = (25, 60, 155)  # #193C9B
    white = (255, 255, 255)
    
    # Calculate center and dimensions
    center_x, center_y = width // 2, height // 2
    logo_size = min(width, height) * 0.7
    
    # Draw compass/compass rose (representing navigation)
    # Outer circle
    outer_radius = logo_size * 0.4
    draw.ellipse(
        [
            center_x - outer_radius,
            center_y - outer_radius,
            center_x + outer_radius,
            center_y + outer_radius
        ],
        fill=primary_blue,
        outline=dark_blue,
        width=int(logo_size * 0.02)
    )
    
    # Inner circle
    inner_radius = outer_radius * 0.6
    draw.ellipse(
        [
            center_x - inner_radius,
            center_y - inner_radius,
            center_x + inner_radius,
            center_y + inner_radius
        ],
        fill=white,
        outline=primary_blue,
        width=int(logo_size * 0.015)
    )
    
    # Draw compass needle/arrow pointing up (representing upward career growth)
    arrow_size = inner_radius * 0.7
    
    # North arrow (pointing up)
    arrow_points = [
        (center_x, center_y - arrow_size),  # Top point
        (center_x - arrow_size * 0.3, center_y - arrow_size * 0.3),  # Left
        (center_x - arrow_size * 0.15, center_y - arrow_size * 0.15),  # Left inner
        (center_x - arrow_size * 0.15, center_y + arrow_size * 0.2),  # Left bottom
        (center_x + arrow_size * 0.15, center_y + arrow_size * 0.2),  # Right bottom
        (center_x + arrow_size * 0.15, center_y - arrow_size * 0.15),  # Right inner
        (center_x + arrow_size * 0.3, center_y - arrow_size * 0.3),  # Right
    ]
    draw.polygon(arrow_points, fill=accent_orange, outline=dark_blue, width=int(logo_size * 0.01))
    
    # Draw cardinal directions (N, S, E, W) - simplified
    direction_size = outer_radius * 0.15
    # North
    draw.text(
        (center_x - direction_size * 0.3, center_y - outer_radius - direction_size * 0.5),
        "N",
        fill=dark_blue,
        font=None  # Will use default
    )
    
    # Add small dots for other directions
    dot_radius = logo_size * 0.02
    # East
    draw.ellipse(
        [
            center_x + outer_radius - dot_radius,
            center_y - dot_radius,
            center_x + outer_radius + dot_radius,
            center_y + dot_radius
        ],
        fill=dark_blue
    )
    # West
    draw.ellipse(
        [
            center_x - outer_radius - dot_radius,
            center_y - dot_radius,
            center_x - outer_radius + dot_radius,
            center_y + dot_radius
        ],
        fill=dark_blue
    )
    # South
    draw.ellipse(
        [
            center_x - dot_radius,
            center_y + outer_radius - dot_radius,
            center_x + dot_radius,
            center_y + outer_radius + dot_radius
        ],
        fill=dark_blue
    )
    
    # Add text "CN" or "Career Navigator" below if space allows
    if height > 400:
        try:
            # Try to load a nice font
            font_size = int(height * 0.12)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            text = "Career Navigator"
            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Draw text below logo
            text_y = center_y + outer_radius + logo_size * 0.1
            text_x = center_x - text_width // 2
            
            # Draw text shadow for better visibility
            draw.text(
                (text_x + 2, text_y + 2),
                text,
                fill=(0, 0, 0, 100),
                font=font
            )
            draw.text(
                (text_x, text_y),
                text,
                fill=dark_blue,
                font=font
            )
        except Exception:
            pass
    
    # Save image
    if output_path is None:
        output_path = f"logo_{width}x{height}.png"
    
    img.save(output_path, "PNG")
    print(f"✓ Created logo: {output_path}")
    
    return img


def create_icon(size=(256, 256), output_path=None):
    """
    Create a simplified icon version (without text).
    
    Args:
        size: Tuple of (width, height) for icon size
        output_path: Path to save the icon
    """
    width, height = size
    
    # Create image with transparent background
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Color scheme
    primary_blue = (41, 98, 255)
    accent_orange = (255, 152, 0)
    dark_blue = (25, 60, 155)
    white = (255, 255, 255)
    
    center_x, center_y = width // 2, height // 2
    logo_size = min(width, height) * 0.8
    
    # Simplified compass icon
    outer_radius = logo_size * 0.45
    draw.ellipse(
        [
            center_x - outer_radius,
            center_y - outer_radius,
            center_x + outer_radius,
            center_y + outer_radius
        ],
        fill=primary_blue,
        outline=dark_blue,
        width=int(logo_size * 0.03)
    )
    
    inner_radius = outer_radius * 0.65
    draw.ellipse(
        [
            center_x - inner_radius,
            center_y - inner_radius,
            center_x + inner_radius,
            center_y + inner_radius
        ],
        fill=white,
        outline=primary_blue,
        width=int(logo_size * 0.02)
    )
    
    # Arrow pointing up
    arrow_size = inner_radius * 0.75
    arrow_points = [
        (center_x, center_y - arrow_size),
        (center_x - arrow_size * 0.35, center_y - arrow_size * 0.35),
        (center_x - arrow_size * 0.2, center_y - arrow_size * 0.2),
        (center_x - arrow_size * 0.2, center_y + arrow_size * 0.25),
        (center_x + arrow_size * 0.2, center_y + arrow_size * 0.25),
        (center_x + arrow_size * 0.2, center_y - arrow_size * 0.2),
        (center_x + arrow_size * 0.35, center_y - arrow_size * 0.35),
    ]
    draw.polygon(arrow_points, fill=accent_orange, outline=dark_blue, width=int(logo_size * 0.015))
    
    if output_path is None:
        output_path = f"icon_{width}x{height}.png"
    
    img.save(output_path, "PNG")
    print(f"✓ Created icon: {output_path}")
    
    return img


def create_favicon(output_path="favicon.ico"):
    """Create favicon (16x16, 32x32, 48x48 sizes)."""
    sizes = [(16, 16), (32, 32), (48, 48)]
    images = []
    
    for size in sizes:
        img = create_icon(size)
        images.append(img)
    
    # Save as ICO (multi-size)
    images[0].save(
        output_path,
        format="ICO",
        sizes=[(s[0], s[1]) for s in sizes]
    )
    print(f"✓ Created favicon: {output_path}")


def main():
    """Generate all logo variants."""
    # Create output directory
    output_dir = Path("assets/logo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎨 Generating Career Navigator logos...\n")
    
    # Generate different sizes
    sizes = [
        (512, 512, "logo_512.png"),
        (256, 256, "logo_256.png"),
        (128, 128, "logo_128.png"),
        (64, 64, "logo_64.png"),
    ]
    
    for width, height, filename in sizes:
        create_logo((width, height), output_dir / filename)
    
    # Generate icon versions
    icon_sizes = [
        (256, 256, "icon_256.png"),
        (128, 128, "icon_128.png"),
        (64, 64, "icon_64.png"),
        (32, 32, "icon_32.png"),
    ]
    
    for width, height, filename in icon_sizes:
        create_icon((width, height), output_dir / filename)
    
    # Generate favicon
    create_favicon(output_dir / "favicon.ico")
    
    # Generate square logo for app stores, etc.
    create_logo((1024, 1024), output_dir / "logo_1024.png")
    
    print(f"\n✅ All logos generated in {output_dir}/")
    print("\nLogo files:")
    for file in sorted(output_dir.glob("*.png")):
        print(f"  - {file.name}")
    if (output_dir / "favicon.ico").exists():
        print(f"  - favicon.ico")


if __name__ == "__main__":
    main()

