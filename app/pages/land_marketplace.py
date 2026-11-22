
import streamlit as st

from app.db.database import get_db_connection
from app.services.land_service import LandRecordService


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Bhumi-Setu | Land Marketplace",
    page_icon="🏡",
    layout="wide"
)


# ==================================================
# DATABASE: MARKETPLACE LISTINGS
# ==================================================

def init_marketplace_table():
    """Create marketplace listings table."""

    conn = get_db_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS marketplace_listings (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_name TEXT NOT NULL,
                seller_contact TEXT NOT NULL,
                district TEXT NOT NULL,
                circle TEXT NOT NULL,
                village TEXT NOT NULL,
                dag_number TEXT NOT NULL,
                patta_number TEXT NOT NULL,
                area_bigha REAL NOT NULL,
                asking_price INTEGER NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Available',
		verification_status TEXT DEFAULT 'Pending Verification',
		matched_record_id INTEGER,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Safely add verification columns to existing databases
        existing_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(marketplace_listings)"
            ).fetchall()
        }        

        if "verification_status" not in existing_columns:
            conn.execute("""
                ALTER TABLE marketplace_listings
                ADD COLUMN verification_status TEXT
                DEFAULT 'Pending Verification'
            """)

        if "matched_record_id" not in existing_columns:
            conn.execute("""
                ALTER TABLE marketplace_listings
                ADD COLUMN matched_record_id INTEGER
            """)

        if "review_status" not in existing_columns:
            conn.execute("""
                ALTER TABLE marketplace_listings
                ADD COLUMN review_status TEXT DEFAULT 'Not Submitted'
            """)

        if "reviewed_by" not in existing_columns:
            conn.execute("""
                ALTER TABLE marketplace_listings
                ADD COLUMN reviewed_by TEXT
            """)

        if "review_notes" not in existing_columns:
            conn.execute("""
                ALTER TABLE marketplace_listings
                ADD COLUMN review_notes TEXT
            """)

        if "reviewed_at" not in existing_columns:
            conn.execute("""
                ALTER TABLE marketplace_listings
                ADD COLUMN reviewed_at TEXT
            """)

        conn.commit()

    finally:
        conn.close()


def save_listing(
    seller_name,
    seller_contact,
    district,
    circle,
    village,
    dag,
    patta,
    area,
    price,
    description,
    verification_status,
    matched_record_id
):
    """Save a new land listing permanently in SQLite."""

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO marketplace_listings (
    		seller_name,
   	 	seller_contact,
    		district,
    		circle,
    		village,
    		dag_number,
    		patta_number,
    		area_bigha,
    		asking_price,
    		description,
    		verification_status,
    		matched_record_id
	)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            seller_name.strip(),
            seller_contact.strip(),
            district.strip(),
            circle.strip(),
            village.strip(),
            dag.strip(),
            patta.strip(),
            area,
            price,
            description.strip(),
            verification_status,
    	    matched_record_id
        ))

        conn.commit()

        return cursor.lastrowid

    finally:
        conn.close()


def get_marketplace_listings():
    """Retrieve all active marketplace listings."""

    conn = get_db_connection()

    try:
        rows = conn.execute("""
            SELECT *
            FROM marketplace_listings
            WHERE status = 'Available'
            ORDER BY listing_id DESC
        """).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()
def verify_listing_against_land_record(
    district,
    circle,
    village,
    dag,
    patta
):
    """Check whether a marketplace listing matches a local land record."""

    record, error = LandRecordService.search_record(
        state="Assam",
        district=district,
        circle=circle,
        village=village,
        dag_number=dag,
        patta_number=patta
    )

    if record:
        return {
            "matched": True,
            "status": "Local Land Record Match Found",
            "record": record
        }

    return {
        "matched": False,
        "status": "Pending Verification",
        "record": None,
        "message": error
    }

# Initialize database table
init_marketplace_table()


# ==================================================
# PAGE HEADER
# ==================================================

st.title("🏡 Bhumi-Setu Land Marketplace")

st.caption(
    "Discover land parcels and explore available properties across Assam."
)

st.divider()


# ==================================================
# SUBMISSION SUCCESS NOTIFICATION
# ==================================================

