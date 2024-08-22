import streamlit as st
from openai import OpenAI
import sqlite3
import os

DB_FILE = 'db.sqlite'

def create_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def load_api_keys():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT key FROM api_keys')
    keys = [row[0] for row in cursor.fetchall()]
    conn.close()
    return keys

def save_api_key(key):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO api_keys (key) VALUES (?)', (key,))
    conn.commit()
    conn.close()

def load_chat_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT role, content FROM chat_history')
    messages = [{'role': row[0], 'content': row[1]} for row in cursor.fetchall()]
    conn.close()
    return messages

def save_chat_history(messages):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history')
    cursor.executemany('INSERT INTO chat_history (role, content) VALUES (?, ?)', 
                       [(m['role'], m['content']) for m in messages])
    conn.commit()
    conn.close()

def main():
    client = OpenAI(api_key=st.session_state.openai_api_key)
    models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
    st.session_state["openai_model"] = st.sidebar.selectbox("Select OpenAI model", models, index=0)
    st.session_state.messages = load_chat_history()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat_history(st.session_state.messages)
    if st.sidebar.button('Clear Chat'):
        st.session_state.messages = []
        save_chat_history(st.session_state.messages)
        st.rerun()

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        create_db()
    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        main()
    else:
        api_keys = load_api_keys()
        selected_key = st.selectbox("Existing OpenAI API Keys", api_keys)
        new_key = st.text_input("New OpenAI API Key", type="password")
        login = st.button("Login")
        if login:
            if new_key:
                save_api_key(new_key)
                st.success("Key saved successfully.")
                st.session_state['openai_api_key'] = new_key
                st.rerun()
            else:
                if selected_key:
                    st.success(f"Logged in with key '{selected_key}'")
                    st.session_state['openai_api_key'] = selected_key
                    st.rerun()
                else:
                    st.error("API Key is required to login")

