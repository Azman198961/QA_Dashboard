import streamlit as st
import pandas as pd
from datetime import datetime

# --- পেজ কনফিগারেশন ---
st.set_page_config(page_title="Support Quality Tool", layout="wide")

# --- সেশন স্টেট হ্যান্ডলিং (ডেটা স্টোর করার জন্য) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if 'agent_db' not in st.session_state:
    # ডিফল্ট কলাম সেটআপ
    st.session_state.agent_db = pd.DataFrame(columns=[
        'ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status'
    ])

if 'param_db' not in st.session_state:
    st.session_state.param_db = pd.DataFrame(columns=[
        'Channel', 'Skill_Type', 'Parameter', 'Max_Score'
    ])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame(columns=[
        'Eval_ID', 'Date_Time', 'Agent_ID', 'Agent_Name', 'Channel', 'Final_Score'
    ])

# --- লগইন ফাংশন ---
def login():
    st.title("🛡️ Customer Support Quality & KPI Tool")
    col1, col2 = st.columns(2)
    with col1:
        user = st.selectbox("Login as:", ["Select Role", "Admin", "Agent"])
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if password == "1234":  # আপনি চাইলে পাসওয়ার্ড পরিবর্তন করতে পারেন
                st.session_state.logged_in = True
                st.session_state.role = user
                st.rerun()
            else:
                st.error("Invalid Password!")

# --- মেইন অ্যাপ্লিকেশন ---
if not st.session_state.logged_in:
    login()