if "listing_submitted" in st.session_state:
    st.success(
        f"Your land listing was submitted successfully! "
        f"Listing ID: {st.session_state['listing_submitted']}"
    )


# ==================================================
# AVAILABLE LAND FOR SALE
# ==================================================

st.header("Available Land for Sale")


# Demonstration listings
demo_listings = [
    {
        "village": "Dharapur",
        "district": "Kamrup Metropolitan",
        "circle": "Azara",
        "dag": "1",
        "patta": "1",
        "area": "2 Bigha",
        "price": 1800000,
        "seller": "Demo Seller 1",
        "contact": "Not available",
        "description": "Illustrative demonstration listing.",
        "demo": True
    },
    {
        "village": "Demo Village",
        "district": "Kamrup",
        "circle": "Demo Circle",
        "dag": "25",
        "patta": "12",
        "area": "1 Bigha",
        "price": 950000,
        "seller": "Demo Seller 2",
        "contact": "Not available",
        "description": "Illustrative demonstration listing.",
        "demo": True
    }
]


# Retrieve saved listings
saved_listings = get_marketplace_listings()

st.metric(
    "Seller-submitted active listings",
    len(saved_listings)
)


# Prepare listings for display
all_listings = []

for land in saved_listings:

    all_listings.append({
        "village": land["village"],
        "district": land["district"],
        "circle": land["circle"],
        "dag": land["dag_number"],
        "patta": land["patta_number"],
        "area": f'{land["area_bigha"]:g} Bigha',
        "price": land["asking_price"],
        "seller": land["seller_name"],
        "contact": land["seller_contact"],
        "description": land["description"] or "No additional details.",
        "verification_status": land.get(
            "verification_status",
            "Pending Verification"
        ),
        "review_status": land.get(
            "review_status",
            "Not Submitted"
        ),
        "listing_id": land["listing_id"],
        "matched_record_id": land["matched_record_id"],
        "demo": False
    })


# Add demonstration listings
all_listings.extend(demo_listings)


# Display property cards
if not all_listings:
    st.info("No properties are currently available.")

else:

    for index, land in enumerate(all_listings):

        if index % 2 == 0:
            col1, col2 = st.columns(2)

        current_col = col1 if index % 2 == 0 else col2

        with current_col:

            with st.container(border=True):

                st.subheader(f"Land at {land['village']}")

                if land["demo"]:
                    st.info("Demonstration Listing")
                else:
                     st.success("Seller Listing - Available")

                     st.write(
                          "**Land Record Matching:**",
                          land.get("verification_status", "Pending Verification")
                       )
                     st.write(
                         "**Government Review Status:**",
                         land.get("review_status", "Not Submitted")
                       )

                st.metric(
                    "Asking Price",
                    f"₹{land['price']:,}"
                )

                st.write(f"**District:** {land['district']}")
                st.write(f"**Circle:** {land['circle']}")
                st.write(f"**Area:** {land['area']}")
                st.write(f"**Dag Number:** {land['dag']}")
                st.write(f"**Patta Number:** {land['patta']}")
                st.write(f"**Seller:** {land['seller']}")

                if not land["demo"]:
                    st.write(f"**Contact:** {land['contact']}")
                    st.write(f"**Description:** {land['description']}")

                    st.caption(
                        "Seller-provided information. "
                        "Independent verification required."
                    )

                    if land.get("matched_record_id"):
                        if st.button(
                            "View Digital Land Passport",
                            key=f"passport_{land['listing_id']}"
                        ):
                            st.session_state["passport_request"] = {
                                "state": "Assam",
                                "district": land["district"],
                                "circle": land["circle"],
                                "village": land["village"],
                                "dag_number": land["dag"],
                                "patta_number": land["patta"],
                                "review_status": land.get("review_status", "Not Submitted")
                            }

                            st.switch_page("main.py")

                else:
                    st.caption(
                        "Illustrative demonstration listing."
                    )


# ==================================================
# SELLER REGISTRATION
# ==================================================

st.header("List Your Land for Sale")

st.write(
    "Landowners can submit their property details."
)


