import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
from io import BytesIO

def init_db():
    conn = sqlite3.connect('call_center.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS complaints
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  location TEXT,
                  complaint_type TEXT,
                  resolution_time REAL,
                  satisfaction_score INTEGER,
                  agent_name TEXT,
                  call_duration REAL,
                  status TEXT)''')
    conn.commit()
    conn.close()

def load_sample_data():
    return pd.DataFrame({
        'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * 3,
        'location': ['NSW', 'QLD', 'VIC'],
        'complaint_type': ['Billing', 'Service', 'Product'],
        'resolution_time': [15, 25, 10],
        'satisfaction_score': [4, 3, 5],
        'agent_name': ['Agent1', 'Agent2', 'Agent3'],
        'call_duration': [120, 180, 90],
        'status': ['Resolved', 'Pending', 'Resolved']
    })

def insert_data(df):
    conn = sqlite3.connect('call_center.db')
    df.to_sql('complaints', conn, if_exists='append', index=False)
    conn.close()

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Complaints')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def main():
    init_db()
    st.set_page_config(layout="wide")
    st.title("Call Center Performance Dashboard")

    with st.sidebar:
        st.header("Menu")
        menu_option = st.radio("Select Option", 
                             ["Dashboard", "Add New Complaint", "Data Export", "Database Management"])
        
        st.header("Filters")
        date_range = st.date_input("Date Range", [])
        status_filter = st.multiselect("Status", ["Resolved", "Pending", "Escalated"])
        agent_filter = st.multiselect("Agent", ["Agent1", "Agent2", "Agent3"])

    conn = sqlite3.connect('call_center.db')
    df = pd.read_sql('SELECT * FROM complaints', conn)
    conn.close()

    if len(df) == 0:
        sample_data = load_sample_data()
        insert_data(sample_data)
        df = sample_data

    if menu_option == "Dashboard":
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Complaints", len(df))
        col2.metric("Avg Resolution Time", f"{df['resolution_time'].mean():.1f} mins")
        col3.metric("Avg Satisfaction", f"{df['satisfaction_score'].mean():.1f}/5")
        col4.metric("Avg Call Duration", f"{df['call_duration'].mean():.1f} secs")

        tab1, tab2, tab3 = st.tabs(["Complaints Analysis", "Agent Performance", "Trends"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Complaints by Location")
                fig1 = px.pie(df, names='location', title='Distribution by State')
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                st.subheader("Complaint Types")
                fig2 = px.pie(df, names='complaint_type', title='Type Distribution')
                st.plotly_chart(fig2, use_container_width=True)

        with tab2:
            st.subheader("Agent Performance Metrics")
            agent_stats = df.groupby('agent_name').agg({
                'resolution_time': 'mean',
                'satisfaction_score': 'mean',
                'call_duration': 'mean',
                'timestamp': 'count'
            }).rename(columns={'timestamp': 'cases_handled'})
            st.dataframe(agent_stats.style.format({
                'resolution_time': '{:.1f} mins',
                'satisfaction_score': '{:.1f}',
                'call_duration': '{:.1f} secs'
            }))

        with tab3:
            st.subheader("Daily Complaint Trends")
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            daily_counts = df.groupby('date').size().reset_index(name='count')
            fig3 = px.line(daily_counts, x='date', y='count', title='Daily Complaints')
            st.plotly_chart(fig3, use_container_width=True)

    elif menu_option == "Add New Complaint":
        st.subheader("Add New Complaint Record")
        with st.form("complaint_form"):
            col1, col2 = st.columns(2)
            with col1:
                location = st.selectbox("Location", ["NSW", "QLD", "VIC", "WA", "SA", "TAS", "NT", "ACT"])
                complaint_type = st.selectbox("Complaint Type", ["Billing", "Service", "Product", "Technical", "Other"])
                agent_name = st.selectbox("Agent", ["Agent1", "Agent2", "Agent3", "Agent4", "Agent5"])
            with col2:
                resolution_time = st.number_input("Resolution Time (minutes)", min_value=0, max_value=120)
                satisfaction_score = st.slider("Satisfaction Score", 1, 5, 3)
                call_duration = st.number_input("Call Duration (seconds)", min_value=0, max_value=3600)
            
            status = st.selectbox("Status", ["Resolved", "Pending", "Escalated"])
            
            if st.form_submit_button("Submit Complaint"):
                new_data = pd.DataFrame([{
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'location': location,
                    'complaint_type': complaint_type,
                    'resolution_time': resolution_time,
                    'satisfaction_score': satisfaction_score,
                    'agent_name': agent_name,
                    'call_duration': call_duration,
                    'status': status
                }])
                insert_data(new_data)
                st.success("Complaint added successfully!")

    elif menu_option == "Data Export":
        st.subheader("Export Data")
        export_format = st.radio("Export Format", ["Excel", "CSV"])
        
        if st.button("Generate Export"):
            if export_format == "Excel":
                excel_data = to_excel(df)
                st.download_button(
                    label="Download Excel File",
                    data=excel_data,
                    file_name="call_center_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV File",
                    data=csv_data,
                    file_name="call_center_data.csv",
                    mime="text/csv"
                )

    elif menu_option == "Database Management":
        st.subheader("Database Management")
        st.warning("Administrator Access Required")
        password = st.text_input("Enter Admin Password", type="password")
        
        if password == "admin123":
            st.success("Access Granted")
            
            if st.button("Clear All Data"):
                conn = sqlite3.connect('call_center.db')
                c = conn.cursor()
                c.execute("DELETE FROM complaints")
                conn.commit()
                conn.close()
                st.warning("All data has been cleared from the database")
            
            if st.button("Load Sample Data"):
                sample_data = load_sample_data()
                insert_data(sample_data)
                st.success("Sample data loaded successfully")

if __name__ == "__main__":
    main()