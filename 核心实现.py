import re
import sys
import tkinter as tk
from tkinter import font

# 打开combined.js文件或者page1.js文件
# 若无法打开，返回错误并终止程序
try:
    # 首先尝试打开combined.js
    with open('combined.js', 'r', encoding='utf-8') as file:
        content = file.read()
        print("成功读取combined.js文件")

except FileNotFoundError:
    print("combined.js文件不存在，尝试打开page1.js...")
    try:
        # 若combined.js不存在，则尝试打开page1.js
        with open('page1.js', 'r', encoding='utf-8') as file:
            content = file.read()
            print("成功读取page1.js文件")
            
    except FileNotFoundError:
        print("错误：page1.js文件也不存在")
        sys.exit(1)  # 两个文件都不存在时退出
        
except Exception as e:  # 处理其他未知错误
    print(f"读取文件时发生未知错误: {str(e)}")

# --- 2. 核心处理逻辑 ---

# 存储最终数据的列表，格式：{'id': 数字, 'data': [明文列表]}
all_extracted_blocks = []

# 使用 'var pageConfig' 将整个文本切分为多个独立的题目块
# 这样我们可以单独处理每一段听力材料
raw_blocks = content.split('var pageConfig')
print(f"初步切分出 {len(raw_blocks)} 个数据块")

for index, block in enumerate(raw_blocks):
    if not block.strip():
        continue

    # A. 提取该块的 T 编号 (作为排序依据)
    # 匹配 media/T1-ZC.mp3 或 media/T1_ZC.mp3
    t_match = re.search(r'media/T(\d+)[-_]ZC', block)
    
    if t_match:
        t_num = int(t_match.group(1))
        
        # B. 在当前块内，使用您【原来验证成功】的正则逻辑提取内容
        # 查找所有位于 "answer_text" 和 "knowledge" 之间的片段
        # 这一步保证了同一段材料下的题目（如11-13题）保持原有顺序
        pattern_inner = r'"answer_text"(.*?)"knowledge"'
        matches = re.findall(pattern_inner, block, re.DOTALL)
        
        block_contents = []
        
        if matches:
            for match_str in matches:
                # 提取答案字母 (A, B, C, D)
                # 使用宽松匹配，找到第一个出现的字母
                option_match = re.search(r'[A-D]', match_str)
                if option_match:
                    option = option_match.group()
                    
                    # 提取该字母对应的 content
                    # 匹配 "id":"B" ... "content":"..."
                    # 使用 re.DOTALL 防止跨行导致匹配失败
                    content_pattern = r'"id":"{}"(.*?)"content":"(.*?)"'.format(option)
                    content_extract = re.search(content_pattern, match_str, re.DOTALL)
                    
                    if content_extract:
                        # 提取 content (第二个括号的内容)
                        text = content_extract.group(2)
                        block_contents.append(text)
        
        if block_contents:
            print(f"--> 找到 T{t_num} 数据块，提取到 {len(block_contents)} 条内容")
            all_extracted_blocks.append({'id': t_num, 'data': block_contents})
    else:
        # 如果某些块没有 T 编号（可能是非题目配置块），忽略
        pass

# C. 全局排序
# 按照 T 编号从小到大排序
all_extracted_blocks.sort(key=lambda x: x['id'])

print("排序完成，准备显示...")

# D. 展平列表用于显示
Outs = []
for item in all_extracted_blocks:
    Outs.extend(item['data'])

# --- 3. GUI 显示 ---
window = tk.Tk()
window.title("天学网分析 (按T序号排序)")
window.attributes("-topmost", True)

output_text = tk.Text(window)
output_text.pack(expand=True, fill='both') # 允许文本框随窗口调整
custom_font = font.Font(family="宋体", size=12)
output_text.configure(font=custom_font)

if not Outs:
    output_text.insert(tk.END, "未提取到任何内容，请检查控制台输出的错误信息。")
else:
    for i, out in enumerate(Outs):
        show = f"{i + 1} {out}"
        output_text.insert(tk.END, show + "\n")

window.mainloop()
