import streamlit as st
import pandas as pd

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

DEMO = {
    "source": "VMware Workspace ONE",
    "targets": ["Microsoft Intune (Windows)", "Jamf Pro (macOS)"],
    "device_count": 550,
    "macos_pct": 60,
    "team_size": 3,
    "urgency": "Medium (8 weeks)",
}

if "demo_loaded" not in st.session_state:
    st.session_state.demo_loaded = False

st.sidebar.subheader("Environment Inputs")
if st.sidebar.button("Load Example (550 devices)"):
    st.session_state.demo_loaded = True

d = st.session_state.demo_loaded

source = st.sidebar.selectbox(
    "Source MDM platform", SOURCE_PLATFORMS,
    index=SOURCE_PLATFORMS.index(DEMO["source"]) if d else 0,
)
targets = st.sidebar.multiselect(
    "Target platform(s)", TARGET_PLATFORMS,
    default=DEMO["targets"] if d else [],
)
device_count = st.sidebar.number_input(
    "Total device count", min_value=1,
    value=DEMO["device_count"] if d else 100,
)
macos_pct = st.sidebar.slider(
    "macOS %", 0, 100,
    value=DEMO["macos_pct"] if d else 50,
)
windows_pct = 100 - macos_pct
st.sidebar.caption(f"Windows: {windows_pct}%")
team_size = st.sidebar.number_input(
    "IT staff for migration", min_value=1,
    value=DEMO["team_size"] if d else 3,
)
urgency_label = st.sidebar.selectbox(
    "Migration urgency", list(URGENCY_OPTIONS.keys()),
    index=list(URGENCY_OPTIONS.keys()).index(DEMO["urgency"]) if d else 0,
)
urgency_weeks = URGENCY_OPTIONS[urgency_label]


# ── Helpers ──────────────────────────────────────────────────────────────────

def target_str(targets):
    return " ".join(targets)

def has_intune(targets):
    return "Intune" in target_str(targets)

def has_jamf(targets):
    return "Jamf" in target_str(targets)

def has_kandji(targets):
    return "Kandji" in target_str(targets)

def has_split(targets):
    return "Jamf + Intune" in targets or (has_intune(targets) and has_jamf(targets))

def scope_label(n, pct_label=""):
    base = f"{n} devices"
    if pct_label:
        base += f" ({pct_label})"
    return base

def os_scope(n, macos_pct, windows_pct, targets):
    if macos_pct == 0 or windows_pct == 0 or not has_split(targets):
        return f"{n} devices"
    mac_n = max(1, int(n * macos_pct / 100))
    win_n = max(1, n - mac_n)
    return f"{n} devices ({mac_n} macOS / {win_n} Windows)"


# ── Discovery actions by source ───────────────────────────────────────────────

DISCOVERY_BY_SOURCE = {
    "VMware Workspace ONE": (
        "Export Smart Groups, OG hierarchy, profiles, VPP app assignments, and DEP token config. "
        "Document Workspace ONE Intelligence rules. Audit which profiles are WS ONE-native vs standard payloads."
    ),
    "Jamf Pro": (
        "Export Jamf policies, configuration profiles, static/smart group scopes, and PreStage Enrollment configs. "
        "Audit VPP content, extension attributes, and Jamf Connect config if in use."
    ),
    "Microsoft Intune": (
        "Export Intune compliance policies, configuration profiles, Autopilot deployment profiles, "
        "and Conditional Access rules. Document app protection policies and group-based assignments."
    ),
    "MobileIron": (
        "Export MobileIron policies, app catalog, labels, compliance actions, and certificate configs. "
        "Identify SCEP/NDES dependencies. Audit ActiveSync device partnerships."
    ),
    "Other": (
        "Audit all MDM-managed profiles, app assignments, and policy scopes. "
        "Export device list with serial numbers, OS versions, and assigned user mappings."
    ),
}

# ── Enrollment method by target ───────────────────────────────────────────────