with st.form("land_listing_form"):

    seller_name = st.text_input("Seller Name")

    seller_contact = st.text_input("Contact Number")

    district = st.text_input("District")

    circle = st.text_input("Revenue Circle")

    village = st.text_input("Village")

    dag = st.text_input("Dag Number")

    patta = st.text_input("Patta Number")

    area = st.number_input(
        "Land Area (in Bigha)",
        min_value=0.0,
        step=0.1
    )

    price = st.number_input(
        "Expected Asking Price (₹)",
        min_value=0,
        step=10000
    )

    description = st.text_area(
        "Additional Land Details"
    )

    submitted = st.form_submit_button(
        "Submit Land Listing",
        type="primary"
    )


# ==================================================
# FORM VALIDATION AND DATABASE SAVE
# ==================================================

if submitted:

    if not all([
        seller_name.strip(),
        seller_contact.strip(),
        district.strip(),
        circle.strip(),
        village.strip(),
        dag.strip(),
        patta.strip()
    ]) or area <= 0 or price <= 0:

        st.error(
            "Please complete all required fields."
        )

    else:

        verification_result = verify_listing_against_land_record(
            district=district,
            circle=circle,
            village=village,
            dag=dag,
            patta=patta
        )

        verification_status = verification_result["status"]

        matched_record_id = (
            getattr(verification_result["record"], "id", None)
            if verification_result["matched"]
            else None
        )

        try:

            listing_id = save_listing(
                seller_name,
                seller_contact,
                district,
                circle,
                village,
                dag,
                patta,
                area,
                price,
                description,
                verification_status,
                matched_record_id
            )

            st.session_state["listing_submitted"] = (
                f"BS-{listing_id:05d}"
            )

            st.rerun()

        except Exception as exc:

            st.error(
                f"Unable to save listing: {exc}"
            )
# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "Bhumi-Setu is a land discovery and due-diligence support platform. "
    "Listings and asking prices are seller-provided and are not government valuations."
)


st.caption(
                        "Illustrative demonstration listing."
                    )


st.divider()


# ==================================================
# SELLER REGISTRATION
# ==================================================

st.header("List Your Land for Sale")

st.write(
    "Landowners can submit their property details."
)


with st.form("land_listing_form_2"):

    seller_name = st.text_input("Seller Name")

    seller_contact = st.text_input("Contact Number")

    district = st.text_input("District")

    circle = st.text_input("Revenue Circle")

    village = st.text_input("Village")

    dag = st.text_input("Dag Number")

    patta = st.text_input("Patta Number")

    area = st.number_input(
        "Land Area (in Bigha)",
        min_value=0.0,
        step=0.1
    )

    price = st.number_input(
        "Expected Asking Price (₹)",
        min_value=0,
        step=10000
    )

    description = st.text_area(
        "Additional Land Details"
    )

    submitted = st.form_submit_button(
        "Submit Land Listing",
        type="primary"
    )


# ==================================================
# FORM VALIDATION AND DATABASE SAVE
# ==================================================

if submitted:

    if not all([
        seller_name.strip(),
        seller_contact.strip(),
        district.strip(),
        circle.strip(),
        village.strip(),
        dag.strip(),
        patta.strip()
    ]) or area <= 0 or price <= 0:

        st.error(
            "Please complete all required fields."
        )

    else:

        verification_result = verify_listing_against_land_record(
            district=district,
            circle=circle,
            village=village,
            dag=dag,
            patta=patta
        )

        verification_status = verification_result["status"]

        matched_record_id = (
            getattr(verification_result["record"], "id", None)
            if verification_result["matched"]
            else None
        )

        try:

            listing_id = save_listing(
                seller_name,
                seller_contact,
                district,
                circle,
                village,
                dag,
                patta,
                area,
                price,
                description,
                verification_status,
                matched_record_id
            )

            st.session_state["listing_submitted"] = (
                f"BS-{listing_id:05d}"
            )

            st.rerun()

        except Exception as exc:

            st.error(
                f"Unable to save listing: {exc}"
            )
# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "Bhumi-Setu is a land discovery and due-diligence support platform. "
    "Listings and asking prices are seller-provided and are not government valuations."
)
