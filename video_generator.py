import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
FPS = 20
SECONDS_PER_SCENE = 4


def load_font(size):
    """Load a readable font, with a fallback if Arial is unavailable."""
    font_paths = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)

    return ImageFont.load_default()


def build_script(data):
    """Create promotional text using only supplied property details."""
    features = data.get("key_features", "").strip()
    description = data.get("description", "").strip()
    cta = data.get("contact_cta", "").strip()

    lines = [
        f"Discover {data['property_name']}",
        f"Located in {data['location']}",
        f"{data['property_type']} | Price: {data['price']}",
        f"Features: {features}",
    ]

    if description:
        lines.append(description)

    lines.append(cta)

    return "\n\n".join(lines)


def fit_image(image_path):
    """Resize and crop an image to the video dimensions."""
    with Image.open(image_path) as source:
        image = source.convert("RGB")

    image_ratio = image.width / image.height
    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT

    if image_ratio > target_ratio:
        new_height = VIDEO_HEIGHT
        new_width = int(new_height * image_ratio)
    else:
        new_width = VIDEO_WIDTH
        new_height = int(new_width / image_ratio)

    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    left = (new_width - VIDEO_WIDTH) // 2
    top = (new_height - VIDEO_HEIGHT) // 2

    return image.crop((
        left,
        top,
        left + VIDEO_WIDTH,
        top + VIDEO_HEIGHT
    ))


def make_frame(image_path, data, caption, scene_index, total_scenes):
    """Create a scene with a property photo and readable text overlays."""
    image = fit_image(image_path)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Dark footer improves text readability.
    footer_top = 490
    draw.rectangle(
        (0, footer_top, VIDEO_WIDTH, VIDEO_HEIGHT),
        fill=(0, 0, 0, 190)
    )

    title_font = load_font(40)
    body_font = load_font(28)
    small_font = load_font(22)

    draw.text(
        (50, footer_top + 25),
        data["property_name"],
        font=title_font,
        fill="white"
    )

    draw.text(
        (50, footer_top + 88),
        caption,
        font=body_font,
        fill="white"
    )

    draw.text(
        (50, footer_top + 145),
        f"{data['location']}  |  {data['price']}",
        font=small_font,
        fill="white"
    )

    draw.text(
        (VIDEO_WIDTH - 180, 30),
        f"{scene_index + 1}/{total_scenes}",
        font=small_font,
        fill="white"
    )

    return Image.alpha_composite(
        image.convert("RGBA"), overlay
    ).convert("RGB")


def generate_video(data, image_paths, output_path):
    """Validate inputs and generate a promotional MP4 video."""
    if not image_paths:
        raise ValueError("Please provide property images.")

    if not data.get("property_name", "").strip():
        raise ValueError("Property name is required.")

    if not data.get("location", "").strip():
        raise ValueError("Property location is required.")

    if not data.get("price", "").strip():
        raise ValueError("Property price is required.")

    valid_images = []

    for image_path in image_paths:
        try:
            with Image.open(image_path) as image:
                image.verify()
            valid_images.append(image_path)
        except Exception:
            continue

    if not valid_images:
        raise ValueError("No valid images found. Please upload valid photos.")

    features = data.get("key_features", "").strip()
    description = data.get("description", "").strip()
    cta = data.get("contact_cta", "").strip()

    captions = [
        f"Welcome to {data['property_name']}",
        f"Explore this {data['property_type']}",
        f"Location: {data['location']}",
        f"Price: {data['price']}",
        f"Key features: {features}",
    ]

    if description:
        captions.append(description)

    if cta:
        captions.append(cta)

    # Reuse supplied photos if there are more captions than photos.
    scene_count = max(len(valid_images), 4)
    scenes = []

    for index in range(scene_count):
        image_path = valid_images[index % len(valid_images)]
        caption = captions[index % len(captions)]
        scenes.append((image_path, caption))

    output_path = str(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        FPS,
        (VIDEO_WIDTH, VIDEO_HEIGHT)
    )

    if not writer.isOpened():
        raise RuntimeError(
            "Could not create MP4. Check OpenCV installation or video codec."
        )

    try:
        total_frames = SECONDS_PER_SCENE * FPS

        for scene_index, (image_path, caption) in enumerate(scenes):
            frame_image = make_frame(
                image_path,
                data,
                caption,
                scene_index,
                len(scenes)
            )

            frame = cv2.cvtColor(
                np.array(frame_image),
                cv2.COLOR_RGB2BGR
            )

            # Simple fade-in transition for each scene.
            for frame_index in range(total_frames):
                alpha = min(1.0, frame_index / max(1, FPS // 2))
                faded = (frame * alpha).astype(np.uint8)
                writer.write(faded)

    finally:
        writer.release()

    if not Path(output_path).exists() or Path(output_path).stat().st_size == 0:
        raise RuntimeError("Video export failed.")

    return output_path