def enrollment_method(targets):
    parts = []
    if has_intune(targets):
        parts.append("Windows Autopilot reset or manual Intune enrollment (OOBE)")
    if has_jamf(targets):
        parts.append("ADE re-enrollment via Apple Business Manager")
    if has_kandji(targets):
        parts.append("Kandji blueprint assignment via ABM automated enrollment")
    return "; ".join(parts) if parts else "Manual enrollment per target platform"

def pilot_actions(targets):
    actions = [f"Enroll pilot group via {enrollment_method(targets)}"]
    if has_intune(targets):
        actions.append("validate Intune compliance policies and Conditional Access")
    if has_jamf(targets):
        actions.append("push Jamf configuration profiles and validate Jamf Remote")
    if has_kandji(targets):
        actions.append("validate Kandji Library item deployment and blueprint assignment")
    actions.append("confirm compliance reporting in new MDM console")
    actions.append("test top-5 app pushes and software distribution")
    return ". ".join(actions) + "."

def wave_actions(targets, wave_num):
    actions = []
    if has_intune(targets):
        actions.append("Windows Autopilot or MDM-join enrollment, push update rings and compliance policies")
    if has_jamf(targets):
        actions.append("ADE enrollment via ABM, push Jamf policies and configuration profiles")
    if has_kandji(targets):
        actions.append("ABM-automated Kandji blueprint assignment, Library item deployment")
    if wave_num == 1:
        actions.append("monitor compliance dashboard hourly, resolve enrollment failures same-day")
    elif wave_num == 2:
        actions.append("help desk support window active, escalation path documented")
    else:
        actions.append("routine help desk support, focus on stragglers and edge-case devices")
    return ". ".join(actions) + "."

def decom_actions(source):
    base = "Confirm 100% enrollment and compliance in new MDM. "
    if "Workspace ONE" in source:
        base += "Remove devices from WS ONE Smart Groups, revoke VPP licenses, unenroll DEP token, cancel WS ONE subscription."
    elif "Jamf Pro" in source:
        base += "Archive Jamf policies, remove devices from Jamf, update ABM MDM server assignment, cancel Jamf subscription."
    elif "Intune" in source:
        base += "Remove devices from Intune, delete Autopilot profiles, archive compliance policy exports, cancel unused Intune licenses."
    elif "MobileIron" in source:
        base += "Retire devices from MobileIron, delete labels and policies, cancel MobileIron subscription."
    else:
        base += "Retire all devices from source MDM, archive config exports, cancel source licenses."
    return base

# ── Risk level scaling by team capacity ──────────────────────────────────────

def scale_risk(base_risk, devices_per_staff):
    if devices_per_staff <= 50:
        return base_risk
    bumps = {
        "Low": {True: "Medium", False: "Low"},
        "Medium": {True: "High", False: "Medium-High"},
        "Medium-High": {True: "Critical", False: "High"},
        "High": {True: "Critical", False: "High"},
    }
    is_heavy = devices_per_staff > 150
    return bumps.get(base_risk, {}).get(is_heavy, base_risk)


# ── Wave duration scaling by team capacity ────────────────────────────────────

def scaled_wave_weeks(base_weeks, devices_in_wave, team_size):
    """Scale wave duration based on team capacity — works in both directions."""
    dps = devices_in_wave / max(1, team_size)
    if dps < 15:
        return max(0.5, round(base_weeks * 0.5, 1))
    elif dps < 30:
        return max(0.5, base_weeks - 1)
    elif dps > 150:
        return base_weeks + 2
    elif dps > 75:
        return base_weeks + 1
    return base_weeks


# ── Main phase table builder — structure varies by urgency ────────────────────

