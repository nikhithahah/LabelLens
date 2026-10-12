import streamlit as st
import pytesseract
import pandas as pd
from PIL import Image, ImageOps, ImageEnhance
import re

# If Tesseract is installed but Python cannot find it,
# uncomment the next line and change the path if needed:
# pytesseract.pytesseract.tesseract_cmd = (
#     r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# )

st.set_page_config(
    page_title="LabelLens",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 LabelLens")
st.subheader("Understand products. Compare labels.")
st.write(
    "Upload two product labels to extract their printed "
    "information and compare them."
)


def read_label(uploaded_file):
    """Extract printed text from a product-label image."""
    image = Image.open(uploaded_file).convert("RGB")

    # Improve image readability for OCR
    image = ImageOps.grayscale(image)
    image = ImageEnhance.Contrast(image).enhance(1.5)

    extracted_text = pytesseract.image_to_string(
        image,
        config="--psm 6"
    )

    return extracted_text.strip()


def find_details(text):
    """Find common label fields using simple text rules."""
    lines = [line.strip() for line in text.splitlines()
             if line.strip()]

    details = {
        "Ingredients": [],
        "Price (MRP)": [],
        "Quantity": [],
        "Expiry / Best Before": [],
        "Warnings": []
    }

    for line in lines:
        lower = line.lower()

        if re.search(r"\bingredients?\b", lower):
            details["Ingredients"].append(line)

        if re.search(r"\b(mrp|rs\.?|₹)\b", lower):
            details["Price (MRP)"].append(line)

        if re.search(
            r"\b(net weight|net wt|net quantity|"
            r"volume|contents)\b", lower
        ) or re.search(r"\b\d+(?:\.\d+)?\s?(?:mg|kg|g|ml|l)\b",
                       lower):
            details["Quantity"].append(line)

        if re.search(
            r"\b(expiry|expires|best before|use by|"
            r"mfg date|manufactured on)\b", lower
        ):
            details["Expiry / Best Before"].append(line)

        if re.search(
            r"\b(warning|caution|allergen|contains|"
            r"keep out of reach)\b", lower
        ):
            details["Warnings"].append(line)

    return details


col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 🛍️ Product A")
    image_a = st.file_uploader(
        "Upload the first label",
        type=["png", "jpg", "jpeg"],
        key="product_a"
    )

with col_b:
    st.markdown("### 🛍️ Product B")
    image_b = st.file_uploader(
        "Upload the second label",
        type=["png", "jpg", "jpeg"],
        key="product_b"
    )

if image_a:
    st.image(image_a, caption="Product A label",
             use_container_width=True)

if image_b:
    st.image(image_b, caption="Product B label",
             use_container_width=True)

if st.button("🔍 Analyze and Compare", type="primary"):

    if not image_a or not image_b:
        st.warning("Please upload both product labels.")

    else:
        try:
            with st.spinner("Reading product labels..."):
                text_a = read_label(image_a)
                text_b = read_label(image_b)

            if not text_a and not text_b:
                st.error(
                    "No text was detected. Try clearer, "
                    "well-lit photos with readable text."
                )
            else:
                st.markdown("## 📄 Extracted Label Text")

                left, right = st.columns(2)

                with left:
                    st.markdown("#### Product A")
                    st.text_area(
                        "Text detected on Product A",
                        value=text_a or "No text detected.",
                        height=220
                    )

                with right:
                    st.markdown("#### Product B")
                    st.text_area(
                        "Text detected on Product B",
                        value=text_b or "No text detected.",
                        height=220
                    )

                details_a = find_details(text_a)
                details_b = find_details(text_b)

                st.markdown("## ⚖️ Side-by-Side Comparison")

                rows = []
                for field in details_a:
                    value_a = "\n".join(details_a[field]) or "Not detected"
                    value_b = "\n".join(details_b[field]) or "Not detected"

                    rows.append({
                        "Label Information": field,
                        "Product A": value_a,
                        "Product B": value_b
                    })

                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True
                )

                st.info(
                    "This comparison uses text detected from the "
                    "printed labels. 'Not detected' does not mean "
                    "the product lacks that information. OCR and "
                    "keyword matching can miss or misread details. "
                    "Verify important information on the package."
                )

        except pytesseract.TesseractNotFoundError:
            st.error(
                "Tesseract OCR was not found. Install the "
                "Tesseract OCR application on Windows, then "
                "restart this app. If necessary, set the "
                "tesseract_cmd path near the top of this file."
            )

        except Exception as error:
            st.error(f"Something went wrong: {error}")
            st.write(
                "Check that both images are valid PNG or JPEG files."
            )

st.divider()
st.caption(
    "LabelLens | Prototype — always verify extracted details "
    "against the original product label."
)