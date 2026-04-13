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
        background-color: #000000 !important; color: white !important; border: 1px solid white !important;
    }}
    label, .stMarkdown p {{ color: white !important; font-weight: bold; }}
    .skill-header {{ background-color: #1e1e1e; padding: 10px; border-radius: 5px; border: 1px solid white; text-align: center; margin-bottom: 15px; }}
    .param-row {{ background-color: #2b2b2b; padding: 8px; border-radius: 5px; margin-bottom: 8px; border-left: 4px solid white; }}
    .reval-box {{ background-color: #000000; padding: 15px; border-radius: 10px; border: 2px solid #FFD700; margin-top: 10px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATA HANDLER ---
AGENT_FILE, PARAM_FILE, AUDIT_FILE, TRAINING_FILE = "agents.csv", "parameters.csv", "audit_logs.csv", "training_logs.csv"
param_cols = ['Channel', 'Skill_Type', 'Parameter', 'Max_Score']
training_cols = ['Date', 'Time', 'Channel', 'Agent Name', 'EMP ID', 'Topic', 'Feedback']

def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df if not df.empty else pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

# Session State Initialization
if 'agent_db' not in st.session_state: st.session_state.agent_db = load_data(AGENT_FILE, ['Name', 'EMP ID', 'Channel', 'Status'])
if 'param_db' not in st.session_state: st.session_state.param_db = load_data(PARAM_FILE, param_cols)
if 'audit_logs' not in st.session_state: st.session_state.audit_logs = load_data(AUDIT_FILE, [])
if 'training_logs' not in st.session_state: st.session_state.training_logs = load_data(TRAINING_FILE, training_cols)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
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
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs", "Agent Training"],
        "QA": ["QA Audit Entry", "Publish Audits", "Re-Validation", "Agent Training", "Audit Logs"],
        "Agent": ["Audit View"]
    }
    choice = st.sidebar.selectbox("Navigate", nav[st.session_state.role])
    if st.sidebar.button("Logout"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- 4. QA AUDIT ENTRY ---
    if choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        sel_ch = st.selectbox("Select Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        active_agents = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_ch) & (st.session_state.agent_db['Status'] == 'Active')]
        
        c1, c2 = st.columns(2)
        ag_nm = c1.selectbox("Agent Name", [""] + active_agents['Name'].tolist())
        int_id = c2.text_input("Interaction ID")
        
        st.divider()
        left_col, right_col = st.columns(2)
        all_p = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_ch]
        scores = {}

        with left_col:
            st.markdown('<div class="skill-header"><h3>🛡️ Soft Skill</h3></div>', unsafe_allow_html=True)
            for _, r in all_p[all_p['Skill_Type'] == 'Soft Skill'].iterrows():
                st.markdown(f'<div class="param-row"><b>{r["Parameter"]}</b> (Max: {r["Max_Score"]})', unsafe_allow_html=True)
                dm = st.checkbox("Demark", key=f"dm_{r['Parameter']}")
                if dm:
                    reason = st.text_input(f"Reason for {r['Parameter']}", key=f"res_{r['Parameter']}")
                    scores[r['Parameter']] = f"0 ({reason})"
                else: scores[r['Parameter']] = r['Max_Score']
                st.markdown('</div>', unsafe_allow_html=True)

        with right_col:
            st.markdown('<div class="skill-header"><h3>🛠️ Service Skill</h3></div>', unsafe_allow_html=True)
            for _, r in all_p[all_p['Skill_Type'] == 'Service Skill'].iterrows():
                st.markdown(f'<div class="param-row"><b>{r["Parameter"]}</b> (Max: {r["Max_Score"]})', unsafe_allow_html=True)
                dm = st.checkbox("Demark", key=f"dm_{r['Parameter']}")
                if dm:
                    reason = st.text_input(f"Reason for {r['Parameter']}", key=f"res_{r['Parameter']}")
                    scores[r['Parameter']] = f"0 ({reason})"
                else: scores[r['Parameter']] = r['Max_Score']
                st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Submit Audit", type="primary", use_container_width=True):
            entry = {'Week': datetime.now().isocalendar()[1], 'Agent Name': ag_nm, 'Channel': sel_ch, 'Eval_ID': int_id, 'Status': 'Pending', 'Interaction Date': str(datetime.now().date())}
            entry.update(scores)
            entry['Total Score'] = sum([v if isinstance(v, (int, float)) else 0 for v in scores.values()])
            st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
            save_data(st.session_state.audit_logs, AUDIT_FILE)
            st.success("Audit Recorded!")

    # --- 5. AGENT TRAINING LOG (NEWLY ADDED & UPDATED) ---
    elif choice == "Agent Training":
        st.header("🎓 Agent Training Log")
        
        if st.session_state.agent_db.empty:
            st.warning("Please add Agent Details first in the Admin section.")
        else:
            with st.form("training_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                
                # Channel selection filters agents
                channels = sorted(st.session_state.agent_db['Channel'].unique().tolist())
                sel_chan = c1.selectbox("Select Channel", channels)
                
                # Filter agents by channel
                filtered_agents = st.session_state.agent_db[st.session_state.agent_db['Channel'] == sel_chan]
                sel_agent_name = c2.selectbox("Select Agent Name", filtered_agents['Name'].tolist())
                
                # Auto-get EMP ID
                emp_id = filtered_agents[filtered_agents['Name'] == sel_agent_name]['EMP ID'].values[0]
                
                st.info(f"📍 Agent: **{sel_agent_name}** | EMP ID: **{emp_id}**")
                
                c3, c4 = st.columns(2)
                t_date = c3.date_input("Training Date", value=datetime.now().date())
                t_time = c4.text_input("Training Time (e.g., 10:30 AM)")
                
                topic = st.text_input("Training Topic")
                feedback = st.text_area("Agent Feedback")
                
                if st.form_submit_button("Save Training Session", type="primary"):
                    new_log = pd.DataFrame([[str(t_date), t_time, sel_chan, sel_agent_name, emp_id, topic, feedback]], columns=training_cols)
                    st.session_state.training_logs = pd.concat([st.session_state.training_logs, new_log], ignore_index=True)
                    save_data(st.session_state.training_logs, TRAINING_FILE)
                    st.success("Training Log Saved Successfully!")

            # Display Recent Logs
            st.subheader("📋 Recent Training Records")
            st.dataframe(st.session_state.training_logs.tail(10), use_container_width=True)

    # --- 6. AGENT VIEW ---
    elif choice == "Audit View":
        st.header("🔎 Agent Audit View")
        df = st.session_state.audit_logs[st.session_state.audit_logs['Status'].isin(['Published', 'Re-validation Requested'])].copy()
        
        c1, c2 = st.columns(2)
        f_week = c1.selectbox("Filter Week", ["All"] + sorted(list(df['Week'].unique().astype(str))))
        f_name = c2.selectbox("Filter Agent Name", ["All"] + list(df['Agent Name'].unique()))
        
        if f_week != "All": df = df[df['Week'].astype(str) == f_week]
        if f_name != "All": df = df[df['Agent Name'] == f_name]
        
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        audit_to_challenge = st.selectbox("Select Audit ID to Challenge/Re-validate", [""] + df[df['Total Score'] < 100]['Eval_ID'].tolist())
        
        if audit_to_challenge:
            row = df[df['Eval_ID'] == audit_to_challenge].iloc[0]
            st.markdown('<div class="reval-box">', unsafe_allow_html=True)
            st.subheader(f"Request Re-validation: {audit_to_challenge}")
            
            param_list = st.session_state.param_db['Parameter'].unique()
            zero_p = [p for p in param_list if p in row and "0 (" in str(row[p])]
            
            if not zero_p:
                st.info("No parameters with 0 score found.")
            else:
                with st.form("agent_reval_form"):
                    reval_data = {}
                    for p in zero_p:
                        reval_data[p] = st.text_area(f"Why challenge **{p}**?", key=f"agent_in_{p}")
                    
                    if st.form_submit_button("Submit Challenge"):
                        m_idx = st.session_state.audit_logs[st.session_state.audit_logs['Eval_ID'] == audit_to_challenge].index[0]
                        st.session_state.audit_logs.at[m_idx, 'Status'] = 'Re-validation Requested'
                        st.session_state.audit_logs.at[m_idx, 'Reval_Reasons'] = str(reval_data)
                        save_data(st.session_state.audit_logs, AUDIT_FILE)
                        st.success("Challenge Submitted!")
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # --- 7. RE-VALIDATION DECISION ---
    elif choice == "Re-Validation":
        st.header("⚖️ QA Re-Validation Decision")
        reqs = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Re-validation Requested']
        
        if reqs.empty:
            st.info("No pending re-validation requests.")
        else:
            for idx, row in reqs.iterrows():
                with st.expander(f"Audit: {row['Eval_ID']} | Agent: {row['Agent Name']}"):
                    reasons = eval(row['Reval_Reasons'])
                    for p, reason in reasons.items():
                        st.write(f"**Parameter:** {p}")
                        st.info(f"**Agent Logic:** {reason}")
                        
                        btn_c1, btn_c2 = st.columns([1, 4])
                        if btn_c1.button("✅ Accept", key=f"acc_{row['Eval_ID']}_{p}"):
                            max_val = st.session_state.param_db[st.session_state.param_db['Parameter'] == p]['Max_Score'].values[0]
                            st.session_state.audit_logs.at[idx, p] = max_val
                            st.session_state.audit_logs.at[idx, 'Status'] = 'Published'
                            save_data(st.session_state.audit_logs, AUDIT_FILE)
                            st.rerun()
                            
                        if btn_c2.button("❌ Reject", key=f"rej_{row['Eval_ID']}_{p}"):
                            st.session_state.audit_logs.at[idx, 'Status'] = 'Published'
                            save_data(st.session_state.audit_logs, AUDIT_FILE)
                            st.rerun()

    # --- 8. ADMIN PAGES ---
    elif choice == "Agent Details":
        st.header("👥 Agent Management")
        with st.form("agent_f"):
            c1, c2, c3 = st.columns(3)
            an = c1.text_input("Name")
            ae = c2.text_input("EMP ID")
            ac = c3.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            if st.form_submit_button("Add Agent"):
                new_a = pd.DataFrame([[an, ae, ac, 'Active']], columns=['Name', 'EMP ID', 'Channel', 'Status'])
                st.session_state.agent_db = pd.concat([st.session_state.agent_db, new_a], ignore_index=True)
                save_data(st.session_state.agent_db, AGENT_FILE); st.rerun()
        st.dataframe(st.session_state.agent_db, use_container_width=True)

    elif choice == "Publish Audits":
        st.header("📢 Publish Audits")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        st.dataframe(pending)
        if st.button("Publish All"):
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
            save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()

    elif choice == "Audit Logs":
        st.header("📜 Master Logs")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)

    elif choice == "Audit Parameters":
        st.header("⚙️ Parameters")
        with st.form("p_f"):
            c1, c2 = st.columns(2)
            pc, ps = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"]), c2.selectbox("Skill", ["Soft Skill", "Service Skill"])
            pn, pm = st.text_input("Name"), st.number_input("Max Score", min_value=1
