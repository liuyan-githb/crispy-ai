import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

# ========== 页面设置 ==========
st.set_page_config(page_title="脆脆大王AI", page_icon="👑")
st.title("👑 脆脆大王")
st.caption("我是一个可爱又聪明的AI助手，叫我脆脆大王就好啦！")

# ========== 从 Secrets 读取 API Key（安全） ==========
# 本地测试时，需要在 .streamlit/secrets.toml 中设置 API_KEY
# 部署到云端时，在 Streamlit Cloud 的 Secrets 中设置
if "API_KEY" not in st.secrets:
    st.error("请在 Streamlit Secrets 中配置 API_KEY")
    st.stop()
API_KEY = st.secrets["API_KEY"]

# ========== API 地址和模型 ==========
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4v-plus"   # 支持文本+图像（有免费额度）

# ========== 初始化 session_state ==========
if "messages" not in st.session_state:
    # 系统消息：设定AI固定身份为“脆脆大王”
    st.session_state.messages = [
        {"role": "system", "content": "你是脆脆大王👑，一个友好、幽默、乐于助人的AI助手。请始终以脆脆大王的身份回应，语气活泼可爱。"}
    ]
if "count" not in st.session_state:
    st.session_state.count = 0
if "queries" not in st.session_state:
    st.session_state.queries = []   # 存储用户每次的提问文本

# ========== 侧边栏：统计 + 历史询问 ==========
with st.sidebar:
    st.header("📊 统计")
    st.metric("询问次数", st.session_state.count)
    
    st.markdown("---")
    st.header("📝 历史询问")
    if st.session_state.queries:
        for i, q in enumerate(st.session_state.queries, 1):
            st.write(f"{i}. {q[:50]}{'...' if len(q) > 50 else ''}")
    else:
        st.write("暂无询问记录")
    
    st.markdown("---")
    if st.button("🗑️ 清空对话"):
        # 保留系统消息，清空其他消息
        system_msg = [msg for msg in st.session_state.messages if msg["role"] == "system"]
        st.session_state.messages = system_msg
        st.session_state.count = 0
        st.session_state.queries = []
        st.rerun()

# ========== 显示聊天历史（一左一右） ==========
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    role = msg["role"]
    content = msg["content"]
    
    # 处理可能的图片消息（content 可能是列表）
    if isinstance(content, list):
        text_parts = [part["text"] for part in content if part["type"] == "text"]
        display_text = text_parts[0] if text_parts else "[图片消息]"
    else:
        display_text = content
    
    with st.chat_message(role):
        st.markdown(display_text)
        # 如果有思考过程，单独显示
        if "reasoning" in msg and msg["reasoning"]:
            with st.expander("💭 思考过程"):
                st.markdown(msg["reasoning"])

# ========== 用户输入区域（文本 + 图片上传） ==========
col1, col2 = st.columns([5, 1])
with col1:
    prompt = st.chat_input("在这里输入你的问题...")
with col2:
    uploaded_file = st.file_uploader(
        "📷", type=["jpg", "jpeg", "png"], label_visibility="collapsed"
    )

# 处理用户消息
if prompt or uploaded_file:
    # 构建用户消息内容（支持文本+图片）
    user_content = []
    if prompt:
        user_content.append({"type": "text", "text": prompt})
    if uploaded_file:
        image = Image.open(uploaded_file)
        image.thumbnail((800, 800))   # 限制尺寸，避免超出 token 限制
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
        })
    
    # 如果没有文本只有图片，给一个默认提示
    if not prompt and uploaded_file:
        user_content.append({"type": "text", "text": "请描述这张图片的内容。"})
    
    # 将用户消息添加到历史
    st.session_state.messages.append({"role": "user", "content": user_content})
    st.session_state.count += 1
    if prompt:
        st.session_state.queries.append(prompt)
    else:
        st.session_state.queries.append("[图片消息]")
    
    # 立即显示用户消息（靠右）
    with st.chat_message("user"):
        if prompt:
            st.markdown(prompt)
        if uploaded_file:
            st.image(image, caption="你上传的图片", width=200)
    
    # 调用 API
    with st.chat_message("assistant"):
        with st.spinner("脆脆大王正在思考..."):
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            # 准备请求数据（messages 包含所有历史）
            payload = {
                "model": MODEL,
                "messages": st.session_state.messages,
                "temperature": 0.8,
                "top_p": 0.9
            }
            try:
                response = requests.post(URL, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                ai_message = result["choices"][0]["message"]
                ai_content = ai_message.get("content", "")
                reasoning = ai_message.get("reasoning_content", "")
                
                # 保存 AI 回复（包括思考过程）
                ai_msg = {"role": "assistant", "content": ai_content}
                if reasoning:
                    ai_msg["reasoning"] = reasoning
                st.session_state.messages.append(ai_msg)
                
                # 显示 AI 回复
                st.markdown(ai_content)
                if reasoning:
                    with st.expander("💭 思考过程"):
                        st.markdown(reasoning)
            except Exception as e:
                st.error(f"调用失败：{e}")
                st.stop()
    
    # 刷新页面以显示新消息
    st.rerun()