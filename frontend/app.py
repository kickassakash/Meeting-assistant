import streamlit as st
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Meeting & Task Assistant", page_icon="📝", layout="wide")

st.title("📝 Smart Meeting & Task Assistant")
st.markdown("---")


def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


if not check_backend():
    st.error(f"⚠️ Backend server is not running at {BACKEND_URL}. Please start the FastAPI backend.")
    st.stop()


menu = st.sidebar.selectbox(
    "Navigation",
    ["📋 Dashboard", "➕ Create Meeting", "✏️ Edit Meeting", "✅ Action Items", "🤖 Ask AI"]
)


if menu == "📋 Dashboard":
    st.header("📋 Meeting Dashboard")
    
    try:
        response = requests.get(f"{BACKEND_URL}/meetings/")
        meetings = response.json()
        
        if not meetings:
            st.info("No meetings found. Create your first meeting!")
        else:
            st.write(f"**Total Meetings:** {len(meetings)}")
            
            for meeting in meetings:
                with st.expander(f"📅 {meeting['title']} - {datetime.fromisoformat(meeting['datetime']).strftime('%Y-%m-%d %H:%M')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Participants:** {meeting['participants']}")
                        st.write(f"**Created:** {datetime.fromisoformat(meeting['created_at']).strftime('%Y-%m-%d %H:%M')}")
                        
                        if meeting['tags']:
                            st.write(f"**Tags:** {meeting['tags']}")
                    
                    with col2:
                        if st.button(f"🤖 Process with AI", key=f"process_{meeting['id']}"):
                            with st.spinner("Processing meeting with AI..."):
                                try:
                                    process_response = requests.post(f"{BACKEND_URL}/meetings/{meeting['id']}/process")
                                    if process_response.status_code == 200:
                                        st.success("✅ Meeting processed successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {process_response.json().get('detail', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        
                        if st.button(f"🗑️ Delete", key=f"delete_{meeting['id']}"):
                            try:
                                delete_response = requests.delete(f"{BACKEND_URL}/meetings/{meeting['id']}")
                                if delete_response.status_code == 200:
                                    st.success("Meeting deleted!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    st.markdown("**Raw Notes:**")
                    st.text_area("Notes", meeting['raw_notes'], height=150, key=f"notes_{meeting['id']}", disabled=True)
                    
                    if meeting['ai_summary']:
                        st.markdown("**AI Summary:**")
                        st.info(meeting['ai_summary'])
                    
                    action_items_response = requests.get(f"{BACKEND_URL}/meetings/{meeting['id']}/action-items/")
                    action_items = action_items_response.json()
                    
                    if action_items:
                        st.markdown("**Action Items:**")
                        for item in action_items:
                            status_emoji = "✅" if item['status'] == "completed" else "🔄" if item['status'] == "in_progress" else "⏳"
                            st.write(f"{status_emoji} {item['description']} - Owner: {item['owner'] or 'N/A'}")
    
    except Exception as e:
        st.error(f"Error loading meetings: {str(e)}")


elif menu == "➕ Create Meeting":
    st.header("➕ Create New Meeting")
    
    with st.form("create_meeting_form"):
        title = st.text_input("Meeting Title", placeholder="e.g., Sprint Planning Meeting")
        meeting_date = st.date_input("Meeting Date", value=datetime.now())
        meeting_time = st.time_input("Meeting Time", value=datetime.now().time())
        participants = st.text_input("Participants", placeholder="e.g., Alice, Bob, Charlie")
        raw_notes = st.text_area("Meeting Notes", height=300, placeholder="Enter meeting notes here...")
        
        process_with_ai = st.checkbox("Process with AI immediately", value=True)
        
        submitted = st.form_submit_button("Create Meeting")
        
        if submitted:
            if not title or not raw_notes:
                st.error("Please fill in all required fields (Title and Notes)")
            else:
                try:
                    meeting_datetime = datetime.combine(meeting_date, meeting_time)
                    
                    meeting_data = {
                        "title": title,
                        "datetime": meeting_datetime.isoformat(),
                        "participants": participants,
                        "raw_notes": raw_notes
                    }
                    
                    response = requests.post(f"{BACKEND_URL}/meetings/", json=meeting_data)
                    
                    if response.status_code == 200:
                        st.success("✅ Meeting created successfully!")
                        meeting = response.json()
                        
                        if process_with_ai:
                            with st.spinner("Processing meeting with AI..."):
                                process_response = requests.post(f"{BACKEND_URL}/meetings/{meeting['id']}/process")
                                if process_response.status_code == 200:
                                    st.success("✅ AI processing completed!")
                                else:
                                    st.warning("Meeting created, but AI processing failed.")
                        
                        st.balloons()
                    else:
                        st.error(f"Error creating meeting: {response.json().get('detail', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif menu == "✏️ Edit Meeting":
    st.header("✏️ Edit Meeting")
    
    try:
        response = requests.get(f"{BACKEND_URL}/meetings/")
        meetings = response.json()
        
        if not meetings:
            st.info("No meetings available to edit.")
        else:
            meeting_options = {f"{m['title']} ({datetime.fromisoformat(m['datetime']).strftime('%Y-%m-%d')})": m['id'] for m in meetings}
            selected_meeting = st.selectbox("Select Meeting", list(meeting_options.keys()))
            
            if selected_meeting:
                meeting_id = meeting_options[selected_meeting]
                meeting_response = requests.get(f"{BACKEND_URL}/meetings/{meeting_id}")
                meeting = meeting_response.json()
                
                with st.form("edit_meeting_form"):
                    title = st.text_input("Meeting Title", value=meeting['title'])
                    raw_notes = st.text_area("Meeting Notes", value=meeting['raw_notes'], height=300)
                    participants = st.text_input("Participants", value=meeting['participants'])
                    
                    submitted = st.form_submit_button("Update Meeting")
                    
                    if submitted:
                        try:
                            update_data = {
                                "title": title,
                                "raw_notes": raw_notes,
                                "participants": participants
                            }
                            
                            update_response = requests.put(f"{BACKEND_URL}/meetings/{meeting_id}", json=update_data)
                            
                            if update_response.status_code == 200:
                                st.success("✅ Meeting updated successfully!")
                                
                                if st.button("Re-process with AI"):
                                    with st.spinner("Processing..."):
                                        requests.post(f"{BACKEND_URL}/meetings/{meeting_id}/process")
                                        st.success("✅ AI processing completed!")
                            else:
                                st.error(f"Error: {update_response.json().get('detail', 'Unknown error')}")
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading meetings: {str(e)}")


elif menu == "✅ Action Items":
    st.header("✅ Action Items")
    
    try:
        response = requests.get(f"{BACKEND_URL}/action-items/")
        action_items = response.json()
        
        if not action_items:
            st.info("No action items found. Create meetings and process them with AI to generate action items.")
        else:
            status_filter = st.selectbox("Filter by Status", ["All", "pending", "in_progress", "completed"])
            
            filtered_items = action_items if status_filter == "All" else [item for item in action_items if item['status'] == status_filter]
            
            st.write(f"**Total Action Items:** {len(filtered_items)}")
            
            for item in filtered_items:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{item['description']}**")
                
                with col2:
                    st.write(f"Owner: {item['owner'] or 'N/A'}")
                
                with col3:
                    current_status = item['status']
                    new_status = st.selectbox(
                        "Status",
                        ["pending", "in_progress", "completed"],
                        index=["pending", "in_progress", "completed"].index(current_status),
                        key=f"status_{item['id']}"
                    )
                    
                    if new_status != current_status:
                        try:
                            update_response = requests.patch(
                                f"{BACKEND_URL}/action-items/{item['id']}",
                                json={"status": new_status}
                            )
                            if update_response.status_code == 200:
                                st.success("Updated!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                with col4:
                    if item['due_date']:
                        due = datetime.fromisoformat(item['due_date'])
                        st.write(f"Due: {due.strftime('%Y-%m-%d')}")
                
                st.markdown("---")
    
    except Exception as e:
        st.error(f"Error loading action items: {str(e)}")


elif menu == "🤖 Ask AI":
    st.header("🤖 Ask AI About Past Meetings")
    
    st.write("Ask questions about your past meetings and get AI-powered answers based on your meeting notes.")
    
    question = st.text_input("Your Question", placeholder="e.g., What did we decide about the new feature?")
    
    if st.button("Ask"):
        if not question:
            st.warning("Please enter a question.")
        else:
            with st.spinner("Searching through meetings and generating answer..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/ask-ai/",
                        json={"question": question}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.markdown("### Answer:")
                        st.success(result['answer'])
                        
                        if result['relevant_meetings']:
                            st.markdown("### Relevant Meetings:")
                            for meeting in result['relevant_meetings']:
                                st.write(f"- {meeting['title']} (ID: {meeting['id']})")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")


st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Process meetings with AI to automatically generate summaries, extract action items, and create tags!")
