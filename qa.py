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
    # আপনার রিকোয়ারমেন্ট অনুযায়ী সব কলাম
    st.session_state.agent_db = pd.DataFrame(columns=[
        'ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status'
    ])

if 'param_db' not in st.session_state:
    st.session_state.param_db = pd.DataFrame(columns=['Channel', 'Skill_Type', 'Parameter', 'Max_Score'])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame()

# --- লগইন ফাংশন ---
def login():
    st.title("🛡️ Customer Support Quality & KPI Tool")
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

    # --- ১. এজেন্ট ডিটেইলস (সবগুলো ফিল্ডসহ) ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        with st.expander("Add New / Update Agent"):
            with st.form("agent_form"):
                col1, col2 = st.columns(2)
                a_id = col1.text_input("Employee ID")
                a_name = col2.text_input("Agent Name")
                a_gen = col1.selectbox("Gender", ["Male", "Female", "Other"])
                a_con = col2.text_input("Contact Number")
                a_emg = col1.text_input("Emergency Contact Number")
                a_chan = col2.selectbox("Assigned Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                a_stat = col1.selectbox("Status", ["Active", "Resigned"])
                
                if st.form_submit_button("Save Agent Details"):
                    new_agent = pd.DataFrame([[a_id, a_name, a_gen, a_con, a_emg, a_chan, a_stat]], 
                                            columns=st.session_state.agent_db.columns)
                    st.session_state.agent_db = pd.concat([st.session_state.agent_db, new_agent]).drop_duplicates(subset=['ID'], keep='last')
                    st.success(f"Agent {a_name} saved successfully!")
        st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- ২. অডিট প্যারামিটারস ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Audit Parameters")
        with st.form("p_form"):
            p_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_skill = st.radio("Skill Category", ["Soft Skill", "Service Skill"])
            p_name = st.text_input("Parameter Name")
            p_score = st.number_input("Max Score", min_value=1, value=10)
            if st.form_submit_button("Add Parameter"):
                new_p = pd.DataFrame([[p_chan, p_skill, p_name, p_score]], columns=st.session_state.param_db.columns)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                st.success("Added!")
        st.dataframe(st.session_state.param_db, use_container_width=True)

    # --- ৩. QA অডিট এন্ট্রি (Updated with Interaction Date/Time & Evaluation Date) ---
    elif choice == "QA Audit Entry":
        st.header("📝 Quality Audit Form")
        c1, c2 = st.columns(2)
        sel_chan = c1.selectbox("Channel Name", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        agent_list = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_chan) & (st.session_state.agent_db['Status'] == 'Active')]
        sel_agent = c2.selectbox("Agent Name", agent_list['Name'].tolist() if not agent_list.empty else ["No Agent Found"])
        
        emp_id = agent_list[agent_list['Name'] == sel_agent]['ID'].values[0] if not agent_list.empty else "N/A"
        
        st.divider()
        f1, f2, f3, f4 = st.columns(4)
        f1.text_input("Employee ID", value=emp_id, disabled=True)
        eval_id = f2.text_input("Evaluation ID (Call/Chat/Order ID)")
        inter_date = f3.date_input("Interaction Date")
        # টাইম ইনপুট ফরম্যাট hh:mm:ss করার জন্য টেক্সট ইনপুট
        inter_time = f4.text_input("Interaction Time (HH:MM:SS)", value=datetime.now().strftime("%H:%M:%S"))

        params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
        
        if params.empty:
            st.warning("No parameters found for this channel.")
        else:
            audit_scores = {}
            st.subheader("Scoring Section")
            for idx, row in params.iterrows():
                u_key = f"dm_{idx}_{row['Parameter']}"
                if u_key not in st.session_state: st.session_state[u_key] = False
                
                col_t, col_b = st.columns([4, 1])
                col_t.write(f"**[{row['Skill_Type']}]** {row['Parameter']} (Max: {row['Max_Score']})")
                if col_b.button("Demark", key=f"btn_{u_key}"):
                    st.session_state[u_key] = not st.session_state[u_key]
                
                audit_scores[row['Parameter']] = 0 if st.session_state[u_key] else row['Max_Score']
                col_b.caption(f"Score: {audit_scores[row['Parameter']]}")

            if st.button("Submit Audit", type="primary"):
                # ক্যালকুলেশন
                soft_obtained = sum(audit_scores[p] for p in params[params['Skill_Type'] == 'Soft Skill']['Parameter'])
                soft_max = params[params['Skill_Type'] == 'Soft Skill']['Max_Score'].sum()
                service_obtained = sum(audit_scores[p] for p in params[params['Skill_Type'] == 'Service Skill']['Parameter'])
                service_max = params[params['Skill_Type'] == 'Service Skill']['Max_Score'].sum()
                
                soft_perc = (soft_obtained / soft_max * 100) if soft_max > 0 else 0
                serv_perc = (service_obtained / service_max * 100) if service_max > 0 else 0
                
                # লগের জন্য ডাটা
                entry = {
                    'Evaluation Date': datetime.now().strftime("%Y-%m-%d"), # অটো সাবমিশন ডেট
                    'Interaction Date': str(inter_date),
                    'Interaction Time': inter_time,
                    'Agent Name': sel_agent,
                    'Employee ID': emp_id,
                    'Eval_ID': eval_id,
                    'Channel': sel_chan,
                    'Soft Skill %': f"{soft_perc:.2f}%",
                    'Service Skill %': f"{serv_perc:.2f}%",
                    'Total Score': sum(audit_scores.values())
                }
                entry.update(audit_scores)
                
                st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                st.success("Audit Submitted Successfully!")
                st.balloons()

    # --- ৪. অডিট লগ ---
    elif choice == "Audit Logs":
        st.header("📊 Detailed Audit History")
        if not st.session_state.audit_logs.empty:
            st.dataframe(st.session_state.audit_logs, use_container_width=True)
            st.download_button("Export to CSV", st.session_state.audit_logs.to_csv(index=False), "detailed_audit.csv")
        else:
            st.info("No audit records found.")
