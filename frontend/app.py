"""
Multi-Agent RAG System – Streamlit Frontend
============================================
A comprehensive UI with both manual controls and agentic chat
for FAQ, Weather, and Todo operations.
"""

import streamlit as st
from api_client import APIClient

# ── Page config ──
st.set_page_config(
    page_title="Multi-Agent RAG System",
    page_icon="🤖",
    layout="wide",
)

# ── Session state init ──
if "api" not in st.session_state:
    st.session_state.api = APIClient()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

api: APIClient = st.session_state.api


# ───────────────────── Helpers ─────────────────────


def _render_response(response):
    """Render a chat response (can be str, dict, or list)."""
    if isinstance(response, str):
        st.markdown(response)
    elif isinstance(response, dict):
        # Show message if present
        msg = response.get("message")
        if msg:
            st.markdown(f"**{msg}**")
        # Show structured data
        data = response.get("task") or response.get("tasks") or response.get("weather") or response.get("result")
        if data:
            st.json(data)
        # If no known keys, show the whole dict
        if not msg and not data:
            st.json(response)
    elif isinstance(response, list):
        if not response:
            st.info("No items found.")
        else:
            st.json(response)
    else:
        st.write(response)


# ───────────────────── Auth Gate ─────────────────────


def show_auth_page():
    """Render login / register forms."""
    st.title("🔐 Multi-Agent RAG System")
    st.markdown("Please log in or register to continue.")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            submitted = st.form_submit_button("Login")
            if submitted:
                if not username or not password:
                    st.warning("Please enter both username and password.")
                else:
                    try:
                        data = api.login(username, password)
                        st.session_state.authenticated = True
                        st.session_state.username = data["username"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {e}")

    with tab_register:
        with st.form("register_form"):
            new_user = st.text_input("Username", key="reg_user")
            new_pass = st.text_input("Password", type="password", key="reg_pass")
            full_name = st.text_input("Full Name (optional)", key="reg_name")
            submitted = st.form_submit_button("Register")
            if submitted:
                if not new_user or not new_pass:
                    st.warning("Username and password are required.")
                else:
                    try:
                        data = api.register(new_user, new_pass, full_name)
                        st.success(
                            f"Account created for **{data['username']}**! "
                            f"Please switch to the Login tab."
                        )
                    except Exception as e:
                        st.error(f"Registration failed: {e}")


# ───────────────────── Main App ─────────────────────


def show_main_app():
    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.chat_history = []
            st.session_state.api = APIClient()
            st.rerun()

        st.divider()
        st.markdown("### Navigation")
        page = st.radio(
            "Go to",
            ["💬 AI Chat Agent", "🌤️ Weather", "📋 Todo Manager"],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("Multi-Agent RAG System v1.0")
        st.caption(
            "Use **AI Chat Agent** for natural language interaction, "
            "or use the **Weather** / **Todo Manager** pages for direct control."
        )

    # ── Page routing ──
    if page == "💬 AI Chat Agent":
        render_chat_page()
    elif page == "🌤️ Weather":
        render_weather_page()
    elif page == "📋 Todo Manager":
        render_todo_page()


# ───────────────────── Chat Page ─────────────────────


def render_chat_page():
    st.title("💬 AI Chat Agent")
    st.caption(
        "Ask anything — FAQ questions about BigRock services, weather queries, "
        "or todo management. The orchestrator agent routes your query automatically."
    )

    # Quick-action suggestion chips
    with st.expander("💡 Try these example queries", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**FAQ (RAG Agent)**")
            st.code("What domains are available from BigRock?", language=None)
            st.code("How does the BigRock Affiliate program work?", language=None)
            st.code("Why do I need a professional email?", language=None)
        with col2:
            st.markdown("**Weather (Tool Agent)**")
            st.code("What is the weather in Mumbai?", language=None)
            st.code("Temperature in New York right now", language=None)
        with col3:
            st.markdown("**Todos (Tool Agent via MCP)**")
            st.code("Create a todo: Buy BigRock domain", language=None)
            st.code("Show me all my tasks (completed and not completed)", language=None)
            st.code("Mark the BigRock task as completed", language=None)

    st.divider()

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                _render_response(msg["content"])
            else:
                st.markdown(msg["content"])

    # User input
    if prompt := st.chat_input("Type your message…"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    result = api.chat(prompt)
                    answer = result.get("response", "No response received.")
                except Exception as e:
                    answer = f"⚠️ Error: {e}"
                _render_response(answer)

        st.session_state.chat_history.append({"role": "assistant", "content": answer})


# ───────────────────── Weather Page ─────────────────────


def render_weather_page():
    st.title("🌤️ Weather")
    st.caption("Fetch current weather for any city using the Open-Meteo API (free, no API key needed).")

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        city = st.text_input("City name", placeholder="e.g. Mumbai, London, New York", label_visibility="collapsed")
    with col_btn:
        fetch_clicked = st.button("🔍 Get Weather", use_container_width=True)

    if fetch_clicked:
        with st.spinner("Fetching weather…"):
            try:
                data = api.get_weather(city if city.strip() else None)

                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🌡️ Temperature", f"{data['temperature']}°C")
                col2.metric("🤒 Feels Like", f"{data['feels_like']}°C")
                col3.metric("💧 Humidity", f"{data['humidity']}%")
                col4.metric("💨 Wind Speed", f"{data['wind_speed']} m/s")

                st.success(f"**{data['city']}**: {data['description'].title()}")

                if data.get("note"):
                    st.warning(data["note"])

                # Show raw JSON in expander
                with st.expander("📄 Raw API Response"):
                    st.json(data)

            except Exception as e:
                st.error(f"Failed to fetch weather: {e}")


# ───────────────────── Todo Page ─────────────────────


def render_todo_page():
    st.title("📋 Todo Manager")
    st.caption("Create, view, update, and delete tasks. All tasks are persisted in the database.")

    # ── Create Task ──
    with st.expander("➕ Create New Task", expanded=False):
        with st.form("create_task_form"):
            title = st.text_input("Title")
            description = st.text_area("Description (optional)")
            if st.form_submit_button("Create Task"):
                if not title.strip():
                    st.warning("Title is required.")
                else:
                    try:
                        result = api.create_task(title.strip(), description.strip())
                        st.success(
                            f"✅ Task created: **{result.get('title', title)}** "
                            f"(ID: `{result.get('id', 'N/A')}`)"
                        )
                    except Exception as e:
                        st.error(f"Failed to create task: {e}")

    st.divider()

    # ── Filter & Refresh ──
    col_filter, col_refresh = st.columns([3, 1])
    with col_filter:
        show_filter = st.selectbox(
            "Show tasks",
            ["All Tasks", "Pending Only", "Completed Only"],
            key="todo_filter",
        )
    with col_refresh:
        st.write("")  # spacing
        st.button("🔄 Refresh", key="refresh_tasks", use_container_width=True)

    include_completed = show_filter != "Pending Only"

    # ── Task List ──
    try:
        tasks = api.list_tasks(include_completed=include_completed)

        # Client-side filter for "Completed Only"
        if show_filter == "Completed Only":
            tasks = [t for t in tasks if t.get("completed")]

        if not tasks:
            st.info("No tasks found. Create one above!")
            return

        st.markdown(f"**{len(tasks)} task(s) found**")

        for task in tasks:
            task_id = task.get("id", "?")
            title = task.get("title", "Untitled") or "(no title)"
            done = task.get("completed", False)
            desc = task.get("description", "")
            status_emoji = "✅" if done else "⬜"

            with st.container():
                # Main row: status, title, action buttons
                col_status, col_info, col_actions = st.columns([0.5, 5, 3])

                with col_status:
                    st.markdown(f"### {status_emoji}")

                with col_info:
                    st.markdown(f"**{title}**")
                    if desc:
                        st.caption(desc)
                    st.caption(f"ID: `{task_id}`")

                with col_actions:
                    btn_cols = st.columns(3)

                    # Toggle complete/incomplete
                    if not done:
                        if btn_cols[0].button("✅ Complete", key=f"done_{task_id}", use_container_width=True):
                            try:
                                api.update_task(task_id, completed=True)
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                    else:
                        if btn_cols[0].button("↩️ Reopen", key=f"undo_{task_id}", use_container_width=True):
                            try:
                                api.update_task(task_id, completed=False)
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))

                    # Edit button
                    if btn_cols[1].button("✏️ Edit", key=f"edit_{task_id}", use_container_width=True):
                        st.session_state[f"editing_{task_id}"] = True

                    # Delete button
                    if btn_cols[2].button("🗑️ Delete", key=f"del_{task_id}", use_container_width=True):
                        try:
                            api.delete_task(task_id)
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                # Edit form (appears below the task when Edit is clicked)
                if st.session_state.get(f"editing_{task_id}", False):
                    with st.form(f"edit_form_{task_id}"):
                        new_title = st.text_input("Title", value=title if title != "(no title)" else "")
                        new_desc = st.text_area("Description", value=desc)
                        new_completed = st.checkbox("Completed", value=done)

                        subcols = st.columns(2)
                        if subcols[0].form_submit_button("💾 Save Changes"):
                            try:
                                api.update_task(
                                    task_id,
                                    title=new_title,
                                    description=new_desc,
                                    completed=new_completed,
                                )
                                st.session_state[f"editing_{task_id}"] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Update failed: {e}")
                        if subcols[1].form_submit_button("Cancel"):
                            st.session_state[f"editing_{task_id}"] = False
                            st.rerun()

                st.divider()

    except Exception as e:
        st.error(f"Failed to load tasks: {e}")


# ───────────────────── Entry point ─────────────────────

if not st.session_state.authenticated:
    show_auth_page()
else:
    show_main_app()
