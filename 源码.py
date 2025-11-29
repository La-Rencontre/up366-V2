import os
import re
import sys
import tkinter as tk
from tkinter import font
from tkinter import filedialog
from tkinter import messagebox

# ==========================================
# 核心逻辑 1: 模拟 Bat 文件的合并与排序功能
# ==========================================
def get_merged_content_from_folder(source_path):
    """
    模仿原 Bat 脚本逻辑：
    1. 进入 questions 目录
    2. 遍历子文件夹
    3. 从 media/*.mp3 中提取 T 序号
    4. 从 net/*.js 或 *.js 中读取内容
    5. 按 T 序号排序并合并
    """
    
    questions_path = os.path.join(source_path, "questions")
    
    if not os.path.exists(questions_path):
        raise FileNotFoundError(f"在路径下未找到 'questions' 文件夹！\n请确认您选择的是包含 questions 目录的父级文件夹。")

    # 存储提取到的数据块: list of tuples (t_number, file_content)
    extracted_files = []
    
    # 遍历 questions 下的一级子目录
    for folder_name in os.listdir(questions_path):
        folder_full_path = os.path.join(questions_path, folder_name)
        
        if not os.path.isdir(folder_full_path):
            continue
            
        # --- A. 获取 T 序号 (模拟 Bat 的 media 查找逻辑) ---
        t_num = 999 # 默认排序号，如果没找到 T 号则排在最后
        media_path = os.path.join(folder_full_path, "media")
        
        if os.path.exists(media_path):
            for file in os.listdir(media_path):
                # 匹配 T4-ZC.mp3 或 T10_ZC.mp3
                match = re.search(r'T(\d+)[-_]ZC', file)
                if match:
                    t_num = int(match.group(1))
                    break # 找到一个就可以确定该文件夹的序号了
        
        # --- B. 查找 JS 文件 (模拟 Bat 的 net/ 优先逻辑) ---
        js_content = None
        js_file_path = None
        
        # 1. 优先找 net/*.js
        net_path = os.path.join(folder_full_path, "net")
        if os.path.exists(net_path):
            for file in os.listdir(net_path):
                if file.endswith(".js"):
                    js_file_path = os.path.join(net_path, file)
                    break
        
        # 2. 如果没找到，找根目录下 *.js
        if not js_file_path:
            for file in os.listdir(folder_full_path):
                if file.endswith(".js"):
                    js_file_path = os.path.join(folder_full_path, file)
                    break
                    
        # --- C. 读取文件并存储 ---
        if js_file_path:
            try:
                with open(js_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    extracted_files.append((t_num, content))
            except Exception as e:
                print(f"读取出错: {js_file_path} - {e}")

    # --- D. 排序与合并 ---
    if not extracted_files:
        return None, 0

    # 按 T 序号 (tuple 的第一个元素) 排序
    extracted_files.sort(key=lambda x: x[0])
    
    # 合并所有内容
    merged_content = ""
    for _, content in extracted_files:
        merged_content += content + "\n"
        
    return merged_content, len(extracted_files)

# ==========================================
# 核心逻辑 2: 答案提取与解析
# ==========================================
def analyze_content(content):
    # 依然保留分块逻辑以防万一，虽然已经合并好了
    raw_blocks = content.split('var pageConfig')
    final_outs = []

    for block in raw_blocks:
        if not block.strip():
            continue

        # 使用最稳定的正则：查找 "answer_text" ... "knowledge" 之间的块
        pattern_inner = r'"answer_text"(.*?)"knowledge"'
        matches = re.findall(pattern_inner, block, re.DOTALL)
        
        if matches:
            for match_str in matches:
                # 1. 提取选项字母
                option_match = re.search(r'[A-D]', match_str)
                if option_match:
                    option = option_match.group()
                    # 2. 提取内容
                    content_pattern = r'"id":"{}"(.*?)"content":"(.*?)"'.format(option)
                    content_extract = re.search(content_pattern, match_str, re.DOTALL)
                    if content_extract:
                        text = content_extract.group(2)
                        final_outs.append(text)
    return final_outs

# ==========================================
# GUI 界面逻辑
# ==========================================
def run_process():
    # 1. 获取文件夹路径
    folder_path = filedialog.askdirectory(title="请选择包含 'questions' 文件夹的目录")
    if not folder_path:
        return
    
    # 清空界面
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "正在扫描并合并文件...\n")
    window.update()
    
    try:
        # 2. 执行合并 (替代 Bat)
        merged_content, file_count = get_merged_content_from_folder(folder_path)
        
        if not merged_content:
            messagebox.showwarning("未找到文件", "未能在 questions 文件夹下找到有效的 JS 数据文件。")
            output_text.insert(tk.END, "扫描失败。\n")
            return
            
        output_text.insert(tk.END, f"成功合并 {file_count} 个文件片段。\n正在提取答案...\n\n")
        
        # 3. 执行分析
        answers = analyze_content(merged_content)
        
        # 4. 显示结果
        output_text.delete(1.0, tk.END) # 清空日志，只显示结果
        if not answers:
            output_text.insert(tk.END, "未提取到答案内容，请检查数据源是否正确。")
        else:
            for i, ans in enumerate(answers):
                output_text.insert(tk.END, f"{i + 1} {ans}\n")
                
        messagebox.showinfo("完成", f"处理完成！\n共找到 {len(answers)} 个答案。")
        
    except Exception as e:
        messagebox.showerror("错误", str(e))
        output_text.insert(tk.END, f"\n发生错误: {str(e)}")

# --- 主窗口配置 ---
window = tk.Tk()
window.title("天学网听力答案一键提取工具")
window.geometry("600x600")

# 顶部说明
header_frame = tk.Frame(window, pady=10, bg="#f0f0f0")
header_frame.pack(fill="x")
tk.Label(header_frame, text="请选择抓包数据的【上级目录】\n(该目录下应包含 questions 文件夹)", 
         bg="#f0f0f0", font=("微软雅黑", 10)).pack()

# 按钮
btn = tk.Button(header_frame, text="选择文件夹并开始", command=run_process, 
                bg="#0078d7", fg="white", font=("微软雅黑", 12, "bold"), padx=20, pady=8)
btn.pack(pady=10)

# 文本输出区
text_frame = tk.Frame(window, padx=10, pady=10)
text_frame.pack(expand=True, fill="both")

custom_font = font.Font(family="宋体", size=12)
output_text = tk.Text(text_frame, font=custom_font)
scrollbar = tk.Scrollbar(text_frame, command=output_text.yview)
output_text.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

window.mainloop()
