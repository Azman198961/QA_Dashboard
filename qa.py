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
        background-color: #000000 !important; color: {PATHAO_RED} !important; border: 1px solid white !important; font-size: 12px !important;
    }}
    label, .stMarkdown p {{ color: white !important; font-weight: bold; }}
    button[kind="primary"] {{ background-color: white !important; color: {PATHAO_RED} !important; border-radius: 4px; font-weight: bold; }}
    .skill-header {{ background-color: #1e1e1e; padding: 10px; border-radius: 5px; border: 1px solid white; text-align: center; margin-bottom: 15px; }}
    .param-row {{ background-color: #2b2b2b; padding: 8px; border-radius: 5px; margin-bottom: 8px; border-left: 4px solid white; }}
    .re-val-box {{ background-color: #333; padding: 15px; border-radius: 10px; border: 1px solid yellow; margin-top: 10px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATA HANDLER ---
AGENT_FILE, PARAM_FILE, AUDIT_FILE = "agents.csv", "parameters.csv", "audit_logs.csv"
agent_cols = ['ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status']
param_cols = ['Channel', 'Skill_Type', 'Parameter', 'Max_Score']

def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df if not df.empty else pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

if 'agent_db' not in st.session_state: st.session_state.agent_db = load_data(AGENT_FILE, agent_cols)
if 'param_db' not in st.session_state: st.session_state.param_db = load_data(PARAM_FILE, param_cols)
if 'audit_logs' not in st.session_state: st.session_state.audit_logs = load_data(AUDIT_FILE, [])
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
            else: st.error("Wrong Password")
else:
    st.sidebar.info(f"Active Role: {st.session_state.role}")
    nav = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs"],
        "QA": ["QA Audit Entry", "Publish Audits", "Re-Validation", "Audit Logs"],
        "Agent": ["Audit View"]
    }
    choice = st.sidebar.selectbox("Navigate", nav[st.session_state.role])
    if st.sidebar.button("Logout"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- AGENT: AUDIT VIEW & RE-VALIDATION ---
    if choice == "Audit View":
        st.header("📋 Your Published Audits")
        df = st.session_state.audit_logs.copy()
        published = df[df['Status'] == 'Published'].reset_index()

        if published.empty:
            st.info("No published audits found.")
        else:
            for idx, row in published.iterrows():
                with st.expander(f"Audit ID: {row['Eval_ID']} | Score: {row['Total Score']} | Date: {row['Interaction Date']}"):
                    st.write(row)
                    
                    # 48 Hours Logic
                    pub_time = datetime.strptime(str(row['Publish_Time']), "%Y-%m-%d %H:%M:%S") if 'Publish_Time' in row and pd.notnull(row['Publish_Time']) else datetime.now()
                    is_expired = datetime.now() > (pub_time + timedelta(hours=48))
                    
                    if not is_expired:
                        if st.button(f"Challenge / Re-validate Audit {row['Eval_ID']}", key=f"btn_{idx}"):
                            st.session_state.reval_id = row['Eval_ID']
                    else:
                        st.warning("Re-validation window (48h) has expired.")

            # Re-validation Form
            if 'reval_id' in st.session_state:
                st.markdown('<div class="re-val-box">', unsafe_allow_html=True)
                st.subheader(f"Request Re-validation for {st.session_state.reval_id}")
                target_audit = published[published['Eval_ID'] == st.session_state.reval_id].iloc[0]
                
                # Filter parameters where score is 0
                zero_params = [c for c in published.columns if "0 (" in str(target_audit[c])]
                
                if not zero_params:
                    st.write("No Demarked (0) parameters found to challenge.")
                else:
                    reval_reasons = {}
                    for p in zero_params:
                        reval_reasons[p] = st.text_area(f"Why should **{p}** be re-evaluated?", key=f"rev_{p}")
                    
                    if st.button("Submit Re-validation Request"):
                        # Update the main audit log with status and reasons
                        main_idx = published.loc[published['Eval_ID'] == st.session_state.reval_id, 'index'].values[0]
                        st.session_state.audit_logs.at[main_idx, 'Status'] = 'Re-validation Requested'
                        # Save reasons as a new column or dictionary
                        st.session_state.audit_logs.at[main_idx, 'Reval_Reasons'] = str(reval_reasons)
                        save_data(st.session_state.audit_logs, AUDIT_FILE)
                        st.success("Request Sent to QA!")
                        del st.session_state.reval_id
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # --- QA: RE-VALIDATION PAGE ---
    elif choice == "Re-Validation":
        st.header("⚖️ Re-Validation Requests")
        requests = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Re-validation Requested'].copy()
        
        if requests.empty:
            st.info("No pending re-validation requests.")
        else:
            for idx, row in requests.iterrows():
                with st.expander(f"Agent: {row['Agent Name']} | Audit ID: {row['Eval_ID']}"):
                    reasons = eval(row['Reval_Reasons'])
                    for param, reason in reasons.items():
                        st.write(f"**Parameter:** {param}")
                        st.warning(f"**Agent Logic:** {reason}")
                        
                        if st.button(f"Validate & Update {param}", key=f"val_{idx}_{param}"):
                            # Auto Update Logic
                            original_max = st.session_state.param_db[st.session_state.param_db['Parameter'] == param]['Max_Score'].values[0]
                            st.session_state.audit_logs.at[idx, param] = original_max
                            
                            # Recalculate Total Score
                            all_cols = st.session_state.audit_logs.columns
                            param_list = st.session_state.param_db['Parameter'].tolist()
                            new_total = sum([ (0 if "0 (" in str(st.session_state.audit_logs.at[idx, p]) else float(st.session_state.audit_logs.at[idx, p])) 
                                             for p in param_list if p in all_cols])
                            
                            st.session_state.audit_logs.at[idx, 'Total Score'] = new_total
                            st.session_state.audit_logs.at[idx, 'Status'] = 'Published' # Re-publish after fix
                            save_data(st.session_state.audit_logs, AUDIT_FILE)
                            st.success(f"{param} updated to {original_max}!")
                            st.rerun()

    # --- QA AUDIT ENTRY ---
    elif choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        sel_ch = st.selectbox("1. Select Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        active_agents = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_ch) & (st.session_state.agent_db['Status'] == 'Active')]
        
        col_id1, col_id2 = st.columns(2)
        ag_nm = col_id1.selectbox("2. Agent Name", [""] + active_agents['Name'].tolist())
        eid = active_agents[active_agents['Name'] == ag_nm]['ID'].values[0] if ag_nm else "---"
        col_id2.info(f"Agent ID: {eid}")
        
        f1, f2, f3 = st.columns(3)
        int_id, int_dt, int_tm = f1.text_input("Interaction ID"), f2.date_input("Date"), f3.text_input("Time (Manual)")

        st.divider()
        left_col, right_col = st.columns(2)
        all_params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_ch]
        scores = {}

        with left_col:
            st.markdown('<div class="skill-header"><h3>🛡️ Soft Skill</h3></div>', unsafe_allow_html=True)
            soft_params = all_params[all_params['Skill_Type'] == 'Soft Skill']
            for _, row in soft_params.iterrows():
                st.markdown(f'<div class="param-row"><b>{row["Parameter"]}</b> (Max: {row["Max_Score"]})', unsafe_allow_html=True)
                dm_check = st.checkbox("Demark", key=f"dm_{row['Parameter']}")
                scores[row['Parameter']] = f"0 ({st.text_input('Reason', key=f'res_{row['Parameter']}')})" if dm_check else row['Max_Score']
                st.markdown('</div>', unsafe_allow_html=True)

        with right_col:
            st.markdown('<div class="skill-header"><h3>🛠️ Service Skill</h3></div>', unsafe_allow_html=True)
            serv_params = all_params[all_params['Skill_Type'] == 'Service Skill']
            for _, row in serv_params.iterrows():
                st.markdown(f'<div class="param-row"><b>{row["Parameter"]}</b> (Max: {row["Max_Score"]})', unsafe_allow_html=True)
                dm_check = st.checkbox("Demark", key=f"dm_{row['Parameter']}")
                scores[row['Parameter']] = f"0 ({st.text_input('Reason', key=f'res_{row['Parameter']}')})" if dm_check else row['Max_Score']
                st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Submit Audit", type="primary", use_container_width=True):
            entry = {
                'Week': datetime.now().isocalendar()[1], 'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                'Agent Name': ag_nm, 'Employee ID': eid, 'Channel': sel_ch,
                'Eval_ID': int_id, 'Interaction Date': str(int_dt), 'Interaction Time': int_tm, 'Status': 'Pending'
            }
            entry.update(scores)
            def clean_v(v): return 0 if isinstance(v, str) else v
            entry['Total Score'] = sum([clean_v(v) for v in scores.values()])
            st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
            save_data(st.session_state.audit_logs, AUDIT_FILE); st.success("Audit Saved!")

    # --- PUBLISH AUDITS ---
    elif choice == "Publish Audits":
        st.header("📢 Publish Audits")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        st.dataframe(pending)
        if st.button("Publish All"):
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Publish_Time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
            save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()

    # --- OTHER SECTIONS (PARAMETERS & LOGS) ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Settings")
        with st.form("p_f"):
            c1, c2 = st.columns(2)
            pc, ps = c1.selectbox("Channel", ["Inbound", "Live Chat"]), c2.selectbox("Skill", ["Soft Skill", "Service Skill"])
            pn, pm = st.text_input("Param Name"), st.number_input("Max Score", min_value=1)
            if st.form_submit_button("Add"):
                new_p = pd.DataFrame([[pc, ps, pn, pm]], columns=param_cols)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                save_data(st.session_state.param_db, PARAM_FILE); st.rerun()
