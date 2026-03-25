import streamlit as st
import requests
import base64
import json
import os
from io import BytesIO
from PIL import Image

# ========== 页面配置 ==========
st.set_page_config(
    page_title="脆脆大王AI",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="auto"
)

# ========== 自定义CSS ==========
st.markdown("""
<style>
    .reasoning-box {
        background-color: #f0f2f6;
        border-left: 4px solid #ff4b4b;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-size: 0.9rem;
        color: #444;
    }
</style>
""", unsafe_allow_html=True)

# ========== API Key ==========
if "API_KEY" not in st.secrets:
    st.error("⚠️ 请在 Streamlit Secrets 中配置 API_KEY")
    st.stop()
API_KEY = st.secrets["API_KEY"]
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4v-plus"

# ========== 数据存储目录 ==========
DATA_DIR = "user_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_user_data_file(username):
    return os.path.join(DATA_DIR, f"{username}.json")

def load_user_data(username):
    file_path = get_user_data_file(username)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_user_data(username, data):
    file_path = get_user_data_file(username)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== 登录管理 ==========
def login():
    st.sidebar.title("🔐 登录")
    username = st.sidebar.text_input("用户名")
    password = st.sidebar.text_input("密码", type="password")
    login_btn = st.sidebar.button("登录/注册")
    if login_btn:
        if username.strip() == "":
            st.sidebar.error("用户名不能为空")
            return False
        # 简单验证：允许任意密码（或可设置统一密码）
        # 这里设置统一密码为 "123456" 或允许空密码，根据需求修改
        # 为了安全，可以设置复杂密码，或从 secrets 读取
        # 此处简单起见：密码固定为 "crispy2026"
        if password != "crispy2026":
            st.sidebar.error("密码错误")
            return False
        # 加载用户数据
        user_data = load_user_data(username)
        if user_data is None:
            # 新用户，初始化空数据
            user_data = {
                "queries": [],
                "count": 0,
                "messages": [{"role": "system", "content": "你是脆脆大王👑，一个友好、幽默、乐于助人的AI助手。请始终以脆脆大王的身份回应，语气活泼可爱。"}]
            }
            save_user_data(username, user_data)
        # 存入 session_state
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.messages = user_data["messages"]
        st.session_state.count = user_data["count"]
        st.session_state.queries = user_data["queries"]
        st.session_state.upload_key = 0
        st.rerun()
    return False

def logout():
    # 登出前保存数据
    if st.session_state.get("logged_in"):
        user_data = {
            "queries": st.session_state.queries,
            "count": st.session_state.count,
            "messages": st.session_state.messages
        }
        save_user_data(st.session_state.username, user_data)
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

# ========== 主程序 ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # 显示登录界面
    st.title("👑 脆脆大王")
    st.markdown("请登录以使用聊天功能")
    login()
    st.stop()
else:
    # 已登录，显示侧边栏用户信息和登出按钮
    with st.sidebar:
        st.write(f"👤 用户：{st.session_state.username}")
        if st.button("🚪 登出", use_container_width=True):
            logout()
        st.markdown("---")
    # 初始化其他状态
    if "upload_key" not in st.session_state:
        st.session_state.upload_key = 0

# ========== 标题区 ==========
st.title("👑 脆脆大王")
st.markdown("我是一个可爱又聪明的AI助手，叫我脆脆大王就好啦！")

# ========== 侧边栏统计和历史 ==========
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
        # 保存到文件
        user_data = {
            "queries": st.session_state.queries,
            "count": st.session_state.count,
            "messages": st.session_state.messages
        }
        save_user_data(st.session_state.username, user_data)
        st.rerun()
    st.caption("💡 支持 JPG/PNG 图片，最大 200MB")
    st.caption("📌 历史记录保存在服务器上，登录即可访问")

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
        with st.spinner("脆脆大王正在思考..."):
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
                
                # 保存到文件
                user_data = {
                    "queries": st.session_state.queries,
                    "count": st.session_state.count,
                    "messages": st.session_state.messages
                }
                save_user_data(st.session_state.username, user_data)
                
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
                st.rerun()