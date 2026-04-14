import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="MDM Migration Planner", page_icon="📱", layout="wide")

st.sidebar.markdown("## 📱 MDM Migration Planner")
st.sidebar.markdown("Plan your MDM migration with phased timelines, risk flags, and checklists.")
st.sidebar.markdown("---")

SOURCE_PLATFORMS = [
    "VMware Workspace ONE", "Jamf Pro", "Microsoft Intune", "MobileIron", "Other"
]
TARGET_PLATFORMS = [
    "Microsoft Intune (Windows)", "Jamf Pro (macOS)", "Kandji (macOS)", "Jamf + Intune (both)"
]
URGENCY_OPTIONS = {
    "Low (12 weeks)": 12,
    "Medium (8 weeks)": 8,
    "High (6 weeks)": 6,
    "Critical (4 weeks)": 4,
}

st.sidebar.subheader("Environment Inputs")
source = st.sidebar.selectbox("Source MDM platform", SOURCE_PLATFORMS)
targets = st.sidebar.multiselect("Target platform(s)", TARGET_PLATFORMS)
device_count = st.sidebar.number_input("Total device count", min_value=1, value=100)
macos_pct = st.sidebar.slider("macOS %", 0, 100, 50)
windows_pct = 100 - macos_pct
st.sidebar.caption(f"Windows: {windows_pct}%")
if macos_pct + windows_pct != 100:
    st.sidebar.error("macOS % + Windows % must equal 100.")
team_size = st.sidebar.number_input("IT staff for migration", min_value=1, value=3)
urgency_label = st.sidebar.selectbox("Migration urgency", list(URGENCY_OPTIONS.keys()))
urgency_weeks = URGENCY_OPTIONS[urgency_label]


def build_phase_table(device_count, urgency_weeks):
    pilot = max(1, int(device_count * 0.05))
    exec_pool = max(1, int(device_count * 0.05))
    wave1 = int(device_count * 0.30)
    wave2 = max(0, device_count - pilot - exec_pool - wave1)

    # Distribute remaining weeks across Wave 1 and Wave 2
    # Fixed weeks: Discovery=1, Pilot=1, Exec=1, Decom=1 -> 4 weeks fixed
    remaining = max(2, urgency_weeks - 4)
    w1_weeks = max(1, remaining // 2)
    w2_weeks = max(1, remaining - w1_weeks)

    phases = [
        {
            "Phase": "1 — Discovery & Inventory",
            "Scope": "All devices",
            "Duration (wks)": 1,
            "Key Actions": "Audit current MDM, export device list, document policy configs, identify edge cases",
            "Risk Level": "Low",
            "Rollback Option": "N/A",
        },
        {
            "Phase": "2 — Pilot Group",
            "Scope": f"{pilot} devices (5%)",
            "Duration (wks)": 1,
            "Key Actions": "Enroll pilot group, validate policy push, test app deployment, confirm compliance reporting",
            "Risk Level": "Low",
            "Rollback Option": "Re-enroll in source MDM",
        },
        {
            "Phase": "3 — Wave 1",
            "Scope": f"{wave1} devices (30%)",
            "Duration (wks)": w1_weeks,
            "Key Actions": "Enroll Wave 1, monitor compliance dashboard, resolve enrollment errors",
            "Risk Level": "Medium",
            "Rollback Option": "Re-enroll devices in source MDM; policies still active",
        },
        {
            "Phase": "4 — Wave 2",
            "Scope": f"{wave2} devices (remaining non-exec)",
            "Duration (wks)": w2_weeks,
            "Key Actions": "Bulk enrollment, automated policy assignment, help desk support window",
            "Risk Level": "Medium-High",
            "Rollback Option": "Source MDM still running; rollback per-device via MDM console",
        },
        {
            "Phase": "5 — Executive & Sensitive Devices",
            "Scope": f"{exec_pool} devices (5%)",
            "Duration (wks)": 1,
            "Key Actions": "1:1 IT support sessions, white-glove enrollment, VIP validation",
            "Risk Level": "High",
            "Rollback Option": "Immediate rollback via source MDM; dedicated support line active",
        },
        {
            "Phase": "6 — Decommission Source MDM",
            "Scope": "Source platform",
            "Duration (wks)": 1,
            "Key Actions": "Confirm 100% enrollment in new MDM, cancel source licenses, archive config exports",
            "Risk Level": "Low",
            "Rollback Option": "Keep licenses active 30 days post-cutover as safety net",
        },
    ]
    return pd.DataFrame(phases)


def build_risk_flags(source, targets):
    flags = []
    target_str = " ".join(targets)

    if "Workspace ONE" in source and "Intune" in target_str:
        flags.append(("warning", "Conditional Access policy conflicts if Okta device trust is active"))
    if "Workspace ONE" in source and "Jamf" in target_str:
        flags.append(("warning", "ADE re-enrollment required for all macOS devices"))
    if "Kandji" in target_str:
        flags.append(("warning", "Apple Business Manager blueprint migration required"))
    if "Jamf + Intune" in target_str or (
        "Jamf" in target_str and "Intune" in target_str and "Jamf + Intune" not in target_str
    ):
        flags.append(("warning", "Dual-platform policy drift risk — enforce platform tagging in Okta groups"))
    flags.append(("info", "Executive devices should be migrated last with a dedicated support window"))
    return flags


st.title("MDM Migration Planner")

if not targets:
    st.info("Select at least one target platform in the sidebar to generate a plan.")
else:
    total_weeks = urgency_weeks
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Devices", device_count)
    col2.metric("Team Size", team_size)
    col3.metric("Timeline", f"{total_weeks} weeks")

    st.subheader("Migration Timeline")
    df = build_phase_table(device_count, urgency_weeks)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Risk Matrix")
    flags = build_risk_flags(source, targets)
    flag_texts = []
    for severity, msg in flags:
        if severity == "warning":
            st.warning(f"**{msg}**")
        else:
            st.info(msg)
        flag_texts.append(f"- [{severity.upper()}] {msg}")

    st.subheader("Cutover Checklist")
    checklist_items = [
        "All devices enrolled in new MDM and reporting compliant",
        "Okta device trust updated to new MDM integration",
        "Software push validated for top 10 apps",
        "FileVault/BitLocker key escrow confirmed in new MDM",
        "Help desk trained on new MDM console",
        "Rollback playbook documented and reviewed",
        "Exec devices migrated with 1:1 support confirmed",
        "Source MDM license cancellation date set (30 days post-cutover)",
    ]
    for item in checklist_items:
        st.checkbox(item, value=False, disabled=True, key=f"check_{item}")

    st.subheader("Export")
    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "Download Migration Plan as CSV",
            data=csv,
            file_name="mdm_migration_plan.csv",
            mime="text/csv",
        )
    with col2:
        risk_md = (
            f"# MDM Migration Risk Summary\n\n"
            f"**Source:** {source}  \n**Targets:** {', '.join(targets)}\n\n"
            f"## Risk Flags\n\n" + "\n".join(flag_texts)
        )
        st.download_button(
            "Download Risk Summary as Markdown",
            data=risk_md,
            file_name="risk_summary.md",
            mime="text/markdown",
        )

st.sidebar.markdown("---")
st.sidebar.markdown("Built by [Oleg Strutsovski](https://linkedin.com/in/olegst)")
