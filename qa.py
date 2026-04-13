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
    .skill-header {{ background-color: #1e1e1e; padding: 10px; border-radius: 5px; border: 1px solid white; text-align: center; margin-bottom: 15px; }}
    .training-box {{ background-color: #2b2b2b; padding: 20px; border-radius: 10px; border: 1px solid gold; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATA HANDLER ---
AGENT_FILE, PARAM_FILE, AUDIT_FILE, TRAINING_FILE = "agents.csv", "parameters.csv", "audit_logs.csv", "training_logs.csv"

def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df if not df.empty else pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

# Initializing Session States
if 'agent_db' not in st.session_state: 
    st.session_state.agent_db = load_data(AGENT_FILE, ['Name', 'EMP ID', 'Channel', 'Status'])
if 'param_db' not in st.session_state: 
    st.session_state.param_db = load_data(PARAM_FILE, ['Channel', 'Skill_Type', 'Parameter', 'Max_Score'])
if 'audit_logs' not in st.session_state: 
    st.session_state.audit_logs = load_data(AUDIT_FILE, [])
if 'training_logs' not in st.session_state: 
    st.session_state.training_logs = load_data(TRAINING_FILE, ['Date', 'Time', 'Channel', 'Agent Name', 'EMP ID', 'Topic', 'Feedback'])
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    st.title("Pathao Quality Portal")
    with st.form("login"):
        role = st.selectbox("Role", ["Admin", "QA", "Agent"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "1234":
                st.session_state.update({"logged_in": True, "role": role})
                st.rerun()
            else: st.error("Wrong Password!")
else:
    # Navigation Logic
    nav = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs", "Agent Training"],
        "QA": ["QA Audit Entry", "Publish Audits", "Re-Validation", "Agent Training", "Audit Logs"],
        "Agent": ["Audit View"]
    }
    
    choice = st.sidebar.selectbox("Navigate", nav.get(st.session_state.role, ["Audit View"]))
    
    if st.sidebar.button("Logout"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- 4. AGENT TRAINING (FIXED & UPDATED) ---
    if choice == "Agent Training":
        st.header("🎓 Agent Training Log")
        
        # Check if agents exist
        if st.session_state.agent_db.empty:
            st.error("⚠️ No Agents found! Please add agent details in 'Agent Details' page first.")
        else:
            with st.container():
                st.markdown('<div class="training-box">', unsafe_allow_html=True)
                with st.form("training_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    
                    # Channel filter
                    channels = sorted(st.session_state.agent_db['Channel'].unique().tolist())
                    sel_chan = c1.selectbox("Select Channel", channels)
                    
                    # Agent filter based on channel
                    filtered_agents = st.session_state.agent_db[st.session_state.agent_db['Channel'] == sel_chan]
                    agent_names = filtered_agents['Name'].tolist()
                    
                    sel_agent = c2.selectbox("Select Agent Name", agent_names)
                    
                    # Auto EMP ID lookup
                    if sel_agent:
                        emp_id = filtered_agents[filtered_agents['Name'] == sel_agent]['EMP ID'].values[0]
                    else:
                        emp_id = "N/A"
                    
                    st.write(f"🔢 **EMP ID:** `{emp_id}`")
                    
                    c3, c4 = st.columns(2)
                    t_date = c3.date_input("Training Date", value=datetime.now().date())
                    t_time = c4.text_input("Time (e.g., 12:00 PM)")
                    
                    topic = st.text_input("Training Topic")
                    feedback = st.text_area("Agent Feedback")
                    
                    if st.form_submit_button("Save Training log", type="primary"):
                        if topic and feedback:
                            new_entry = {
                                'Date': str(t_date),
                                'Time': t_time,
                                'Channel': sel_chan,
                                'Agent Name': sel_agent,
                                'EMP ID': emp_id,
                                'Topic': topic,
                                'Feedback': feedback
                            }
                            st.session_state.training_logs = pd.concat([st.session_state.training_logs, pd.DataFrame([new_entry])], ignore_index=True)
                            save_data(st.session_state.training_logs, TRAINING_FILE)
                            st.success("✅ Training logged successfully!")
                        else:
                            st.warning("Please fill topic and feedback fields.")
                st.markdown('</div>', unsafe_allow_html=True)

            st.divider()
            st.subheader("📜 Previous Training Logs")
            st.dataframe(st.session_state.training_logs, use_container_width=True)

    # --- 5. AGENT DETAILS (Admin can add agents here) ---
    elif choice == "Agent Details":
        st.header("👥 Agent Management")
        with st.form("add_agent"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Agent Name")
            eid = c2.text_input("EMP ID")
            chan = c3.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            if st.form_submit_button("Add Agent"):
                if name and eid:
                    new_agent = {'Name': name, 'EMP ID': eid, 'Channel': chan, 'Status': 'Active'}
                    st.session_state.agent_db = pd.concat([st.session_state.agent_db, pd.DataFrame([new_agent])], ignore_index=True)
                    save_data(st.session_state.agent_db, AGENT_FILE)
                    st.success("Agent Added!")
                    st.rerun()
        st.dataframe(st.session_state.agent_db, use_container_width=True)

    # (অন্যান্য পেইজগুলো যেমন QA Audit Entry, Audit View ইত্যাদি আগের মতোই কাজ করবে)
    elif choice == "QA Audit Entry":
        st.subheader("Audit Entry code goes here...")
    
    elif choice == "Audit Logs":
        st.dataframe(st.session_state.audit_logs)
