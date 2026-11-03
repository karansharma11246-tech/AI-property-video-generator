import streamlit as st
import tempfile
from pathlib import Path

from video_generator import build_script, generate_video

st.set_page_config(
    page_title="AI Property Video Generator",
    page_icon="🏡",
    layout="wide"
)

st.title("🏡 AI Property Video Generator")
st.write(
    "Turn property details and photos into a promotional MP4 video."
)

with st.form("property_form"):
    st.subheader("Property Information")

    property_name = st.text_input("Property Name")
    location = st.text_input("Location")
    property_type = st.selectbox(
        "Property Type",
        ["Apartment", "Independent House", "Villa", "Plot",
         "Commercial Property"]
    )

    price = st.text_input("Price", placeholder="₹85 lakh")

    key_features = st.text_area(
        "Key Features",
        placeholder="Example: 3 bedrooms, balcony, garden"
    )

    description = st.text_area(
        "Additional Description (Optional)"
    )

    contact_cta = st.text_input(
        "Contact / Call to Action",
        placeholder="Contact us today to arrange a visit"
    )

    uploaded_images = st.file_uploader(
        "Upload 4–8 Property Images",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True
    )

    submitted = st.form_submit_button("Generate Video")

if submitted:
    if not property_name.strip():
        st.error("Please enter the property name.")

    elif not location.strip():
        st.error("Please enter the location.")

    elif not price.strip():
        st.error("Please enter the property price.")

    elif not key_features.strip():
        st.error("Please enter at least one key feature.")

    elif not contact_cta.strip():
        st.error("Please enter contact details or an enquiry prompt.")

    elif not uploaded_images or not 4 <= len(uploaded_images) <= 8:
        st.error("Please upload between 4 and 8 property images.")

    else:
        property_data = {
            "property_name": property_name.strip(),
            "location": location.strip(),
            "property_type": property_type,
            "price": price.strip(),
            "key_features": key_features.strip(),
            "description": description.strip(),
            "contact_cta": contact_cta.strip()
        }

        try:
            with st.spinner("Creating your property video..."):
                with tempfile.TemporaryDirectory() as temp_dir:
                    folder = Path(temp_dir)
                    image_paths = []

                    for index, uploaded_file in enumerate(uploaded_images):
                        suffix = Path(uploaded_file.name).suffix.lower()

                        if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
                            suffix = ".jpg"

                        image_path = folder / f"image_{index}{suffix}"
                        image_path.write_bytes(uploaded_file.getvalue())
                        image_paths.append(str(image_path))

                    script = build_script(property_data)
                    st.subheader("Generated Script")
                    st.write(script)

                    output_path = folder / "property_promo.mp4"

                    generate_video(
                        property_data,
                        image_paths,
                        str(output_path)
                    )

                    if not output_path.exists() or output_path.stat().st_size == 0:
                        raise RuntimeError("The MP4 file was not generated.")

                    video_bytes = output_path.read_bytes()

            st.success("Property video generated successfully!")
            st.video(video_bytes)

            st.download_button(
                "Download MP4",
                data=video_bytes,
                file_name="property_promo.mp4",
                mime="video/mp4"
            )

        except Exception as error:
            st.error(f"Could not generate video: {error}")
            st.info("Check the terminal for more technical details.")

st.divider()
st.caption(
    "Prototype uses template-based text generation. "
    "Only supplied property information should appear in the video."
)
