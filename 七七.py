import streamlit as st
import requests
import base64
import json
from io import BytesIO
from PIL import Image

# ========== 页面配置 ==========
st.set_page_config(
    page_title="七七AI助手",
    page_icon="7️⃣",
    layout="wide",
    initial_sidebar_state="auto"
)

# ========== 自定义CSS ==========
st.markdown("""
<style>
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: #888; border-radius: 10px; }
    .reasoning-box {
        background-color: #f0f2f6;
        border-left: 4px solid #ff4b4b;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-size: 0.9rem;
        color: #444;
    }
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 20px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #f9f9f9;
    }
    .login-title {
        text-align: center;
        font-size: 24px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ========== 登录状态管理 ==========
def init_login_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.current_user = None

init_login_state()

# ========== 登录界面 ==========
def show_login():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🔐 登录 七七AI</div>', unsafe_allow_html=True)
    username = st.text_input("账号", key="login_username")
    password = st.text_input("密码", type="password", key="login_password")
    col1, col2 = st.columns(2)
    with col1:
        login_btn = st.button("登录", use_container_width=True)
    with col2:
        register_btn = st.button("注册新账号", use_container_width=True)
    
    if login_btn:
        if username and password:
            # 从 localStorage 获取用户信息（前端模拟）
            st.markdown(f"""
            <script>
            const users = JSON.parse(localStorage.getItem('ai_users') || '{{}}');
            const user = users['{username}'];
            if (user && user.password === '{password}') {{
                localStorage.setItem('current_user', '{username}');
                window.location.reload();
            }} else {{
                alert('账号或密码错误');
            }}
            </script>
            """, unsafe_allow_html=True)
        else:
            st.warning("请输入账号和密码")
    
    if register_btn:
        if username and password:
            # 注册：检查账号是否已存在，若不存在则创建
            st.markdown(f"""
            <script>
            const users = JSON.parse(localStorage.getItem('ai_users') || '{{}}');
            if (users['{username}']) {{
                alert('账号已存在，请直接登录');
            }} else {{
                users['{username}'] = {{ password: '{password}', created: new Date().toISOString() }};
                localStorage.setItem('ai_users', JSON.stringify(users));
                localStorage.setItem('current_user', '{username}');
                window.location.reload();
            }}
            </script>
            """, unsafe_allow_html=True)
        else:
            st.warning("请输入账号和密码")
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 从 localStorage 加载用户历史 ==========
def load_user_history(username):
    # 通过 JavaScript 读取 localStorage 中该用户的 history，并通过 URL 参数传递
    st.markdown(f"""
    <script>
    const key = 'history_{username}';
    const saved = localStorage.getItem(key);
    if (saved) {{
        const urlParams = new URLSearchParams(window.location.search);
        if (!urlParams.has('history')) {{
            const encoded = encodeURIComponent(saved);
            window.location.href = window.location.pathname + '?history=' + encoded + '&user={username}';
        }}
    }} else {{
        // 无历史，直接标记已加载
        const urlParams = new URLSearchParams(window.location.search);
        if (!urlParams.has('loaded')) {{
            window.location.href = window.location.pathname + '?loaded=true&user={username}';
        }}
    }}
    </script>
    """, unsafe_allow_html=True)

# ========== 主应用 ==========
def main_app():
    # ========== API Key ==========
    if "API_KEY" not in st.secrets:
        st.error("⚠️ 请在 Streamlit Secrets 中配置 API_KEY")
        st.stop()
    API_KEY = st.secrets["API_KEY"]
    URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    MODEL = "glm-4v-plus"

    # ========== 初始化 session_state ==========
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "你是七七，一个友好、幽默、乐于助人的AI助手。请始终以七七的身份回应，语气活泼可爱。"}
        ]
    if "count" not in st.session_state:
        st.session_state.count = 0
    if "queries" not in st.session_state:
        st.session_state.queries = []
    if "upload_key" not in st.session_state:
        st.session_state.upload_key = 0
    if "history_loaded" not in st.session_state:
        st.session_state.history_loaded = False

    # ========== 从 URL 加载历史（由前端传递） ==========
    if not st.session_state.history_loaded:
        if "history" in st.query_params:
            try:
                history_json = st.query_params["history"]
                history_data = json.loads(history_json)
                st.session_state.messages = history_data.get("messages", [
                    {"role": "system", "content": "你是七七，一个友好、幽默、乐于助人的AI助手。请始终以七七的身份回应，语气活泼可爱。"}
                ])
                st.session_state.count = history_data.get("count", 0)
                st.session_state.queries = history_data.get("queries", [])
            except:
                pass
            # 清除 URL 参数
            st.query_params.clear()
            st.session_state.history_loaded = True
            st.rerun()
        elif "loaded" in st.query_params:
            st.query_params.clear()
            st.session_state.history_loaded = True
            st.rerun()
        else:
            # 第一次加载，尝试从 localStorage 读取历史
            load_user_history(st.session_state.current_user)

    # ========== 标题区 ==========
    st.title("7️⃣ 七七")
    st.markdown("我是一个可爱又聪明的AI助手，叫我七七就好啦！")

    # ========== 侧边栏 ==========
    with st.sidebar:
        st.header("📊 统计")
        st.metric("询问次数", st.session_state.count)
        st.markdown("---")
        st.header("📝 历史询问")
        if st.session_state.queries:
            for i, q in enumerate(st.session_state.queries, 1):
                st.markdown(f"{i}. {q[:60]}{'...' if len(q) > 60 else ''}")
        else:
            st.info("暂无询问记录")
        st.markdown("---")
        if st.button("🗑️ 清空对话", use_container_width=True):
            system_msg = [msg for msg in st.session_state.messages if msg["role"] == "system"]
            st.session_state.messages = system_msg
            st.session_state.count = 0
            st.session_state.queries = []
            st.session_state.upload_key += 1
            # 清除 localStorage 中该用户的 history
            st.markdown(f"""
            <script>
            const key = 'history_{st.session_state.current_user}';
            localStorage.removeItem(key);
            </script>
            """, unsafe_allow_html=True)
            st.rerun()
        if st.button("🚪 退出登录", use_container_width=True):
            st.markdown("<script>localStorage.removeItem('current_user'); window.location.reload();</script>", unsafe_allow_html=True)
            st.stop()
        st.caption("💡 支持 JPG/PNG 图片，最大 200MB")
        st.caption("📌 对话自动保存在您的账号下，下次登录自动恢复")

    # ========== 聊天记录显示 ==========
    for msg in st.session_state.messages:
        if msg["role"] == "system":
            continue
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, list):
            text_parts = [part["text"] for part in content if part["type"] == "text"]
            display_text = text_parts[0] if text_parts else "📷 [图片消息]"
        else:
            display_text = content
        with st.chat_message(role):
            st.markdown(display_text)
            if "reasoning" in msg and msg["reasoning"]:
                st.markdown(
                    f"""
                    <div class="reasoning-box">
                        <strong>💭 思考过程</strong><br>
                        {msg["reasoning"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # ========== 输入区 ==========
    col1, col2 = st.columns([5, 1.2])
    with col1:
        prompt = st.chat_input("在这里输入你的问题...")
    with col2:
        st.markdown("**📷 上传图片**")
        uploaded_file = st.file_uploader(
            "点击上传图片",
            type=["jpg", "jpeg", "png"],
            label_visibility="visible",
            key=f"upload_{st.session_state.upload_key}"
        )
        st.caption("支持 JPG/PNG，最大 200MB")

    # ========== 处理用户请求 ==========
    if prompt or uploaded_file:
        # 构建用户消息内容
        user_content = []
        if prompt:
            user_content.append({"type": "text", "text": prompt})
        if uploaded_file:
            try:
                image = Image.open(uploaded_file)
                image.thumbnail((1024, 1024))
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                })
            except Exception as e:
                st.error(f"图片处理失败：{e}")
                st.stop()
        if not prompt and uploaded_file:
            user_content.append({"type": "text", "text": "请描述这张图片的内容。"})
        
        # 记录用户消息
        st.session_state.messages.append({"role": "user", "content": user_content})
        st.session_state.count += 1
        if prompt:
            st.session_state.queries.append(prompt)
        else:
            st.session_state.queries.append("📷 [图片消息]")
        
        # 立即显示用户消息
        with st.chat_message("user"):
            if prompt:
                st.markdown(prompt)
            if uploaded_file:
                st.image(image, caption="你上传的图片", width=200)
        
        # 调用 AI
        with st.chat_message("assistant"):
            with st.spinner("七七正在思考..."):
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": MODEL,
                    "messages": st.session_state.messages,
                    "temperature": 0.8,
                    "top_p": 0.9
                }
                try:
                    response = requests.post(URL, headers=headers, json=payload, timeout=30)
                    response.raise_for_status()
                    result = response.json()
                    ai_message = result["choices"][0]["message"]
                    ai_content = ai_message.get("content", "")
                    reasoning = ai_message.get("reasoning_content", "")
                    
                    ai_msg = {"role": "assistant", "content": ai_content}
                    if reasoning:
                        ai_msg["reasoning"] = reasoning
                    st.session_state.messages.append(ai_msg)
                    
                    st.markdown(ai_content)
                    if reasoning:
                        st.markdown(
                            f"""
                            <div class="reasoning-box">
                                <strong>💭 思考过程</strong><br>
                                {reasoning}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    # 重置上传组件
                    st.session_state.upload_key += 1
                    
                except requests.exceptions.Timeout:
                    st.error("⏰ 网络超时，请稍后再试")
                except requests.exceptions.ConnectionError:
                    st.error("📡 网络连接失败，请检查网络或稍后重试")
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        st.error("🔑 API Key 无效，请在 Secrets 中检查配置")
                    elif e.response.status_code == 429:
                        st.error("📊 请求过于频繁，请稍后再试")
                    else:
                        st.error(f"❌ API 错误：{e}")
                except Exception as e:
                    st.error(f"❌ 未知错误：{e}")
                finally:
                    # 每次对话完成后，保存当前历史到 localStorage（按用户）
                    history_data = {
                        "queries": st.session_state.queries,
                        "count": st.session_state.count,
                        "messages": [msg for msg in st.session_state.messages if msg["role"] != "system"]
                    }
                    json_str = json.dumps(history_data, ensure_ascii=False)
                    st.markdown(f"""
                    <script>
                    const key = 'history_{st.session_state.current_user}';
                    localStorage.setItem(key, `{json_str}`);
                    </script>
                    """, unsafe_allow_html=True)
                    st.rerun()

# ========== 主流程 ==========
def check_login_status():
    # 通过 JavaScript 获取当前登录用户（存在 localStorage 中）
    if "current_user" not in st.session_state:
        st.markdown("""
        <script>
        const user = localStorage.getItem('current_user');
        if (user) {
            window.location.href = window.location.pathname + '?user=' + user;
        } else {
            // 未登录，无需操作
        }
        </script>
        """, unsafe_allow_html=True)
        if "user" in st.query_params:
            st.session_state.current_user = st.query_params["user"]
            st.query_params.clear()
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.session_state.logged_in = False
    else:
        st.session_state.logged_in = True

check_login_status()

if st.session_state.get("logged_in", False):
    main_app()
else:
    show_login()