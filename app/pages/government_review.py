
import streamlit as st
from app.db.database import get_db_connection

st.set_page_config(
    page_title="Government Review | Bhumi-Setu",
    page_icon="🏛️",
    layout="wide"
)

st.title("Government Verification Review")
st.caption(
    "Prototype review interface for examining submitted land listings. "
    "This is not a live government verification system."
)

conn = get_db_connection()

try:
    existing_columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(marketplace_listings)"
        ).fetchall()
    }

    review_columns = {
        "review_status": "TEXT DEFAULT 'Not Submitted'",
        "reviewed_by": "TEXT",
        "review_notes": "TEXT",
        "reviewed_at": "TEXT"
    }

    for column, definition in review_columns.items():
        if column not in existing_columns:
            conn.execute(
                f"ALTER TABLE marketplace_listings "
                f"ADD COLUMN {column} {definition}"
            )

    conn.commit()
    listings = conn.execute("""
        SELECT *
        FROM marketplace_listings
        WHERE status = 'Available'
        ORDER BY listing_id DESC
    """).fetchall()

    if not listings:
        st.info("No land listings are available for review.")

    else:
        options = {
            f"BS-{row['listing_id']:05d} | {row['village']} | "
            f"Dag {row['dag_number']} | Patta {row['patta_number']}": row
            for row in listings
        }

        selected_label = st.selectbox(
            "Select Land Listing",
            list(options.keys())
        )

        listing = options[selected_label]

        st.subheader("Land Listing Details")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Seller:**", listing["seller_name"])
            st.write("**District:**", listing["district"])
            st.write("**Circle:**", listing["circle"])
            st.write("**Village:**", listing["village"])

        with col2:
            st.write("**Dag Number:**", listing["dag_number"])
            st.write("**Patta Number:**", listing["patta_number"])
            st.write("**Asking Price:**", f"₹{listing['asking_price']:,}")
            st.write(
                "**Land Record Match:**",
                listing["verification_status"]
            )

        st.divider()

        st.subheader("Record Review Decision")

        with st.form("government_review_form"):

            reviewer = st.text_input("Reviewer Name")

            decision = st.selectbox(
                "Review Decision",
                [
                    "Under Review",
                    "Approved",
                    "Rejected",
                    "Correction Required"
                ]
            )

            notes = st.text_area("Review Remarks")

            submitted = st.form_submit_button(
                "Save Review Decision",
                type="primary"
            )

            if submitted:
                if not reviewer.strip():
                    st.error("Please enter the reviewer name.")

                else:
                    conn.execute("""
                        UPDATE marketplace_listings
                        SET review_status = ?,
                            reviewed_by = ?,
                            review_notes = ?,
                            reviewed_at = CURRENT_TIMESTAMP
                        WHERE listing_id = ?
                    """, (
                        decision,
                        reviewer.strip(),
                        notes.strip(),
                        listing["listing_id"]
                    ))

                    conn.commit()

                    st.success("Review decision saved successfully.")
                    st.rerun()

        st.divider()

        st.subheader("Previous Review Details")

        st.write(
            "**Review Status:**",
            listing["review_status"]
        )
        st.write("**Reviewed By:**", listing["reviewed_by"] or "Not reviewed")
        st.write("**Remarks:**", listing["review_notes"] or "No remarks")

finally:
    conn.close()
