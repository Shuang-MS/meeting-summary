import streamlit as st
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig
import openai
import io
import speech_fast_transcription
import llm_analysis

# 设置页面配置
st.set_page_config(page_title="会议纪要助手", page_icon="🎧", layout="centered")

# 设置 Azure Speech 和 OpenAI API 密钥
AZURE_SPEECH_KEY = 'YOUR_AZURE_SPEECH_KEY'
AZURE_SPEECH_REGION = 'YOUR_AZURE_SPEECH_REGION'
OPENAI_API_KEY = 'YOUR_OPENAI_API_KEY'

openai.api_key = OPENAI_API_KEY

st.title("🎧 会议智能助手")

# 上传文件，添加图标
audio_file = st.file_uploader("🎤 上传音频文件", type=["wav", "mp3", "m4a"])
image_file = st.file_uploader("🖼️ 上传图像文件", type=["jpg", "jpeg", "png"])

user_prompt = st.text_input("📝 输入提示词，用于会议总结 (Optional)")

if st.button("🚀 处理") and (audio_file or image_file):
    transcription = None
    image_result = None
    with st.spinner("处理中，请稍候..."):
        # 转录音频
        
        if audio_file:
            result = speech_fast_transcription.fast_transcript(audio_file)
            
            if result:
                transcription = result
            else:
                transcription = "转录失败。"

        # 分析图像内容
        if image_file:
            image_result = llm_analysis.analysis_image(image_file)
        

        # 总结内容
        summary_prompt = f"""
        音频转录：{transcription}
        图像分析：{image_result}

        请提供一份侧重于会议内容和待办事项的总结。
        """

        summary = llm_analysis.analysis_text(user_prompt,summary_prompt)
       


    if transcription:
        st.subheader("📝 音频转录")
        # st.write(transcription)
        
        # 添加下载链接
        st.download_button(
            label="下载音频转录",
            data=transcription,
            file_name="transcription.txt",
            mime="text/plain"
        )
        
    st.subheader("📝 会议纪要")
    st.write(summary)
