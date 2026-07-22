import streamlit as st
import requests
import json

OPENROUTER_API_KEY = "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"
SERPER_API_KEY = "c70f35baf4aaebbe2cc75470d0d14eac4b5595e7"
TAVILY_API_KEY = "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"

st.set_page_config(page_title="Zabi AI", layout="centered")

st.markdown("""
    <style>
    .stChatInputContainer {
        bottom: 20px;
    }
    [data-testid="stSidebar"] {
        background-color: #1e1e1e;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Test Big Models")
    model_choice = st.selectbox(
        "Choose Model",
        (
            "Llama 3.1 70B (Free)", 
            "Qwen 2 72B (Free)", 
            "Gemma 2 27B (Free)",
            "Dolphin Mixtral 8x22B (Paid Test)"
        ),
        label_visibility="collapsed"
    )

model_ids = {
    "Llama 3.1 70B (Free)": "meta-llama/llama-3.1-70b-instruct:free",
    "Qwen 2 72B (Free)": "qwen/qwen-2-72b-instruct:free",
    "Gemma 2 27B (Free)": "google/gemma-2-27b-it:free",
    "Dolphin Mixtral 8x22B (Paid Test)": "cognitivecomputations/dolphin-mixtral-8x22b"
}
selected_model = model_ids[model_choice]

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "✨"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Testing start karein..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="✨"):
        search_context = ""
        
        with st.status("Searching the web...", expanded=False) as status:
            try:
                serper_url = "https://google.serper.dev/search"
                serper_payload = json.dumps({"q": prompt})
                serper_headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
                res = requests.post(serper_url, headers=serper_headers, data=serper_payload)
                snippets = [item.get("snippet", "") for item in res.json().get("organic", [])[:5]]
                search_context = "\n\n".join(snippets)
                status.update(label="Web search complete", state="complete", expanded=False)
            except:
                status.update(label="Search skipped", state="complete", expanded=False)

        message_placeholder = st.empty()
        full_response = ""
        
        or_url = "https://openrouter.ai/api/v1/chat/completions"
        or_headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        
        system_prompt = f"Context from web:\n{search_context}\n\nAnswer thoroughly."
        api_messages = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        try:
            or_res = requests.post(or_url, headers=or_headers, json={"model": selected_model, "messages": api_messages, "stream": True}, stream=True)
            
            # Yahan hum ne Error Checker laga diya hai web app ke liye
            if or_res.status_code != 200:
                error_msg = f"**API ERROR {or_res.status_code}:** Ye model shayad paid hai ya available nahi. \n\nDetails: `{or_res.text}`"
                message_placeholder.error(error_msg)
            else:
                for line in or_res.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith('data: ') and decoded != 'data: [DONE]':
                            try:
                                chunk = json.loads(decoded[6:])
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    token = chunk['choices'][0]['delta'].get('content', '')
                                    full_response += token
                                    message_placeholder.markdown(full_response + "▌")
                            except:
                                pass
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            message_placeholder.error(f"Connection error: {e}")
