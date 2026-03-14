from PIL import Image, ImageDraw, ImageFilter

def create_hexagon(size, color):
    # Create a larger image for anti-aliasing
    scale = 4
    img_size = (size * scale, size * scale)
    img = Image.new("RGBA", img_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Hexagon points
    w, h = img_size
    # Center
    cx, cy = w // 2, h // 2
    # Radius
    r = min(w, h) // 2 - 10
    
    import math
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.radians(angle_deg)
        x = cx + r * math.cos(angle_rad)
        y = cy + r * math.sin(angle_rad)
        points.append((x, y))
        
    # Draw Hexagon
    draw.polygon(points, outline=color, width=15)
    
    # Draw Inner V
    v_points = [
        (cx - r//2, cy - r//2),
        (cx, cy + r//2),
        (cx + r//2, cy - r//2)
    ]
    draw.line(v_points, fill="white", width=20, joint="curve")
    
    # Resize down
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    return img

# Create the icon
icon_image = create_hexagon(256, "#00f3ff")

# Save as ICO (containing multiple sizes)
icon_image.save("vox_ops.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

print("Icon created: vox_ops.ico")