else:
    st.sidebar.title(f"Logged in as: {st.session_state.role}")
    
    # মেনু সিলেকশন
    if st.session_state.role == "Admin":
        menu = ["Agent Details", "Audit Parameters", "QA Audit Entry", "Audit Logs"]
    else:
        menu = ["QA Audit Entry"] # এজেন্ট শুধু অডিট এন্ট্রি/ভিউ দেখতে পারবে (আপনার রিকোয়ারমেন্ট অনুযায়ী)

    choice = st.sidebar.selectbox("Navigation", menu)
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # --- ১. এজেন্ট ডিটেইলস পেইজ ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        
        with st.expander("Add New / Update Agent"):
            with st.form("agent_form"):
                col1, col2 = st.columns(2)
                a_id = col1.text_input("Employee ID")
                a_name = col2.text_input("Agent Name")
                a_gen = col1.selectbox("Gender", ["Male", "Female", "Other"])
                a_con = col2.text_input("Contact Number")
                a_emg = col1.text_input("Emergency Contact")
                a_chan = col2.selectbox("Assigned Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                a_stat = col1.selectbox("Status", ["Active", "Resigned"])
                
                if st.form_submit_button("Save Agent Details"):
                    new_agent = pd.DataFrame([[a_id, a_name, a_gen, a_con, a_emg, a_chan, a_stat]], 
                                            columns=st.session_state.agent_db.columns)
                    # ডুপ্লিকেট আইডি থাকলে আপডেট হবে, না থাকলে নতুন অ্যাড হবে
                    st.session_state.agent_db = pd.concat([st.session_state.agent_db, new_agent]).drop_duplicates(subset=['ID'], keep='last')
                    st.success(f"Agent {a_name} saved successfully!")

        st.subheader("Existing Agents")
        st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- ২. অডিট প্যারামিটারস পেইজ ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Audit Parameters & Scoring")
        
        with st.form("param_form"):
            p_chan = st.selectbox("Select Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_skill = st.radio("Skill Category", ["Soft Skill", "Service Skill"])
            p_name = st.text_input("Parameter Name")
            p_score = st.number_input("Assigned Score", min_value=1, max_value=100, value=10)
            
            if st.form_submit_button("Add Parameter"):
                new_p = pd.DataFrame([[p_chan, p_skill, p_name, p_score]], columns=st.session_state.param_db.columns)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                st.success("Parameter added!")

        st.subheader("Current Parameters")
        st.dataframe(st.session_state.param_db, use_container_width=True)

    # --- ৩. QA অডিট এন্ট্রি (Main Logic) ---
    elif choice == "QA Audit Entry":
        st.header("📝 Quality Audit Form")
        
        # চ্যানেল ও এজেন্ট ফিল্টারিং
        c1, c2 = st.columns(2)
        with c1:
            sel_chan = st.selectbox("Channel Name", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        with c2:
            # লজিক: শুধু ওই চ্যানেলের অ্যাক্টিভ এজেন্টদের দেখাবে
            agent_list = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_chan) & 
                                                  (st.session_state.agent_db['Status'] == 'Active')]
            sel_agent_name = st.selectbox("Agent Name", agent_list['Name'].tolist() if not agent_list.empty else ["No Agent Found"])

        # অটো-ফেচ এমপ্লয়ি আইডি
        current_agent_row = agent_list[agent_list['Name'] == sel_agent_name]
        emp_id = current_agent_row['ID'].values[0] if not current_agent_row.empty else "N/A"
        
        st.divider()
        
        # কনস্ট্যান্ট ফিল্ডস
        f1, f2, f3 = st.columns(3)
        f1.text_input("Employee ID", value=emp_id, disabled=True)
        eval_id = f2.text_input("Evaluation ID (Call/Chat/Order ID)")
        eval_dt = f3.date_input("Evaluation Date")
        eval_tm = f3.time_input("Evaluation Time")

        # --- ডুপ্লিকেট চেক লজিক ---
        is_duplicate = False
        if eval_id:
            existing = st.session_state.audit_logs
            if sel_chan in ["Live Chat", "Report Issue"]:
                if eval_id in existing['Eval_ID'].values:
                    is_duplicate = True
            elif sel_chan == "Inbound":
                check = existing[(existing['Eval_ID'] == eval_id) & (existing['Date_Time'] == str(eval_dt))]
                if not check.empty: is_duplicate = True
            elif sel_chan == "Complaint Management":
                check = existing[(existing['Eval_ID'] == eval_id) & (existing['Agent_ID'] == emp_id)]
                if not check.empty: is_duplicate = True

        if is_duplicate:
            st.error(f"🛑 Error: This Evaluation ID ({eval_id}) has already been audited for this criteria!")
        else:
            # --- অডিট প্যারামিটার ফর্ম ---
            st.subheader("Scoring Section")
            params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
            
            if params.empty:
                st.warning("No parameters set for this channel. Please add parameters first.")
            else:
                audit_scores = {}
                
                for skill in ["Soft Skill", "Service Skill"]:
                    st.markdown(f"#### {skill}")
                    skill_params = params[params['Skill_Type'] == skill]
                    
                    for idx, row in skill_params.iterrows():
                        col_text, col_btn = st.columns([4, 1])
                        col_text.write(f"{row['Parameter']} (Max: {row['Max_Score']})")
                        
                        # ইউনিক কি (Key) তৈরি করা এরর এড়াতে
                        u_key = f"btn_{sel_chan}_{idx}_{row['Parameter']}"
                        
                        if f"demark_{u_key}" not in st.session_state:
                            st.session_state[f"demark_{u_key}"] = False

                        if col_btn.button("Demark", key=u_key):
                            st.session_state[f"demark_{u_key}"] = not st.session_state[f"demark_{u_key}"]
                        
                        if st.session_state[f"demark_{u_key}"]:
                            audit_scores[row['Parameter']] = 0
                            col_btn.caption("Score: 0")
                        else:
                            audit_scores[row['Parameter']] = row['Max_Score']
                            col_btn.caption(f"Score: {row['Max_Score']}")

                if st.button("Submit Audit", type="primary"):
                    total_score = sum(audit_scores.values())
                    new_log = pd.DataFrame([[eval_id, str(eval_dt), emp_id, sel_agent_name, sel_chan, total_score]], 
                                          columns=st.session_state.audit_logs.columns)
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, new_log], ignore_index=True)
                    st.success(f"Audit Submitted! Total Score: {total_score}")
                    st.balloons()

    # --- ৪. অডিট লগ (অ্যাডমিনদের জন্য ভিউ) ---
    elif choice == "Audit Logs":
        st.header("📊 Audit History & Reports")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)
        
        if not st.session_state.audit_logs.empty:
            st.download_button(
                label="Export Data to CSV",
                data=st.session_state.audit_logs.to_csv(index=False),
                file_name=f"audit_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )