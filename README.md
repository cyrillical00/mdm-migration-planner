# MDM Migration Planner

A structured planning tool for MDM migrations. Input your current environment and get a phased migration timeline, risk flag matrix, and a pre-populated cutover checklist — all offline, no API keys required.

Demonstrates 550-device Workspace ONE → Intune/Jamf migration expertise.

![Screenshot placeholder](screenshot.png)

## Features

- Source/target platform selector (Workspace ONE, Jamf, Intune, Kandji, and more)
- Phased timeline scaled to urgency (4–12 weeks)
- Platform-specific risk flags (ADE re-enrollment, Conditional Access conflicts, etc.)
- Pre-populated cutover checklist
- CSV and Markdown export

## Local Setup

```bash
git clone https://github.com/cyrillical00/mdm-migration-planner
cd mdm-migration-planner
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/cloud)

No secrets required — deploy directly.

---

Built by [Oleg Strutsovski](https://linkedin.com/in/olegst)
