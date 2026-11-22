import streamlit as st
from pathlib import Path
import hashlib
import json
from datetime import datetime
from app.config import DOCUMENTS_DIR

from app.services.document_intelligence import (
    extract_document_text,
    classify_document,
    extract_land_fields,
    compare_land_fields
)
from app.services.anomaly_detection import detect_land_anomalies
def render_due_diligence_dashboard(record):
    """
    Renders the Bhumi-Setu Digital Land Passport
    Due Diligence Dashboard.

    Demonstration data is explicitly labelled.
    This dashboard does not certify ownership or title.
    """

    st.markdown("---")
    st.header("Digital Land Passport")
    st.subheader("Land Due Diligence Dashboard")

    st.caption(
        "Prototype demonstration. Information shown here "
        "does not constitute legal clearance or title verification."
    )

    # Parcel identification
    st.markdown("### Parcel Identification")

    col1, col2, col3 = st.columns(3)

    col1.metric("Village", getattr(record, "village", "Unavailable"))
    col2.metric("Dag Number", getattr(record, "dag_number", "Unavailable"))
    col3.metric("Patta Number", getattr(record, "patta_number", "Unavailable"))

    st.markdown("---")

    # Five due-diligence categories + Supporting Documents
    tabs = st.tabs([
        "Government Records",
        "Legal Documents",
        "Court Cases",
        "Land Classification",
        "Environment",
        "Supporting Documents",
        "AI Anomaly Screening"
    ])

    # TAB 1: Government records
    with tabs[0]:
        st.subheader("Government Land Records")

        st.info("Existing prototype record information")

        st.write("**Record information available in the database:**")

        st.write("District:", getattr(record, "district", "Unavailable"))
        st.write("Circle:", getattr(record, "circle", "Unavailable"))
        st.write("Village:", getattr(record, "village", "Unavailable"))
        st.write("Patta Type:", getattr(record, "patta_type", "Unavailable"))
        st.write("Land Classification:", getattr(record, "land_classification", "Unavailable"))
        st.write("Source:", getattr(record, "source", "Not recorded"))

        if getattr(record, "is_demo_data", False):
            st.warning(
                "This is synthetic demonstration data. "
                "It is not independently verified government evidence."
            )

        st.caption(
            "Mutation history, source timestamps and official "
            "document references require further integration."
        )

 
     # TAB 2: Legal documents
    with tabs[1]:
        st.subheader("Legal Document Verification")

        st.write(
            "Track the availability and preliminary review status "
            "of important land-related documents."
        )

        record_id = getattr(record, "id", "unknown")
        parcel_folder = DOCUMENTS_DIR / str(record_id)
        parcel_folder.mkdir(parents=True, exist_ok=True)

        status_file = parcel_folder / "legal_document_statuses.json"

        # Load previously saved statuses
        if status_file.exists():
            try:
                legal_statuses = json.loads(
                    status_file.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                legal_statuses = {}
        else:
            legal_statuses = {}

        documents = [
            "Registered Sale Deed",
            "Jamabandi / Record of Rights",
            "Mutation Order",
            "Encumbrance Certificate (where applicable)",
            "Other Supporting Documents"
        ]

        status_options = [
            "Not Provided",
            "Uploaded — Awaiting Review",
            "Under Review",
            "Discrepancy Found",
            "Human Review Completed"
        ]

        for document in documents:
            st.markdown(f"**{document}**")

            current_status = legal_statuses.get(
                document, "Not Provided"
            )

            if current_status not in status_options:
                current_status = "Not Provided"

            new_status = st.selectbox(
                f"Status — {document}",
                status_options,
                index=status_options.index(current_status),
                key=f"doc_status_{document}_{record_id}"
            )

            # Persist status immediately
            if new_status != legal_statuses.get(
                document, "Not Provided"
            ):
                legal_statuses[document] = new_status

                status_file.write_text(
                    json.dumps(legal_statuses, indent=4),
                    encoding="utf-8"
                )

        st.info(
            "These statuses are manually maintained. "
            "They do not represent independent legal verification."
        )


    # TAB 3: Court cases
    with tabs[2]:
        st.subheader("Court Cases and Stay Orders")

        st.warning(
            "No live court-record search is connected to this prototype."
        )

        st.write("**Court verification status:** Not Checked")

        st.write("Potential information to review:")

        st.markdown(
            "- Case reference number\n"
            "- Court name\n"
            "- Case status\n"
            "- Stay order or injunction\n"
            "- Parcel association evidence\n"
            "- Human verification"
        )

        st.caption(
            "Absence of retrieved case information does not establish "
            "that the parcel has no litigation."
        )

    # TAB 4: Land classification
    with tabs[3]:
        st.subheader("Land Classification and Zoning")

        st.write(
            "**Recorded Revenue Classification:**",
            getattr(record, "land_classification", "Not Available")
        )

        st.info(
            "Revenue classification, existing land use and "
            "permitted zoning are separate categories."
        )

        st.write("**Existing Land Use:** Not Assessed")
        st.write("**Planning / Zoning Classification:** Not Checked")
        st.write("**Residential Permission:** Authority Confirmation Required")
        st.write("**Commercial Permission:** Authority Confirmation Required")
        st.write("**Industrial Permission:** Authority Confirmation Required")

    # TAB 5: Environmental assessment
    with tabs[4]:
        st.subheader("Environmental Assessment")

        environmental_checks = {
            "Flood Exposure": "Not Assessed",
            "River Erosion": "Not Assessed",
            "Wetland Proximity": "Not Assessed",
            "Protected Area Restrictions": "Not Checked"
        }

        for item, status in environmental_checks.items():
            st.write(f"**{item}:** {status}")

        st.caption(
            "Environmental assessments require authoritative "
            "geospatial datasets and appropriate review."
        )
	       
    # TAB 6: Supporting Documents
    with tabs[5]:
        st.subheader("Supporting Documents")

        st.write(
            "Upload and organise supporting documents for this land parcel."
        )

        record_id = getattr(record, "id", "unknown")
        parcel_folder = DOCUMENTS_DIR / str(record_id)
        parcel_folder.mkdir(parents=True, exist_ok=True)

        metadata_path = parcel_folder / "document_metadata.json"

        # Load saved document metadata
        if metadata_path.exists():
            try:
                metadata = json.loads(
                    metadata_path.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                metadata = {}
        else:
            metadata = {}

        # Import previously uploaded files into the metadata list
        for existing_file in parcel_folder.iterdir():
            if existing_file.is_file() and existing_file.name != metadata_path.name:
                if existing_file.name not in metadata:
                    original_name = existing_file.name.split("_", 1)[-1]
                    metadata[existing_file.name] = {
                        "filename": original_name,
                        "category": "Other Supporting Document",
                        "uploaded_at": datetime.fromtimestamp(
                            existing_file.stat().st_mtime
                        ).strftime("%d %b %Y, %I:%M %p"),
                        "status": "Awaiting Review"
                    }

        # Document category
        categories = [
            "Registered Sale Deed",
            "Jamabandi / Record of Rights",
            "Mutation Order",
            "Encumbrance Certificate",
            "Land Revenue Receipt",
            "Identity Supporting Document",
            "Other Supporting Document"
        ]

        selected_category = st.selectbox(
            "Select document category",
            categories,
            key=f"support_category_{record_id}"
        )

        # Upload files
        supporting_files = st.file_uploader(
            "Choose supporting documents",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"supporting_docs_{record_id}"
        )

        if supporting_files:
            newly_saved = 0

            for uploaded_file in supporting_files:
                safe_name = Path(uploaded_file.name).name

                file_hash = hashlib.sha256(
                    uploaded_file.getvalue()
                ).hexdigest()

                stored_name = f"{file_hash}_{safe_name}"
                file_path = parcel_folder / stored_name

                if stored_name not in metadata:
                    if not file_path.exists():
                        file_path.write_bytes(uploaded_file.getvalue())

                    metadata[stored_name] = {
                        "filename": safe_name,
                        "category": selected_category,
                        "uploaded_at": datetime.now().strftime(
                            "%d %b %Y, %I:%M %p"
                        ),
                        "status": "Awaiting Review"
                    }

                    newly_saved += 1

            metadata_path.write_text(
                json.dumps(metadata, indent=4),
                encoding="utf-8"
            )

            if newly_saved:
                st.success(
                    f"{newly_saved} document(s) saved successfully."
                )
            else:
                st.info("These documents have already been saved.")

        # Save metadata, including previously uploaded files
        metadata_path.write_text(
            json.dumps(metadata, indent=4),
            encoding="utf-8"
        )

        st.markdown("### Stored Documents")

        if metadata:
            for stored_name, details in metadata.items():
                with st.container(border=True):
                    st.write(f"📄 **{Path(stored_name).name.split('_', 1)[-1]}**")
                    st.caption(
                        f"Category: {details['category']} | "
                        f"Uploaded: {details['uploaded_at']}"
                    )

                    st.write(
                        f"Stored file: `{stored_name}`"
                    )
                    if st.button(
                        "Extract Text with OCR",
                        key=f"ocr_{record_id}_{stored_name}"
                    ):
                        file_path = parcel_folder / stored_name

                        try:
                            extracted_text = extract_document_text(file_path)
                            st.text_area("OCR Raw Text", extracted_text, height=300)
                            predicted_category = classify_document(extracted_text)
                            extracted_fields = extract_land_fields(extracted_text)
                            single_parcel_fields = {
                                field: values[:1]
                                for field, values in extracted_fields.items()
                            }

                            comparison_results = compare_land_fields(
                                single_parcel_fields,
                                record
                            )

                            # Persist document intelligence results
                            details["predicted_category"] = predicted_category
                            details["extracted_fields"] = extracted_fields
                            details["comparison_results"] = comparison_results
                            details["extracted_text"] = extracted_text

                            metadata[stored_name] = details
                            metadata_path.write_text(
                                json.dumps(metadata, indent=4, ensure_ascii=False),
                                encoding="utf-8"
                            )

                            st.subheader("Land Record Comparison")

                            for field, status in comparison_results.items():
                                st.write(
                                    f"**{field.replace('_', ' ').title()}:** {status}"
                                )

                            st.subheader("AI Land Field Extraction")

                            for field, values in extracted_fields.items():
                                st.write(
                                    f"**{field.replace('_', ' ').title()}:**",
                                    ", ".join(values) if values else "Not Found"
                                )

                            details["predicted_category"] = predicted_category

                            st.info(f"AI Document Classification: {predicted_category}")

                            if extracted_text:
                                details["extracted_text"] = extracted_text
                                with open(metadata_path, "w", encoding="utf-8") as f:
                                    json.dump(metadata, f, indent=4, ensure_ascii=False)
                                st.success("Text extracted successfully!")

                                st.text_area(
                                    "Extracted Document Text",
                                    extracted_text,
                                    height=200,
                                    key=f"ocr_text_{record_id}_{stored_name}"
                                )
                            else:
                                st.warning("No readable text found in this document.")

                        except Exception as e:
                            st.error(f"OCR failed: {e}")
                    # Display previously saved AI analysis
                    if details.get("predicted_category"):
                        with st.expander("Saved AI Document Analysis"):
                            st.write(
                                "**Document Classification:**",
                                details["predicted_category"]
                            )

                            st.write("**Land Record Comparison:**")
                            for field, result in details.get(
                                "comparison_results", {}
                            ).items():
                                st.write(
                                    f"- {field.replace('_', ' ').title()}: {result}"
                                )

                            st.write("**Extracted Land Fields:**")
                            for field, values in details.get(
                                "extracted_fields", {}
                            ).items():
                                st.write(
                                    f"- {field.replace('_', ' ').title()}: "
                                    f"{', '.join(values) if values else 'Not Found'}"
                                )

                    status_options = [
                        "Awaiting Review",
                        "Under Review",
                        "Discrepancy Found",
                        "Human Review Completed"
                    ]

                    current_status = details.get(
                        "status", "Awaiting Review"
                    )

                    if current_status not in status_options:
                        current_status = "Awaiting Review"

                    new_status = st.selectbox(
                        "Review Status",
                        status_options,
                        index=status_options.index(current_status),
                        key=f"review_{record_id}_{stored_name}"
                    )

                    if new_status != details.get("status"):
                        metadata[stored_name]["status"] = new_status

                        metadata_path.write_text(
                            json.dumps(metadata, indent=4),
                            encoding="utf-8"
                        )

                    if new_status == "Discrepancy Found":
                        st.warning("A discrepancy has been reported.")
                    elif new_status == "Human Review Completed":
                        st.info(
                            "Marked as human review completed. "
                            "This status is a manual declaration, "
                            "not independent legal certification."
                        )
        else:
            st.info("No supporting documents uploaded yet.")

        st.caption(
            "Document upload and status tracking do not constitute "
            "legal verification, title certification or government approval."
        )


    # TAB 7: AI anomaly screening
    with tabs[6]:
        st.subheader("AI-Assisted Land Anomaly Screening")

        st.caption(
            "Preliminary rule-based screening of the selected land parcel. "
            "Results are not proof of fraud or legal irregularity."
        )

        anomalies = detect_land_anomalies([record])

        area_difference = getattr(record, "area_difference_pct", None)

        if area_difference is not None:
            st.metric("Area Difference", f"{area_difference}%")

        if anomalies:
            st.warning("Potential data inconsistencies detected.")

            for anomaly in anomalies:
                st.write(
                    f"**Dag:** {anomaly['dag_number']} | "
                    f"**Patta:** {anomaly['patta_number']}"
                )

                for issue in anomaly["issues"]:
                    st.write(f"- {issue}")
        else:
            st.success("No anomalies detected in the selected parcel.")

        st.info(
            "This screening checks the selected parcel's available "
            "information. Duplicate checking across the full database "
            "requires a database-wide comparison."
        )

    # Final status
    st.markdown("---")
    st.subheader("Transaction Preparation Status")

    st.warning(
        "DUE DILIGENCE INCOMPLETE — Additional documents, "
        "authoritative records and relevant authority confirmation "
        "are required."
    )

    st.caption(
        "Bhumi-Setu is an information and transaction-preparation "
        "prototype. It does not certify ownership, title, legal "
        "validity or transaction eligibility."
    )
