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
    .stDataFrame {{ background-color: white; border-radius: 5px; }}
    .reval-card {{ background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid white; margin-bottom: 10px; }}
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

# --- 3. LOGIN & NAV ---
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

    # --- 4. AGENT VIEW (FIXED TABLE & WEEKLY FILTER) ---
    if choice == "Audit View":
        st.header("📊 Your Published Audits")
        df = st.session_state.audit_logs[st.session_state.audit_logs['Status'].isin(['Published', 'Re-validation Requested'])].copy()
        
        if df.empty:
            st.info("No published audits found.")
        else:
            c1, c2 = st.columns(2)
            sel_week = c1.selectbox("Filter Week", ["All"] + sorted(list(df['Week'].unique().astype(str))))
            sel_chan = c2.selectbox("Filter Channel", ["All"] + list(df['Channel'].unique()))
            
            if sel_week != "All": df = df[df['Week'].astype(str) == sel_week]
            if sel_chan != "All": df = df[df['Channel'] == sel_chan]

            # Display Table
            fixed_cols = ['Week', 'Channel', 'Eval_ID', 'Interaction Date', 'Total Score']
            all_params = st.session_state.param_db['Parameter'].unique().tolist()
            display_cols = fixed_cols + [p for p in all_params if p in df.columns]
            
            st.dataframe(df[display_cols], use_container_width=True)

            # Re-validation Request Section
            st.divider()
            st.subheader("Challenge an Audit")
            audit_to_rev = st.selectbox("Select Audit ID to Re-validate", [""] + df['Eval_ID'].tolist())
            
            if audit_to_rev:
                row = df[df['Eval_ID'] == audit_to_rev].iloc[0]
                # Filter params that have 0 score
                zero_params = [p for p in all_params if p in row and "0 (" in str(row[p])]
                
                if zero_params:
                    with st.form("rev_form"):
                        reasons = {}
                        for p in zero_params:
                            reasons[p] = st.text_input(f"Reason for {p}", key=f"re_{p}")
                        if st.form_submit_button("Submit Challenge"):
                            idx = df[df['Eval_ID'] == audit_to_rev].index[0]
                            st.session_state.audit_logs.at[idx, 'Status'] = 'Re-validation Requested'
                            st.session_state.audit_logs.at[idx, 'Reval_Reasons'] = str(reasons)
                            save_data(st.session_state.audit_logs, AUDIT_FILE)
                            st.success("Request sent!")
                            st.rerun()
                else:
                    st.write("No '0' score parameters found in this audit.")

    # --- 5. QA RE-VALIDATION (ACCEPT/REJECT LOGIC) ---
    elif choice == "Re-Validation":
        st.header("⚖️ Re-Validation Requests")
        requests = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Re-validation Requested']
        
        if requests.empty:
            st.info("No pending requests.")
        else:
            for idx, row in requests.iterrows():
                with st.container():
                    st.markdown(f'<div class="reval-card"><h4>Audit: {row["Eval_ID"]} | Agent: {row["Agent Name"]}</h4>', unsafe_allow_html=True)
                    reasons = eval(row['Reval_Reasons'])
                    
                    for p, r in reasons.items():
                        st.write(f"**Parameter:** {p} | **Agent's Reason:** {r}")
                        col1, col2 = st.columns(5)
                        
                        if col1.button("✅ Accept", key=f"acc_{idx}_{p}"):
                            # Update to max score
                            max_val = st.session_state.param_db[st.session_state.param_db['Parameter'] == p]['Max_Score'].values[0]
                            st.session_state.audit_logs.at[idx, p] = max_val
                            
                            # CLEAN CALCULATION: Recalculate total accurately
                            all_p = st.session_state.param_db[st.session_state.param_db['Channel'] == row['Channel']]['Parameter'].tolist()
                            new_total = sum([ (float(st.session_state.audit_logs.at[idx, param]) if not isinstance(st.session_state.audit_logs.at[idx, param], str) else 0) for param in all_p if param in st.session_state.audit_logs.columns])
                            
                            st.session_state.audit_logs.at[idx, 'Total Score'] = new_total
                            st.session_state.audit_logs.at[idx, 'Status'] = 'Published'
                            save_data(st.session_state.audit_logs, AUDIT_FILE)
                            st.success("Score Updated!")
                            st.rerun()
                            
                        if col2.button("❌ Reject", key=f"rej_{idx}_{p}"):
                            st.session_state.audit_logs.at[idx, 'Status'] = 'Published' # No change in score
                            save_data(st.session_state.audit_logs, AUDIT_FILE)
                            st.warning("Challenge Rejected.")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. REMAINING FEATURES (CLEANED) ---
    elif choice == "QA Audit Entry":
        st.header("📝 New Audit Entry")
        sel_ch = st.selectbox("Select Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        active_agents = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_ch) & (st.session_state.agent_db['Status'] == 'Active')]
        
        c1, c2 = st.columns(2)
        ag_nm = c1.selectbox("Agent", [""] + active_agents['Name'].tolist())
        int_id = c2.text_input("Interaction ID")
        
        st.divider()
        all_p = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_ch]
        scores = {}
        
        for _, r in all_p.iterrows():
            st.write(f"**{r['Parameter']}** (Max: {r['Max_Score']})")
            dm = st.checkbox("Demark", key=f"dm_{r['Parameter']}")
            if dm:
                reason = st.text_input("Demark Reason", key=f"dr_{r['Parameter']}")
                scores[r['Parameter']] = f"0 ({reason})"
            else:
                scores[r['Parameter']] = r['Max_Score']
        
        if st.button("Save Audit", type="primary"):
            entry = {'Week': datetime.now().isocalendar()[1], 'Agent Name': ag_nm, 'Channel': sel_ch, 'Eval_ID': int_id, 'Status': 'Pending', 'Interaction Date': str(datetime.now().date())}
            entry.update(scores)
            # Safe calculation
            entry['Total Score'] = sum([v if isinstance(v, (int, float)) else 0 for v in scores.values()])
            st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
            save_data(st.session_state.audit_logs, AUDIT_FILE)
            st.success("Saved!")

    elif choice == "Publish Audits":
        st.header("📢 Publish Pending Audits")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        st.dataframe(pending)
        if st.button("Publish All"):
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Publish_Time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
            save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()

    elif choice == "Audit Parameters":
        st.header("⚙️ Parameter Setup")
        with st.form("p_f"):
            pc, ps = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"]), st.selectbox("Skill", ["Soft Skill", "Service Skill"])
            pn, pm = st.text_input("Parameter Name"), st.number_input("Max Score", min_value=1)
            if st.form_submit_button("Add"):
                new_p = pd.DataFrame([[pc, ps, pn, pm]], columns=param_cols)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                save_data(st.session_state.param_db, PARAM_FILE); st.rerun()
