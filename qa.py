import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. UI & STYLING ---
PATHAO_RED = "#ED1C24"
st.set_page_config(page_title="Pathao Quality Tool", layout="wide")

st.markdown(f"""
<style>
    .stApp {{ background-color: {PATHAO_RED}; color: white; }}
    @import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;700&family=Comic+Sans+MS&display=swap');
    html, body, [class*="st-"] {{ font-family: "Comic Sans MS", "Anek Bangla", sans-serif !important; font-size: 13px; }}
    div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {{
        background-color: #000000 !important; color: white !important; border: 1px solid white !important; font-size: 12px !important;
    }}
    label, .stMarkdown p {{ color: white !important; font-weight: bold; }}
    button[kind="primary"] {{ background-color: white !important; color: {PATHAO_RED} !important; border-radius: 4px; font-weight: bold; }}
    .skill-header {{ background-color: #1e1e1e; padding: 10px; border-radius: 5px; border: 1px solid white; text-align: center; margin-bottom: 15px; }}
    .param-row {{ background-color: #2b2b2b; padding: 8px; border-radius: 5px; margin-bottom: 8px; border-left: 4px solid white; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATA HANDLER ---
AGENT_FILE, PARAM_FILE, AUDIT_FILE = "agents.csv", "parameters.csv", "audit_logs.csv"
param_cols = ['Channel', 'Skill_Type', 'Parameter', 'Max_Score']

def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df if not df.empty else pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

if 'agent_db' not in st.session_state: st.session_state.agent_db = load_data(AGENT_FILE, [])
if 'param_db' not in st.session_state: st.session_state.param_db = load_data(PARAM_FILE, param_cols)
if 'audit_logs' not in st.session_state: st.session_state.audit_logs = load_data(AUDIT_FILE, [])
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. NAVIGATION ---
if not st.session_state.logged_in:
    st.title("Pathao Quality Portal")
    with st.form("login"):
        role = st.selectbox("Role", ["Admin", "QA", "Agent"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
            if pwd == "1234":
                st.session_state.update({"logged_in": True, "role": role})
                st.rerun()
            else: st.error("Access Denied")
else:
    nav = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs"],
        "QA": ["QA Audit Entry", "Publish Audits", "Re-Validation", "Audit Logs"],
        "Agent": ["Audit View"]
    }
    choice = st.sidebar.selectbox("Navigate", nav[st.session_state.role])
    if st.sidebar.button("Logout"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- 4. QA AUDIT ENTRY (SIDE BY SIDE TABLES FIXED) ---
    if choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        sel_ch = st.selectbox("Select Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        active_agents = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_ch) & (st.session_state.agent_db['Status'] == 'Active')]
        
        c1, c2, c3 = st.columns(3)
        ag_nm = c1.selectbox("Agent Name", [""] + active_agents['Name'].tolist())
        int_id = c2.text_input("Interaction ID")
        feedback = st.text_area("QA Feedback")
        
        st.divider()
        left_col, right_col = st.columns(2)
        all_p = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_ch]
        scores = {}

        with left_col:
            st.markdown('<div class="skill-header"><h3>🛡️ Soft Skill</h3></div>', unsafe_allow_html=True)
            for _, r in all_p[all_p['Skill_Type'] == 'Soft Skill'].iterrows():
                st.markdown(f'<div class="param-row"><b>{r["Parameter"]}</b> (Max: {r["Max_Score"]})', unsafe_allow_html=True)
                dm = st.checkbox("Demark", key=f"dm_{r['Parameter']}")
                scores[r['Parameter']] = f"0 ({st.text_input('Reason', key=f'res_{r.Parameter}')})" if dm else r['Max_Score']
                st.markdown('</div>', unsafe_allow_html=True)

        with right_col:
            st.markdown('<div class="skill-header"><h3>🛠️ Service Skill</h3></div>', unsafe_allow_html=True)
            for _, r in all_p[all_p['Skill_Type'] == 'Service Skill'].iterrows():
                st.markdown(f'<div class="param-row"><b>{r["Parameter"]}</b> (Max: {r["Max_Score"]})', unsafe_allow_html=True)
                dm = st.checkbox("Demark", key=f"dm_{r['Parameter']}")
                scores[r['Parameter']] = f"0 ({st.text_input('Reason', key=f'res_{r.Parameter}')})" if dm else r['Max_Score']
                st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Submit Audit", type="primary", use_container_width=True):
            entry = {'Week': datetime.now().isocalendar()[1], 'Agent Name': ag_nm, 'Channel': sel_ch, 'Eval_ID': int_id, 'Status': 'Pending', 'Interaction Date': str(datetime.now().date()), 'QA Feedback': feedback}
            entry.update(scores)
            entry['Total Score'] = sum([v if isinstance(v, (int, float)) else 0 for v in scores.values()])
            st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
            save_data(st.session_state.audit_logs, AUDIT_FILE)
            st.success("Audit Recorded!")

    # --- 5. PUBLISH AUDITS (ONLY PENDING) ---
    elif choice == "Publish Audits":
        st.header("📢 Pending Publications")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        if not pending.empty:
            st.dataframe(pending, use_container_width=True)
            if st.button("Publish All Audits"):
                st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Publish_Time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
                save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()
        else: st.info("No pending audits to publish.")

    # --- 6. AGENT VIEW (FILTER & REVAL BUTTON LOGIC FIXED) ---
    elif choice == "Audit View":
        st.header("🔎 Agent Performance View")
        df = st.session_state.audit_logs[st.session_state.audit_logs['Status'].isin(['Published', 'Re-validation Requested'])].copy()
        
        c1, c2 = st.columns(2)
        f_week = c1.selectbox("Select Week", ["All"] + sorted(list(df['Week'].unique().astype(str))))
        f_name = c2.selectbox("Select Agent Name", ["All"] + list(df['Agent Name'].unique()))
        
        if f_week != "All": df = df[df['Week'].astype(str) == f_week]
        if f_name != "All": df = df[df['Agent Name'] == f_name]
        
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("Action Center")
        for idx, row in df.iterrows():
            # Button visible ONLY if score < 100 and Status is Published
            if row['Total Score'] < 100 and row['Status'] == 'Published':
                if st.button(f"Re-validate Audit: {row['Eval_ID']}", key=f"rev_btn_{idx}"):
                    st.session_state.target_eval = row['Eval_ID']
        
        if 'target_eval' in st.session_state:
            target = df[df['Eval_ID'] == st.session_state.target_eval].iloc[0]
            with st.form("reval_form_agent"):
                st.write(f"Challenging Audit: {st.session_state.target_eval}")
                # Only show 0 score parameters
                zero_p = [p for p in st.session_state.param_db['Parameter'].unique() if p in target and "0 (" in str(target[p])]
                reasons = {p: st.text_input(f"Why {p}?", key=f"txt_{p}") for p in zero_p}
                if st.form_submit_button("Submit Challenge"):
                    m_idx = st.session_state.audit_logs[st.session_state.audit_logs['Eval_ID'] == st.session_state.target_eval].index[0]
                    st.session_state.audit_logs.at[m_idx, 'Status'] = 'Re-validation Requested'
                    st.session_state.audit_logs.at[m_idx, 'Reval_Reasons'] = str(reasons)
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    del st.session_state.target_eval
                    st.rerun()

    # --- 7. AUDIT LOGS (ALL AUDITS) ---
    elif choice == "Audit Logs":
        st.header("📜 Master Audit Logs (All Status)")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)

    # --- 8. QA RE-VALIDATION (ACCEPT/REJECT) ---
    elif choice == "Re-Validation":
        st.header("⚖️ QA Decision Panel")
        reqs = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Re-validation Requested']
        for idx, row in reqs.iterrows():
            with st.expander(f"Request from {row['Agent Name']} (ID: {row['Eval_ID']})"):
                reasons = eval(row['Reval_Reasons'])
                for p, r in reasons.items():
                    st.write(f"**Parameter:** {p} | **Agent Logic:** {r}")
                    c1, c2 = st.columns(5)
                    if c1.button("Accept ✅", key=f"acc_{idx}_{p}"):
                        max_v = st.session_state.param_db[st.session_state.param_db['Parameter'] == p]['Max_Score'].values[0]
                        st.session_state.audit_logs.at[idx, p] = max_v
                        # Recalculate Total
                        param_list = st.session_state.param_db['Parameter'].tolist()
                        new_total = sum([v if isinstance(v, (int, float)) else 0 for v in st.session_state.audit_logs.loc[idx, st.session_state.audit_logs.columns.intersection(param_list)]])
                        st.session_state.audit_logs.at[idx, 'Total Score'] = new_total
                        st.session_state.audit_logs.at[idx, 'Status'] = 'Published'
                        save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()
                    if c2.button("Reject ❌", key=f"rej_{idx}_{p}"):
                        st.session_state.audit_logs.at[idx, 'Status'] = 'Published'
                        save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()
