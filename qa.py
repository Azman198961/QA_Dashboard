import streamlit as st
import pandas as pd
import os
from datetime import datetime

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
    .training-box {{ background-color: #2b2b2b; padding: 20px; border-radius: 10px; border: 1px solid gold; }}
    .skill-header {{ background-color: #1e1e1e; padding: 10px; border-radius: 5px; border: 1px solid white; text-align: center; margin-bottom: 15px; }}
    .param-row {{ background-color: #2b2b2b; padding: 8px; border-radius: 5px; margin-bottom: 8px; border-left: 4px solid white; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATA HANDLER ---
# ফাইল পাথ এবং কলাম ডেফিনিশন
AGENT_FILE, PARAM_FILE, AUDIT_FILE, TRAINING_FILE = "agents.csv", "parameters.csv", "audit_logs.csv", "training_logs.csv"
param_cols = ['Channel', 'Skill_Type', 'Parameter', 'Max_Score']
training_cols = ['Date', 'Time', 'Channel', 'Agent Name', 'ID', 'Topic', 'Feedback']

def load_data(file, default_cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        if not df.empty:
            df.columns = df.columns.str.strip() # কলামের স্পেস ক্লিন করা
            return df
    return pd.DataFrame(columns=default_cols)

def save_data(df, file):
    df.to_csv(file, index=False)

# Session State লোড করা (ID কলাম ব্যবহার করা হয়েছে)
if 'agent_db' not in st.session_state: 
    st.session_state.agent_db = load_data(AGENT_FILE, ['Name', 'ID', 'Channel', 'Status'])
if 'param_db' not in st.session_state: 
    st.session_state.param_db = load_data(PARAM_FILE, param_cols)
if 'audit_logs' not in st.session_state: 
    st.session_state.audit_logs = load_data(AUDIT_FILE, [])
if 'training_logs' not in st.session_state: 
    st.session_state.training_logs = load_data(TRAINING_FILE, training_cols)
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

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
    choice = st.sidebar.selectbox("Navigate", nav.get(st.session_state.role, ["Audit View"]))
    
    if st.sidebar.button("Logout"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- 4. AGENT TRAINING (Updated with ID) ---
    if choice == "Agent Training":
        st.header("🎓 Agent Training Log")
        
        if st.session_state.agent_db.empty:
            st.error("⚠️ No Agents found! Please add agent details in 'Agent Details' page first.")
        else:
            with st.container():
                st.markdown('<div class="training-box">', unsafe_allow_html=True)
                
                # রিয়েলটাইম ফিল্টারিং এর জন্য ফর্মের বাইরে ড্রপডাউন
                c1, c2 = st.columns(2)
                channels = sorted(st.session_state.agent_db['Channel'].unique().tolist())
                sel_chan = c1.selectbox("Select Channel", channels)
                
                filtered_agents = st.session_state.agent_db[st.session_state.agent_db['Channel'] == sel_chan]
                agent_names = filtered_agents['Name'].tolist()
                sel_agent = c2.selectbox("Select Agent Name", agent_names)
                
                # ID Lookup
                agent_id = "N/A"
                if sel_agent:
                    try:
                        agent_id = filtered_agents[filtered_agents['Name'] == sel_agent]['ID'].values[0]
                    except KeyError:
                        st.error("Column 'ID' not found in your CSV. Ensure it's named 'ID'.")

                st.info(f"📍 Agent: **{sel_agent}** | ID: **{agent_id}**")

                with st.form("training_submit_form", clear_on_submit=True):
                    c3, c4 = st.columns(2)
                    t_date = c3.date_input("Training Date", value=datetime.now().date())
                    t_time = c4.text_input("Time (e.g., 10:30 AM)")
                    
                    topic = st.text_input("Training Topic")
                    feedback = st.text_area("Agent Feedback")
                    
                    # সাবমিট বাটন
                    if st.form_submit_button("Save Training Log", type="primary"):
                        if topic and feedback:
                            new_entry = {
                                'Date': str(t_date),
                                'Time': t_time,
                                'Channel': sel_chan,
                                'Agent Name': sel_agent,
                                'ID': agent_id,
                                'Topic': topic,
                                'Feedback': feedback
                            }
                            st.session_state.training_logs = pd.concat([st.session_state.training_logs, pd.DataFrame([new_entry])], ignore_index=True)
                            save_data(st.session_state.training_logs, TRAINING_FILE)
                            st.success(f"✅ Training log saved for {sel_agent}!")
                        else:
                            st.warning("Please fill all fields.")
                st.markdown('</div>', unsafe_allow_html=True)

            st.divider()
            st.subheader("📜 Previous Logs")
            st.dataframe(st.session_state.training_logs.tail(10), use_container_width=True)

    # --- 5. AGENT DETAILS ---
    elif choice == "Agent Details":
        st.header("👥 Agent Management")
        with st.form("add_agent"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Agent Name")
            eid = c2.text_input("ID")
            chan = c3.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            if st.form_submit_button("Add Agent"):
                if name and eid:
                    new_agent = {'Name': name, 'ID': eid, 'Channel': chan, 'Status': 'Active'}
                    st.session_state.agent_db = pd.concat([st.session_state.agent_db, pd.DataFrame([new_agent])], ignore_index=True)
                    save_data(st.session_state.agent_db, AGENT_FILE)
                    st.success("Agent Added!")
                    st.rerun()
        st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- 6. QA AUDIT ENTRY ---
    elif choice == "QA Audit Entry":
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

    # বাকি পেজগুলো (Audit Logs, Publish Audits, Parameters) একইভাবে থাকবে...
    elif choice == "Audit Logs":
        st.header("📜 Audit Logs")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)

    elif choice == "Audit Parameters":
        st.header("⚙️ Audit Parameters")
        with st.form("p_f"):
            c1, c2 = st.columns(2)
            pc = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            ps = c2.selectbox("Skill Type", ["Soft Skill", "Service Skill"])
            pn = st.text_input("Parameter Name")
            pm = st.number_input("Max Score", min_value=1)
            if st.form_submit_button("Add Parameter"):
                new_p = pd.DataFrame([[pc, ps, pn, pm]], columns=param_cols)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                save_data(st.session_state.param_db, PARAM_FILE)
                st.success("Parameter Added!")
