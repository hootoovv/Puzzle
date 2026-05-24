import matplotlib 

matplotlib.use('Agg') 

import matplotlib.pyplot as plt 
import matplotlib.patches as patches 
import matplotlib.font_manager as fm 
import numpy as np 

fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/SarasaMonoSC-Regular.ttf') 
fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/SarasaMonoSC-Bold.ttf') 
plt.rcParams['font.sans-serif'] = ['Sarasa Mono SC', 'DejaVu Sans'] 
plt.rcParams['axes.unicode_minus'] = False 

# ============================================================ # 加密流程图 - 更完整的版本，包含子步骤 # ============================================================ 

fig, ax = plt.subplots(1, 1, figsize=(18, 10)) 
ax.axis('off') 
ax.set_xlim(-1, 17) 
ax.set_ylim(-1, 11) 

# 定义流程框的位置和内容 
# 主流程（水平方向）
 
main_steps = [ 
              (1.5, 8.5, '原始图片\n(任意格式)', '#BBDEFB', '#1565C0'), 
              (5.0, 8.5, 'Padding填充\n(右侧+下侧\n添加黑色像素)', '#C8E6C9', '#2E7D32'), 
              (8.5, 8.5, '分块\n(m×n个\na×b子图块)', '#FFF9C4', '#F57F17'), 
              (12.0, 8.5, '按起点和顺序\n提取为一维\n数组A', '#FFE0B2', '#E65100'), 
              (15.5, 8.5, '加密图片\n(PNG+\n元数据)', '#F8BBD0', '#C62828'), 
             ] 

for x, y, text, fc, ec in main_steps: 
  rect = patches.FancyBboxPatch((x-1.2, y-0.9), 2.4, 1.8, boxstyle="round,pad=0.15", facecolor=fc, edgecolor=ec, linewidth=2.5) 
  ax.add_patch(rect) 
  ax.text(x, y, text, ha='center', va='center', fontsize=11, fontweight='bold', color='#1a1a1a') 
  
# 主流程箭头 
arrow_pairs = [(0,1), (1,2), (2,3), (3,4)] 

for i, j in arrow_pairs: 
  x1 = main_steps[i][0] + 1.2 
  x2 = main_steps[j][0] - 1.2 
  y = 8.5 
  ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle='->', color='#455A64', lw=2.5)) 
    
# 子步骤详情框 
sub_steps = [ 
              # Padding详情 
              (5.0, 5.8, [ 'W\' = ⌈W/a⌉ × a', 'H\' = ⌈H/b⌉ × b', 'padW = W\' - W', 'padH = H\' - H', ], '#E8F5E9', '#388E3C'), 
              
              # 提取详情 
              (8.5, 5.8, [ '起点: 1=左上 2=右上', ' 3=右下 4=左下', '顺序: 1=顺时针螺旋', ' 2=逆时针螺旋', ' 3=逐行前进', ' 4=逐列前进', ' 5=逐行迂回', ' 6=逐列迂回', ], '#FFFDE7', '#F9A825'), 
              
              # 数字序列驱动填充详情 
              (12.0, 5.8, [ '按数字序列C驱动填充:', '1. 取序列C中非零数字d', '2. 从当前位置前进d步', '3. 若目标位置已被占用,', ' 找下一个空白位置', '4. 放入数组A中下一个子图', '5. 重复直到所有子图放入', ], '#FFF3E0', '#EF6C00'), 
            ] 

for x, y, lines, fc, ec in sub_steps: 
  box_h = len(lines) * 0.42 + 0.4 
  rect = patches.FancyBboxPatch((x-1.8, y - box_h/2), 3.6, box_h, boxstyle="round,pad=0.12", facecolor=fc, edgecolor=ec, linewidth=1.8, linestyle='--') 
  ax.add_patch(rect) 
  for i, line in enumerate(lines): 
    ax.text(x, y + box_h/2 - 0.3 - i * 0.42, line, ha='center', va='center', fontsize=9.5, color='#333333', fontfamily='Sarasa Mono SC') 
    
# 连接线（从主步骤到子步骤） 
for idx, (x, y, lines, fc, ec) in enumerate(sub_steps): 
  main_x = main_steps[[1,2,3][idx]][0] 
  main_y = main_steps[[1,2,3][idx]][1] - 0.9 
  ax.annotate('', xy=(x, y + len(lines)*0.42/2 + 0.2), xytext=(main_x, main_y), arrowprops=dict(arrowstyle='->', color=ec, lw=1.5, linestyle='--')) 
  
# 元数据保存说明 
meta_text = '元数据格式:\npadW×padH_blockW×blockH_extractStart+Order_outputStart+Order.origFmt.seqKey\n例: 2×2_4×3_32_13.jpg.pi' 
rect = patches.FancyBboxPatch((13.5, 1.0), 3.5, 2.5, boxstyle="round,pad=0.12", facecolor='#E1F5FE', edgecolor='#0277BD', linewidth=1.8, linestyle='--') 
ax.add_patch(rect) 
ax.text(15.25, 2.25, meta_text, ha='center', va='center', fontsize=8.5, color='#01579B', fontfamily='Sarasa Mono SC', linespacing=1.5) 

# 连接元数据到最终输出 
ax.annotate('', xy=(15.5, 3.5), xytext=(15.5, 7.6), arrowprops=dict(arrowstyle='->', color='#0277BD', lw=1.5, linestyle='--')) 

# 步骤编号 
step_labels = ['步骤1', '步骤2', '步骤3', '步骤4', '步骤5'] 

