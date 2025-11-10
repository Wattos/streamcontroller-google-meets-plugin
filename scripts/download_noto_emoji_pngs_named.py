import os
import requests
import cairosvg

# Map emojis to friendly names
emoji_names = {
    "💖": "sparkling_heart",
    "👍": "thumbs_up",
    "🎉": "celebrate",
    "👏": "applause",
    "😂": "laugh",
    "😮": "surprised",
    "😢": "sad",
    "🤔": "thinking",
    "👎": "thumbs_down",
    "✅": "success",
    "❌": "failure",
}

# Output directories
svg_dir = "tmp_svg"
png_dir = "reactions"
os.makedirs(svg_dir, exist_ok=True)
os.makedirs(png_dir, exist_ok=True)

# Base URL for SVGs from Noto Emoji repo
base_url = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/svg/emoji_u{}.svg"

for emoji in emoji_names.keys():
    codepoints = "-".join(f"{ord(c):x}" for c in emoji)
    svg_url = base_url.format(codepoints)
    svg_path = os.path.join(svg_dir, f"{emoji_names[emoji]}.svg")
    png_path = os.path.join(png_dir, f"{emoji_names[emoji]}.png")

    # Download SVG
    response = requests.get(svg_url)
    if response.status_code == 200:
        with open(svg_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded {emoji} SVG ({emoji_names[emoji]})")

        # Render as 96×96 PNG
        cairosvg.svg2png(url=svg_url, write_to=png_path, output_width=96, output_height=96)
        print(f"🎨 Rendered {emoji} -> {png_path}")

        # Delete SVG file to save space
        os.remove(svg_path)
    else:
        print(f"❌ Could not find {emoji} ({response.status_code})")

print("All done!")
