import streamlit as st
import pandas as pd
from datetime import datetime

# --- পেজ কনফিগারেশন ---
st.set_page_config(page_title="Support Quality Tool", layout="wide")

# --- সেশন স্টেট হ্যান্ডলিং ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if 'agent_db' not in st.session_state:
    st.session_state.agent_db = pd.DataFrame(columns=['ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status'])

if 'param_db' not in st.session_state:
    st.session_state.param_db = pd.DataFrame(columns=['Channel', 'Skill_Type', 'Parameter', 'Max_Score'])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame()

# --- লগইন ফাংশন ---
def login():
    st.title("🛡️ Customer Support Quality Tool")
    col1, _ = st.columns([1, 1])
    with col1:
        user = st.selectbox("Login as:", ["Select Role", "Admin", "Agent"])
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if password == "1234":
                st.session_state.logged_in = True
                st.session_state.role = user
                st.rerun()
            else:
                st.error("Invalid Password!")

if not st.session_state.logged_in:
    login()
else:
    st.sidebar.title(f"Logged in as: {st.session_state.role}")
    menu = ["Agent Details", "Audit Parameters", "QA Audit Entry", "Audit Logs"] if st.session_state.role == "Admin" else ["QA Audit Entry"]
    choice = st.sidebar.selectbox("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # --- ১. এজেন্ট ডিটেইলস ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        with st.expander("Add New Agent"):
            with st.form("agent_form"):
                col1, col2 = st.columns(2)
                a_id = col1.text_input("Employee ID")
                a_name = col2.text_input("Agent Name")
                a_gen = col1.selectbox("Gender", ["Male", "Female", "Other"])
                a_con = col2.text_input("Contact Number")
                a_emg = col1.text_input("Emergency Contact Number")
                a_chan = col2.selectbox("Assigned Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                a_stat = col1.selectbox("Status", ["Active", "Resigned"])
                if st.form_submit_button("Save"):
                    if a_id and a_name:
                        new_agent = pd.DataFrame([[a_id, a_name, a_gen, a_con, a_emg, a_chan, a_stat]], columns=st.session_state.agent_db.columns)
                        st.session_state.agent_db = pd.concat([st.session_state.agent_db, new_agent]).drop_duplicates(subset=['ID'], keep='last')
                        st.success("Saved!")
                    else: st.error("ID and Name required!")
        st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- ২. অডিট প্যারামিটারস ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Parameters")
        with st.form("p_form"):
            p_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_skill = st.radio("Skill Category", ["Soft Skill", "Service Skill"])
            p_name = st.text_input("Parameter Name")
            p_score = st.number_input("Max Score", min_value=1, value=10)
            if st.form_submit_button("Add"):
                if p_name:
                    new_p = pd.DataFrame([[p_chan, p_skill, p_name, p_score]], columns=st.session_state.param_db.columns)
                    st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                    st.success("Added!")
        st.dataframe(st.session_state.param_db, use_container_width=True)

    # --- ৩. QA অডিট এন্ট্রি (Updated with Date & Warning) ---
    elif choice == "QA Audit Entry":
        st.header("📝 Quality Audit Form")
        
        # --- নতুন আপডেট: ডেট এবং সিস্টেম ওয়ার্নিং ---
        today = datetime.now()
        current_date = today.strftime("%d %B, %Y")
        current_day = today.strftime("%A")
        
        # টপ ইনফো বার
        col_date, col_day = st.columns(2)
        col_date.info(f"📅 **Date:** {current_date}")
        col_day.info(f"⏳ **Day:** {current_day}")

        # শনিবারের ওয়ার্নিং মেসেজ
        if current_day == "Saturday":
            st.warning("⚠️ Today is the last day for this week's Audit! Please ensure all pending audits are completed.")
        
        st.divider()

        # ১. ইনফরমেশন সেকশন
        with st.container():
            c1, c2, c3 = st.columns(3)
            evaluator = c1.text_input("Evaluator Name")
            sel_chan = c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            
            agent_list = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_chan) & (st.session_state.agent_db['Status'] == 'Active')]
            agent_names = agent_list['Name'].tolist()
            sel_agent = c3.selectbox("Agent Name", ["Select Agent"] + agent_names)
            
            emp_id = agent_list[agent_list['Name'] == sel_agent]['ID'].values[0] if sel_agent != "Select Agent" else ""

            f1, f2, f3, f4 = st.columns(4)
            f1.text_input("Employee ID", value=emp_id, disabled=True)
            eval_id = f2.text_input("Evaluation ID (Call/Chat ID)")
            inter_date = f3.date_input("Interaction Date")
            inter_time = f4.text_input("Interaction Time (HH:MM:SS)", value=datetime.now().strftime("%H:%M:%S"))
            
            feedback = st.text_area("QA Feedback")

        st.divider()
        
        # ২. স্কোরিং সেকশন
        params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
        if params.empty:
            st.warning("No parameters found.")
        else:
            audit_scores = {}
            for idx, row in params.iterrows():
                u_key = f"dm_{idx}_{row['Parameter']}"
                if u_key not in st.session_state: st.session_state[u_key] = False
                
                col_t, col_b = st.columns([4, 1])
                col_t.write(f"**{row['Skill_Type']}**: {row['Parameter']} (Max: {row['Max_Score']})")
                if col_b.button("Demark", key=f"btn_{u_key}"):
                    st.session_state[u_key] = not st.session_state[u_key]
                
                audit_scores[row['Parameter']] = 0 if st.session_state[u_key] else row['Max_Score']
                col_b.caption(f"Score: {audit_scores[row['Parameter']]}")

            if st.button("Submit Audit", type="primary"):
                if not evaluator or sel_agent == "Select Agent" or not eval_id or not feedback:
                    st.error("Please fill all required fields before submitting!")
                else:
                    soft_obtained = sum(audit_scores[p] for p in params[params['Skill_Type'] == 'Soft Skill']['Parameter'])
                    soft_max = params[params['Skill_Type'] == 'Soft Skill']['Max_Score'].sum()
                    service_obtained = sum(audit_scores[p] for p in params[params['Skill_Type'] == 'Service Skill']['Parameter'])
                    service_max = params[params['Skill_Type'] == 'Service Skill']['Max_Score'].sum()
                    
                    entry = {
                        'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                        'Evaluator Name': evaluator,
                        'Agent Name': sel_agent,
                        'Employee ID': emp_id,
                        'Channel': sel_chan,
                        'Interaction Date': str(inter_date),
                        'Interaction Time': inter_time,
                        'Eval_ID': eval_id,
                        'QA Feedback': feedback
                    }
                    entry.update(audit_scores)
                    
                    entry['Total Score'] = sum(audit_scores.values())
                    entry['Soft Skill %'] = f"{(soft_obtained / soft_max * 100):.2f}%" if soft_max > 0 else "0.00%"
                    entry['Service Skill %'] = f"{(service_obtained / service_max * 100):.2f}%" if service_max > 0 else "0.00%"

                    new_row = pd.DataFrame([entry])
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, new_row], ignore_index=True)
                    st.success("Audit Logged Successfully!")
                    st.balloons()

    # --- ৪. অডিট লগ ---
    elif choice == "Audit Logs":
        st.header("📊 Audit History")
        if not st.session_state.audit_logs.empty:
            base_cols = ['Evaluation Date', 'Evaluator Name', 'Agent Name', 'Employee ID', 'Channel', 'Interaction Date', 'Interaction Time', 'Eval_ID', 'QA Feedback']
            other_cols = [c for c in st.session_state.audit_logs.columns if c not in base_cols + ['Total Score', 'Soft Skill %', 'Service Skill %']]
            final_cols = base_cols + other_cols + ['Total Score', 'Soft Skill %', 'Service Skill %']
            
            st.dataframe(st.session_state.audit_logs[final_cols], use_container_width=True)
            st.download_button("Export CSV", st.session_state.audit_logs[final_cols].to_csv(index=False), "audit_report.csv")
        else:
            st.info("No logs available.")