for i, (x, y, text, fc, ec) in enumerate(main_steps): 
  ax.text(x, y + 1.3, step_labels[i], ha='center', va='center', fontsize=11, fontweight='bold', color=ec, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=ec, linewidth=1.5)) 
  ax.set_title('加密流程图', fontsize=18, fontweight='bold', y=0.98, pad=15) 
    
plt.tight_layout() 
plt.savefig('../paper_images/encryption_flow.png', dpi=150, bbox_inches='tight', facecolor='white') 
plt.close() 
print("加密流程图生成完成") 
            
# ============================================================ # 解密流程图 # ============================================================ 
fig, ax = plt.subplots(1, 1, figsize=(18, 10)) 
ax.axis('off') 
ax.set_xlim(-1, 17) 
ax.set_ylim(-1, 11) 

main_steps_dec = [ 
                  (1.5, 8.5, '加密图片\n(PNG+\n元数据)', '#F8BBD0', '#C62828'), 
                  (5.0, 8.5, '读取元数据\n提取解密\n参数', '#E1BEE7', '#6A1B9A'), 
                  (8.5, 8.5, '分块\n(m×n个\na×b子图块)', '#FFF9C4', '#F57F17'), 
                  (12.0, 8.5, '逆填充\n恢复一维\n数组A', '#FFE0B2', '#E65100'), 
                  (15.5, 8.5, '原始图片\n(已解密)', '#BBDEFB', '#1565C0'), 
                ] 

for x, y, text, fc, ec in main_steps_dec: 
  rect = patches.FancyBboxPatch((x-1.2, y-0.9), 2.4, 1.8, boxstyle="round,pad=0.15", facecolor=fc, edgecolor=ec, linewidth=2.5) 
  ax.add_patch(rect) 
  ax.text(x, y, text, ha='center', va='center', fontsize=11, fontweight='bold', color='#1a1a1a') 
  
# 主流程箭头 
for i in range(4): 
  x1 = main_steps_dec[i][0] + 1.2 
  x2 = main_steps_dec[i+1][0] - 1.2 
  y = 8.5 
  ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle='->', color='#455A64', lw=2.5)) 
  
# 子步骤 
sub_steps_dec = [ 
                  # 读取元数据详情 
                  (5.0, 5.5, [ '从PNG tEXt/EXIF中', '读取UserComment字段', '解析参数:', ' padW, padH, blockW, blockH', ' extractStart, extractOrder', ' outputStart, outputOrder', ' origFormat, sequenceKey', ], '#F3E5F5', '#7B1FA2'), 
                  
                  # 逆填充详情 
                  (8.5, 5.5, [ '将加密图片分割为', 'm×n个a×b子图块', '形成二维数组B', ], '#FFFDE7', '#F9A825'), 
                  
                  # 逆填充算法详情 
                  (12.0, 5.5, [ '按数字序列C重新计算', '每个子图的放置位置', '建立位置映射:', ' 位置Pi → 子图Si', '从数组B按映射提取', '恢复一维数组A', '再按提取起点/顺序', '逆映射恢复原始图片', ], '#FFF3E0', '#EF6C00'), 
                  
                ] 

for x, y, lines, fc, ec in sub_steps_dec: 
  box_h = len(lines) * 0.42 + 0.4 
  rect = patches.FancyBboxPatch((x-1.8, y - box_h/2), 3.6, box_h, boxstyle="round,pad=0.12", facecolor=fc, edgecolor=ec, linewidth=1.8, linestyle='--') 
  ax.add_patch(rect) 
  
  for i, line in enumerate(lines): 
    ax.text(x, y + box_h/2 - 0.3 - i * 0.42, line, ha='center', va='center', fontsize=9.5, color='#333333', fontfamily='Sarasa Mono SC') 
    
# 连接线 
for idx, (x, y, lines, fc, ec) in enumerate(sub_steps_dec): 
  main_x = main_steps_dec[[1,2,3][idx]][0] 
  main_y = main_steps_dec[[1,2,3][idx]][1] - 0.9 
  box_h = len(lines) * 0.42 + 0.4 
  ax.annotate('', xy=(x, y + box_h/2 + 0.1), xytext=(main_x, main_y), arrowprops=dict(arrowstyle='->', color=ec, lw=1.5, linestyle='--')) 
  
# 去Padding说明 
depad_text = '去除Padding:\n裁剪右侧padW像素\n裁剪下侧padH像素\n按origFormat保存' 
rect = patches.FancyBboxPatch((13.8, 1.5), 3.2, 2.2, boxstyle="round,pad=0.12", facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=1.8, linestyle='--') 
ax.add_patch(rect) 
ax.text(15.4, 2.6, depad_text, ha='center', va='center', fontsize=9.5, color='#0D47A1', fontfamily='Sarasa Mono SC', linespacing=1.4) 
ax.annotate('', xy=(15.5, 3.7), xytext=(15.5, 7.6), arrowprops=dict(arrowstyle='->', color='#1565C0', lw=1.5, linestyle='--')) 

# 步骤编号 
step_labels_dec = ['步骤1', '步骤2', '步骤3', '步骤4', '步骤5'] 

for i, (x, y, text, fc, ec) in enumerate(main_steps_dec): 
  ax.text(x, y + 1.3, step_labels_dec[i], ha='center', va='center', fontsize=11, fontweight='bold', color=ec, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=ec, linewidth=1.5)) 
  ax.set_title('解密流程图', fontsize=18, fontweight='bold', y=0.98, pad=15) 
    
plt.tight_layout() 
plt.savefig('../paper_images/decryption_flow.png', dpi=150, bbox_inches='tight', facecolor='white') 
plt.close() 
print("解密流程图生成完成") 