def build_phase_table(source, targets, device_count, macos_pct, windows_pct, team_size, urgency_weeks):
    devices_per_staff = device_count / max(1, team_size)
    is_small = device_count < 100

    disc_detail = DISCOVERY_BY_SOURCE.get(source, DISCOVERY_BY_SOURCE["Other"])
    phases = []

    # ── CRITICAL (4 weeks): no pilot, single compressed wave ──────────────────
    if urgency_weeks <= 4:
        disc_suffix = " Scope limited to critical policies only — full audit deferred post-migration."
        phases.append({
            "Phase": "1 — Discovery + Target Setup (parallel)",
            "Scope": os_scope(device_count, macos_pct, windows_pct, targets),
            "Duration (wks)": 0.5,
            "Key Actions": disc_detail + disc_suffix + f" Simultaneously configure {', '.join(targets)}, pre-stage all enrollment profiles, and brief IT staff on compressed runbook.",
            "Risk Level": "Low",
            "Rollback": f"N/A — {source} unchanged",
        })
        phases.append({
            "Phase": "2 — Full Migration (all devices)",
            "Scope": os_scope(device_count, macos_pct, windows_pct, targets),
            "Duration (wks)": max(1, urgency_weeks - 1),
            "Key Actions": (
                f"No dedicated pilot — first 10 devices serve as live validation checkpoint before proceeding. "
                f"{wave_actions(targets, 1)} "
                f"Executive devices handled 1:1 inline during this wave. All IT staff dedicated full-time. "
                f"Compliance reviewed at end of each day; rollback threshold: >10% enrollment failures."
            ),
            "Risk Level": scale_risk("High", devices_per_staff),
            "Rollback": f"{source} remains active; re-enroll failed devices immediately",
        })
        phases.append({
            "Phase": "3 — Validate & Decommission",
            "Scope": source,
            "Duration (wks)": 0.5,
            "Key Actions": decom_actions(source) + " Conduct rapid post-migration compliance check across all devices before license cancellation.",
            "Risk Level": "Low",
            "Rollback": "Maintain source MDM licenses minimum 30 days post-cutover",
        })

    # ── HIGH (6 weeks): minimal pilot, single main wave ───────────────────────
    elif urgency_weeks == 6:
        pilot = max(5, int(device_count * 0.03)) if not is_small else max(3, int(device_count * 0.05))
        exec_pool = max(3, int(device_count * 0.05))
        main_wave = device_count - pilot - exec_pool
        w_main = scaled_wave_weeks(max(2, urgency_weeks - 3), main_wave, team_size)

        phases.append({
            "Phase": "1 — Discovery & Inventory",
            "Scope": os_scope(device_count, macos_pct, windows_pct, targets),
            "Duration (wks)": 1,
            "Key Actions": disc_detail,
            "Risk Level": "Low",
            "Rollback": "N/A — source MDM unchanged",
        })
        phases.append({
            "Phase": "2 — Pilot Group",
            "Scope": scope_label(pilot, "3% — early adopters"),
            "Duration (wks)": scaled_wave_weeks(1, pilot, team_size),
            "Key Actions": pilot_actions(targets) + " Abbreviated observation window — 2 business days of compliance data required before proceeding.",
            "Risk Level": "Low",
            "Rollback": f"Re-enroll pilot devices in {source}",
        })
        phases.append({
            "Phase": "3 — Full Wave (all remaining non-exec)",
            "Scope": os_scope(main_wave, macos_pct, windows_pct, targets),
            "Duration (wks)": w_main,
            "Key Actions": wave_actions(targets, 1),
            "Risk Level": scale_risk("High", devices_per_staff),
            "Rollback": f"Re-enroll in {source}; policies still active",
        })
        phases.append({
            "Phase": "4 — Executive Devices",
            "Scope": scope_label(exec_pool, "5% — VIPs last"),
            "Duration (wks)": 1,
            "Key Actions": "1:1 IT support sessions with white-glove enrollment. Pre-stage device in new MDM before session. Validate VPN, email, and key app access before closing ticket.",
            "Risk Level": scale_risk("High", devices_per_staff),
            "Rollback": f"Immediate rollback via {source}; dedicated exec support active",
        })
        phases.append({
            "Phase": "5 — Decommission Source MDM",
            "Scope": source,
            "Duration (wks)": 1,
            "Key Actions": decom_actions(source),
            "Risk Level": "Low",
            "Rollback": "Keep source MDM licenses active 30 days post-cutover",
        })

    # ── MEDIUM (8 weeks): structure scales with team capacity ─────────────────
    elif urgency_weeks == 8:
        if is_small or devices_per_staff < 25:
            # Small org or well-staffed large org: single wave, compressed
            pilot = max(3, int(device_count * 0.05))
            exec_pool = 0 if is_small else max(3, int(device_count * 0.05))
            main_wave = device_count - pilot - exec_pool
            w_main = scaled_wave_weeks(2, main_wave, team_size)
            pilot_weeks = scaled_wave_weeks(1, pilot, team_size)

            phases.append({
                "Phase": "1 — Discovery & Inventory",
                "Scope": os_scope(device_count, macos_pct, windows_pct, targets),
                "Duration (wks)": scaled_wave_weeks(1, device_count, team_size),
                "Key Actions": disc_detail,
                "Risk Level": "Low",
                "Rollback": "N/A — source MDM unchanged",
            })
            phases.append({
                "Phase": "2 — Pilot Group",
                "Scope": scope_label(pilot, "5% sample"),
                "Duration (wks)": pilot_weeks,
                "Key Actions": pilot_actions(targets),
                "Risk Level": "Low",
                "Rollback": f"Re-enroll pilot devices in {source}",
            })
            exec_note = " Exec devices handled 1:1 at end of wave." if exec_pool == 0 else ""
            phases.append({
                "Phase": "3 — Full Migration",
                "Scope": os_scope(main_wave, macos_pct, windows_pct, targets),
                "Duration (wks)": w_main,
                "Key Actions": wave_actions(targets, 1) + exec_note,
                "Risk Level": scale_risk("Medium", devices_per_staff),
                "Rollback": f"Re-enroll in {source}; policies still active",
            })
            if exec_pool > 0:
                phases.append({
                    "Phase": "4 — Executive & Sensitive Devices",
                    "Scope": scope_label(exec_pool, "5% — VIPs last"),
                    "Duration (wks)": 0.5,
                    "Key Actions": "1:1 IT support sessions with white-glove enrollment. Pre-stage device before session. Validate VPN, email, and key app access.",
                    "Risk Level": scale_risk("High", devices_per_staff),
                    "Rollback": f"Immediate rollback via {source}; dedicated exec support line active",
                })
            phases.append({
                "Phase": f"{len(phases) + 1} — Decommission Source MDM",
                "Scope": source,
                "Duration (wks)": 1,
                "Key Actions": decom_actions(source),
                "Risk Level": "Low",
                "Rollback": "Keep source MDM licenses active 30 days post-cutover",
            })
        else:
            # Standard 2-wave structure for larger teams with higher load
            pilot = max(5, int(device_count * 0.05))
            exec_pool = max(5, int(device_count * 0.05))
            wave1 = int(device_count * 0.35)
            wave2 = max(0, device_count - pilot - exec_pool - wave1)

            remaining = max(2, urgency_weeks - 4)
            w1_base = max(1, remaining // 2)
            w2_base = max(1, remaining - w1_base)
            w1_weeks = scaled_wave_weeks(w1_base, wave1, team_size)
            w2_weeks = scaled_wave_weeks(w2_base, wave2, team_size)

            phases.append({
                "Phase": "1 — Discovery & Inventory",
                "Scope": os_scope(device_count, macos_pct, windows_pct, targets),
                "Duration (wks)": 1,
                "Key Actions": disc_detail,
                "Risk Level": "Low",
                "Rollback": "N/A — source MDM unchanged",
            })
            phases.append({
                "Phase": "2 — Pilot Group",
                "Scope": scope_label(pilot, "5% sample"),
                "Duration (wks)": 1,
                "Key Actions": pilot_actions(targets),
                "Risk Level": "Low",
                "Rollback": f"Re-enroll pilot devices in {source}",
            })
            phases.append({
                "Phase": "3 — Wave 1",
                "Scope": os_scope(wave1, macos_pct, windows_pct, targets) + " (35%)",
                "Duration (wks)": w1_weeks,
                "Key Actions": wave_actions(targets, 1),
                "Risk Level": scale_risk("Medium", devices_per_staff),
                "Rollback": f"Re-enroll in {source}; policies still active",
            })
            phases.append({
                "Phase": "4 — Wave 2",
                "Scope": os_scope(wave2, macos_pct, windows_pct, targets) + " (remaining non-exec)",
                "Duration (wks)": w2_weeks,
                "Key Actions": wave_actions(targets, 2),
                "Risk Level": scale_risk("Medium-High", devices_per_staff),
                "Rollback": f"Source MDM still running; rollback per-device via {source} console",
            })
            phases.append({
                "Phase": "5 — Executive & Sensitive Devices",
                "Scope": scope_label(exec_pool, "5% — VIPs last"),
                "Duration (wks)": 1,
                "Key Actions": "1:1 IT support sessions with white-glove enrollment. Pre-stage device in new MDM before session. Validate VPN, email, and key app access before closing ticket.",
                "Risk Level": scale_risk("High", devices_per_staff),
                "Rollback": f"Immediate rollback via {source}; dedicated exec support line active",
            })
            phases.append({
                "Phase": "6 — Decommission Source MDM",
                "Scope": source,
                "Duration (wks)": 1,
                "Key Actions": decom_actions(source),
                "Risk Level": "Low",
                "Rollback": "Keep source MDM licenses active 30 days post-cutover as safety net",
            })

    # ── LOW (12 weeks): training phase, extended pilot, 3 waves ──────────────
    else:
        pilot = max(10, int(device_count * 0.08))
        exec_pool = max(5, int(device_count * 0.05))
        wave1 = int(device_count * 0.25)
        wave2 = int(device_count * 0.30)
        wave3 = max(0, device_count - pilot - exec_pool - wave1 - wave2)

        remaining = max(3, urgency_weeks - 5)
        w1_base = max(1, remaining // 3)
        w2_base = max(1, remaining // 3)
        w3_base = max(1, remaining - w1_base - w2_base)
        w1_weeks = scaled_wave_weeks(w1_base, wave1, team_size)
        w2_weeks = scaled_wave_weeks(w2_base, wave2, team_size)
        w3_weeks = scaled_wave_weeks(w3_base, wave3, team_size) if wave3 > 0 else 0

        phases.append({
            "Phase": "1 — Discovery & Inventory",
            "Scope": os_scope(device_count, macos_pct, windows_pct, targets),
            "Duration (wks)": 1,
            "Key Actions": disc_detail,
            "Risk Level": "Low",
            "Rollback": "N/A — source MDM unchanged",
        })
        phases.append({
            "Phase": "2 — Target MDM Config & IT Training",
            "Scope": "IT team + target MDM tenant(s)",
            "Duration (wks)": 1,
            "Key Actions": (
                f"Fully configure {', '.join(targets)} — all profiles, app assignments, and compliance policies. "
                f"Train all IT staff on new MDM console(s). Document enrollment runbook, escalation matrix, "
                f"and rollback procedures. Conduct end-to-end enrollment test before pilot kick-off."
            ),
            "Risk Level": "Low",
            "Rollback": f"Source MDM {source} unchanged",
        })
        phases.append({
            "Phase": "3 — Extended Pilot",
            "Scope": scope_label(pilot, "8% — cross-functional volunteers"),
            "Duration (wks)": 2,
            "Key Actions": (
                pilot_actions(targets) +
                " Extended observation: collect minimum 5 business days of compliance telemetry. "
                "Conduct user feedback survey. Iterate on profile or app config issues before Wave 1."
            ),
            "Risk Level": "Low",
            "Rollback": f"Re-enroll pilot devices in {source}",
        })
        phases.append({
            "Phase": "4 — Wave 1",
            "Scope": os_scope(wave1, macos_pct, windows_pct, targets) + " (25%)",
            "Duration (wks)": w1_weeks,
            "Key Actions": wave_actions(targets, 1),
            "Risk Level": scale_risk("Low", devices_per_staff),
            "Rollback": f"Re-enroll in {source}; policies still active",
        })
        phases.append({
            "Phase": "5 — Wave 2",
            "Scope": os_scope(wave2, macos_pct, windows_pct, targets) + " (30%)",
            "Duration (wks)": w2_weeks,
            "Key Actions": wave_actions(targets, 2),
            "Risk Level": scale_risk("Medium", devices_per_staff),
            "Rollback": f"Source MDM still running; rollback per-device via {source} console",
        })
        if wave3 > 0:
            phases.append({
                "Phase": "6 — Wave 3",
                "Scope": os_scope(wave3, macos_pct, windows_pct, targets) + " (remaining non-exec)",
                "Duration (wks)": w3_weeks,
                "Key Actions": wave_actions(targets, 3),
                "Risk Level": scale_risk("Medium", devices_per_staff),
                "Rollback": f"Source MDM still running; rollback per-device via {source} console",
            })
        exec_num = len(phases) + 1
        phases.append({
            "Phase": f"{exec_num} — Executive & Sensitive Devices",
            "Scope": scope_label(exec_pool, "5% — VIPs last"),
            "Duration (wks)": 1,
            "Key Actions": "1:1 IT support sessions with white-glove enrollment. Pre-stage device in new MDM before session. Validate VPN, email, and key app access before closing ticket.",
            "Risk Level": scale_risk("Medium", devices_per_staff),
            "Rollback": f"Immediate rollback via {source}; dedicated exec support line active",
        })
        decom_num = exec_num + 1
        phases.append({
            "Phase": f"{decom_num} — Decommission Source MDM",
            "Scope": source,
            "Duration (wks)": 1,
            "Key Actions": decom_actions(source),
            "Risk Level": "Low",
            "Rollback": "Keep source MDM licenses active 30 days post-cutover as safety net",
        })

    return pd.DataFrame(phases)


# ── Risk matrix ───────────────────────────────────────────────────────────────

def build_risk_flags(source, targets, device_count, macos_pct, windows_pct, team_size, urgency_weeks):
    flags = []
    ts = target_str(targets)
    devices_per_staff = device_count / max(1, team_size)

    if urgency_weeks <= 4:
        flags.append(("error", "Critical urgency: no dedicated pilot phase — first 10 devices are live validation. Ensure rollback is tested and documented before Day 1."))
    elif urgency_weeks == 6:
        flags.append(("warning", "High urgency: abbreviated pilot (3%) and single main wave — limited recovery time if enrollment issues surface mid-wave."))

    if "Workspace ONE" in source and "Intune" in ts:
        flags.append(("warning", "Conditional Access policy conflicts likely if Okta device trust is active — audit CA policies before Wave 1"))
    if "Workspace ONE" in source and "Jamf" in ts:
        flags.append(("warning", "ADE re-enrollment required for all macOS devices — confirm Apple Business Manager MDM server assignment is updated"))
    if "Workspace ONE" in source and "Kandji" in ts:
        flags.append(("warning", "ADE re-enrollment required for macOS — Kandji Blueprint must be pre-configured in ABM before Wave 1"))
    if "MobileIron" in source:
        flags.append(("warning", "MobileIron uses proprietary SCEP/NDES for cert delivery — audit certificate dependencies before migration"))
    if "Kandji" in ts:
        flags.append(("warning", "Apple Business Manager blueprint migration required — all devices must be unassigned from current MDM server in ABM first"))
    if has_split(targets):
        flags.append(("warning", "Dual-platform target (Jamf + Intune) — enforce strict platform tagging in Okta groups to prevent policy drift"))

    if windows_pct >= 30 and not has_intune(targets):
        flags.append(("error", f"{windows_pct}% of devices are Windows but no Intune target selected — Windows devices will be unmanaged after migration"))
    if macos_pct >= 30 and not has_jamf(targets) and not has_kandji(targets):
        flags.append(("error", f"{macos_pct}% of devices are macOS but no Jamf/Kandji target selected — macOS devices will be unmanaged after migration"))

    if devices_per_staff > 200:
        flags.append(("error", f"Team capacity risk: {device_count} devices / {team_size} staff = {devices_per_staff:.0f} devices per person — strongly recommend adding staff or extending timeline"))
    elif devices_per_staff > 100:
        flags.append(("warning", f"Team load is high: {devices_per_staff:.0f} devices per staff member — wave durations have been extended automatically"))

    flags.append(("info", "Executive devices should always be migrated last with a dedicated 1:1 support window"))
    return flags


# ── Cutover checklist (dynamic based on targets) ──────────────────────────────

def build_checklist(targets):
    items = [
        "All devices enrolled in new MDM and reporting compliant",
        "Okta device trust updated to new MDM integration",
        "Software push validated for top 10 apps",
    ]
    if has_jamf(targets) or has_kandji(targets):
        items.append("FileVault key escrow confirmed in new MDM (Jamf/Kandji)")
    if has_intune(targets):
        items.append("BitLocker key escrow confirmed in Microsoft Intune")
    items += [
        "Help desk trained on new MDM console(s)",
        "Rollback playbook documented and reviewed by team",
        "Exec devices migrated with 1:1 support confirmed",
        "Source MDM license cancellation date set (30 days post-cutover)",
    ]
    if has_split(targets):
        items.append("Platform-based Okta group rules validated — macOS → Jamf/Kandji, Windows → Intune")
    if has_intune(targets):
        items.append("Windows Autopilot deployment profiles assigned to correct AAD groups")
    if has_kandji(targets):
        items.append("Kandji Blueprint assignments validated in Apple Business Manager")
    return items


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("MDM Migration Planner")

if not targets:
    st.info("Select at least one target platform in the sidebar to generate a plan.")
else:
    devices_per_staff = device_count / max(1, team_size)
    mac_count = int(device_count * macos_pct / 100)
    win_count = device_count - mac_count

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Devices", device_count)
    c2.metric("macOS / Windows", f"{mac_count} / {win_count}")
    c3.metric("Team Size", team_size)
    c4.metric("Timeline", f"{urgency_weeks} weeks")

    if devices_per_staff > 100:
        st.warning(f"**Capacity notice:** {devices_per_staff:.0f} devices per staff member — wave durations auto-extended.")

    st.subheader("Migration Timeline")
    df = build_phase_table(source, targets, device_count, macos_pct, windows_pct, team_size, urgency_weeks)
    st.dataframe(df, use_container_width=True, hide_index=True)

    total_wks = df["Duration (wks)"].sum()
    total_display = f"{total_wks:.1f}".rstrip("0").rstrip(".")
    st.caption(f"Total projected duration: **{total_display} weeks** | {len(df)} phases | {source} → {', '.join(targets)}")

    st.subheader("Risk Matrix")
    flags = build_risk_flags(source, targets, device_count, macos_pct, windows_pct, team_size, urgency_weeks)
    flag_texts = []
    for severity, msg in flags:
        if severity == "error":
            st.error(msg)
        elif severity == "warning":
            st.warning(msg)
        else:
            st.info(msg)
        flag_texts.append(f"- [{severity.upper()}] {msg}")

    st.subheader("Cutover Checklist")
    for item in build_checklist(targets):
        st.checkbox(item, value=False, disabled=True, key=f"check_{item}")

    st.subheader("Export")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download Migration Plan as CSV",
            data=df.to_csv(index=False),
            file_name="mdm_migration_plan.csv",
            mime="text/csv",
        )
    with col2:
        risk_md = (
            f"# MDM Migration Risk Summary\n\n"
            f"**Source:** {source}  \n"
            f"**Targets:** {', '.join(targets)}  \n"
            f"**Devices:** {device_count} ({mac_count} macOS / {win_count} Windows)  \n"
            f"**Team size:** {team_size}  \n"
            f"**Timeline:** {urgency_weeks} weeks\n\n"
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
