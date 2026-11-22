from collections import Counter


def detect_land_anomalies(records, area_threshold_pct=5.0):
    """
    Detects suspicious inconsistencies in land records.
    Returns explainable anomaly flags.
    """

    anomalies = []
    seen = Counter()

    for record in records:
        issues = []

        dag = str(record.dag_number or "").strip()
        patta = str(record.patta_number or "").strip()

        # Missing identifiers
        if not dag:
            issues.append("Missing Dag number")

        if not patta:
            issues.append("Missing Patta number")

        # Duplicate parcel identifier
        key = (dag, patta)

        if dag and patta:
            seen[key] += 1

            if seen[key] > 1:
                issues.append("Duplicate Dag-Patta combination")

        # Missing classification
        if not str(record.land_classification or "").strip():
            issues.append("Missing land classification")

        # Area deviation
        difference_pct = record.area_difference_pct

        if (
            difference_pct is not None
            and abs(difference_pct) > area_threshold_pct
        ):
            issues.append(
                f"Area deviation exceeds {area_threshold_pct}%"
            )

        if issues:
            anomalies.append({
                "dag_number": dag or "Unavailable",
                "patta_number": patta or "Unavailable",
                "issues": issues
            })

    return anomalies
