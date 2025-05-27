import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from services.rag_pipeline import RAGPipeline, GeminiResultParser
from services.scheduler import SchedulerService
from services.data_sources import GmailSource, SlackSource
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize services
try:
    rag_pipeline = RAGPipeline()
    scheduler = SchedulerService()
    result_parser = GeminiResultParser()
except Exception as e:
    st.error(f"Error initializing services: {str(e)}")
    st.stop()

def main():
    st.title("AI Agent Dashboard")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # API Keys Configuration
    st.sidebar.subheader("API Keys")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Data Sources Section
    st.header("Data Sources")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Gmail")
        if st.button("Fetch Recent Emails"):
            try:
                gmail_source = GmailSource()
                emails = gmail_source.fetch_emails(days_back=7)
                st.write(f"Fetched {len(emails)} emails")
                
                # Display emails in an expandable section
                with st.expander("View Emails"):
                    for email in emails:
                        st.write(f"**Subject:** {email['subject']}")
                        st.write(f"**Date:** {email['date']}")
                        st.write(f"**Preview:** {email['body']}")
                        st.write("---")
                        
                # Process emails through RAG pipeline
                if emails:
                    documents = [email['body'] for email in emails]
                    metadata = [{'source': 'gmail', 'subject': email['subject'], 'date': email['date']} 
                              for email in emails]
                    rag_pipeline.process_and_store(documents, metadata)
                    st.success("Emails processed and stored in vector database")
            except Exception as e:
                st.error(f"Error fetching emails: {str(e)}")
    
    with col2:
        st.subheader("Slack")
        slack_token = st.text_input("Slack Token", type="password", value=os.getenv("SLACK_TOKEN", ""))
        channel_id = st.text_input("Channel ID", value=os.getenv("SLACK_CHANNEL_ID", ""))
        
        if st.button("Fetch Recent Messages"):
            if not slack_token or not channel_id:
                st.error("Please provide both Slack token and Channel ID")
            else:
                try:
                    slack_source = SlackSource(slack_token)
                    messages = slack_source.fetch_messages(channel_id, days_back=7)
                    st.write(f"Fetched {len(messages)} messages")
                    
                    # Display messages in an expandable section
                    with st.expander("View Messages"):
                        for message in messages:
                            st.write(f"**User:** {message['user']}")
                            st.write(f"**Date:** {message['date']}")
                            st.write(f"**Message:** {message['text']}")
                            st.write("---")
                            
                    # Process messages through RAG pipeline
                    if messages:
                        documents = [msg['text'] for msg in messages]
                        metadata = [{'source': 'slack', 'user': msg['user'], 'date': msg['date']} 
                                  for msg in messages]
                        rag_pipeline.process_and_store(documents, metadata)
                        st.success("Messages processed and stored in vector database")
                except Exception as e:
                    st.error(f"Error fetching messages: {str(e)}")
    
    # RAG Pipeline Section
    st.header("RAG Pipeline")
    
    # Query input
    query = st.text_input("Enter your query:")
    if query:
        try:
            results = rag_pipeline.similarity_search(query)
            st.write("Search Results:")
            for i, result in enumerate(results, 1):
                with st.expander(f"Result {i} (Score: {result['score']:.2f})"):
                    st.write(result['content'])
                    st.write("Metadata:", result['metadata'])
        except Exception as e:
            st.error(f"Error performing search: {str(e)}")
    
    # Flags Section
    st.header("Flags")
    if st.button("Check for Flags"):
        try:
            # Example flag check
            sample_result = "This is an urgent matter that requires immediate attention."
            parsed_result = result_parser.parse(sample_result)
            
            if parsed_result['has_flags']:
                st.warning("⚠️ Flags detected!")
                st.write("Flags found:", ", ".join(parsed_result['flags']))
            else:
                st.success("✅ No flags detected")
        except Exception as e:
            st.error(f"Error checking flags: {str(e)}")
    
    # Scheduler Status
    st.header("Scheduler Status")
    try:
        jobs = scheduler.get_all_jobs()
        if jobs:
            jobs_df = pd.DataFrame.from_dict(jobs, orient='index')
            st.dataframe(jobs_df)
        else:
            st.info("No scheduled jobs")
    except Exception as e:
        st.error(f"Error getting scheduler status: {str(e)}")

if __name__ == "__main__":
    main() 