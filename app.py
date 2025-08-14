import os
import time
import streamlit as st
from feishu_screenshot import FeishuScreenshot
from ai_summary import AISummary

st.set_page_config(page_title="飞书转图文助手", page_icon="📝", layout="centered")

st.title("飞书转图文助手")
st.caption("对飞书笔记进行截图，选择性使用 AI 生成小红书文案。当前版本不支持自动发布到小红书。")

with st.form("params_form"):
    st.subheader("参数设置")
    note_url = st.text_input("飞书笔记网址", placeholder="https://...", help="支持飞书云文档 / Wiki 页面")

    # 接受宽高比 r（宽/高），宽采用浏览器默认宽度，由 r 计算高度
    r = st.number_input("截图宽高比 r = 宽/高", min_value=0.2, max_value=5.0, value=0.5625, step=0.01, help="例如 9:16 约等于 0.5625")

    st.markdown("---")
    use_ai = st.checkbox("使用 AI 生成小红书文案", value=False)
    api_key = st.text_input("OpenAI API Key", type="password", disabled=not use_ai)
    base_url = st.text_input("OpenAI Base URL", placeholder="https://api.openai.com/v1", disabled=not use_ai)

    st.markdown("---")
    output_dir = st.text_input("输出目录", value="output")
    screenshots_dir = st.text_input("截图目录", value="screenshots")
    run = st.form_submit_button("开始处理", type="primary")

if run:
    if not note_url:
        st.error("请填写飞书笔记网址")
        st.stop()

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(screenshots_dir, exist_ok=True)

    # 截图
    with st.status("正在对飞书笔记截图…", expanded=True) as status:
        try:
            shot = FeishuScreenshot(aspect_ratio=r)
            st.write("打开页面…")
            files, title = shot.take_full_screenshot(note_url, output_dir=screenshots_dir)
            if not files:
                st.error("截图失败，请检查链接或网络")
                st.stop()
            st.write(f"截图完成，共 {len(files)} 张。标题：{title}")
            status.update(label="截图完成", state="complete", expanded=False)
        except Exception as e:
            st.exception(e)
            st.stop()

    # 读取正文（可选：用于 AI 生成文案）
    content_text = ""
    try:
        shot2 = FeishuScreenshot(aspect_ratio=r)
        if shot2.navigate_to_note(note_url):
            content_text = shot2.get_note_content()
    except Exception:
        pass

    st.subheader("截图预览")
    for fp in sorted(files):
        st.image(fp, caption=os.path.basename(fp), use_column_width=True)

    # AI 生成文案
    ai_result = None
    if use_ai:
        with st.status("正在调用 AI 生成文案…", expanded=True) as status:
            try:
                summarizer = AISummary(api_key=api_key or None, base_url=base_url or None)
                ai_result = summarizer.generate_summary(content_text or "")
                st.write("AI 生成完成")
                status.update(label="AI 生成完成", state="complete", expanded=False)
            except Exception as e:
                st.exception(e)

    st.subheader("结果导出")
    if ai_result:
        st.markdown("**AI 标题**")
        st.write(ai_result.get("title", ""))
        st.markdown("**AI 内容**")
        st.text_area("文案", ai_result.get("content", ""), height=220)
        st.markdown("**AI 话题**")
        st.write(" ".join(ai_result.get("topics", [])))

        # 保存草稿
        draft_path = os.path.join(output_dir, f"draft_{int(time.time())}.txt")
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(f"标题: {ai_result.get('title','')}\n\n")
            f.write(f"内容:\n{ai_result.get('content','')}\n\n")
            f.write(f"话题:\n{' '.join(ai_result.get('topics', []))}\n")
            f.write(f"截图文件:\n" + "\n".join(files))
        st.success(f"草稿已保存: {draft_path}")

    st.success("处理完成！")
    st.info("小红书自动发布功能尚未实现，请将图片与文案手动发布。")

st.sidebar.title("关于")
st.sidebar.info(
    "该工具用于将飞书笔记转为图片，并可选用 AI 生成小红书风格文案。\n"
    "当前版本未实现自动发布功能。"
) 