#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于视觉扰乱与数字序列驱动的图片加密解密工具 (OpenCV版本)

用法:
  加密: python imgcrypto_opencv.py encrypt -i input.jpg -o encrypted.png -bw 8 -bh 8 -es 1 -eo 2 -os 1 -oo 3 -sq pi
  解密: python imgcrypto_opencv.py decrypt -i encrypted.png -o decrypted.jpg
"""

import os
import sys
import math
import argparse
import numpy as np

try:
    import cv2
except ImportError:
    print("错误: 需要安装opencv-python: pip install opencv-python")
    sys.exit(1)

try:
    import mpmath
except ImportError:
    print("错误: 需要安装mpmath: pip install mpmath")
    sys.exit(1)

# piexif仅用于JPEG格式（可选）
try:
    import piexif
    HAS_PIEXIF = True
except ImportError:
    HAS_PIEXIF = False


# ============================================================
# 数学常数数字序列生成
# ============================================================

# 常数缓存，避免重复计算
_const_cache = {}

def _get_const_digits(const_name, count):
    """使用mpmath动态计算数学常数的十进制数字序列"""
    if const_name in _const_cache and len(_const_cache[const_name]) >= count:
        return _const_cache[const_name][:count]
    
    # 计算多一点余量
    mpmath.mp.dps = count + 10
    
    if const_name == 'pi':
        s = str(mpmath.mp.pi)
    elif const_name == 'e':
        s = str(mpmath.mp.e)
    elif const_name == 'phi':
        s = str((1 + mpmath.sqrt(5)) / 2)
    else:
        raise ValueError(f"未知常数: {const_name}")
    
    # 去掉整数部分和小数点，只取小数部分
    if '.' in s:
        digits_str = s.replace('.', '')[1:]  # 去掉 '3.' / '2.' / '1.'
    else:
        digits_str = s
    
    digits = [int(c) for c in digits_str[:count]]
    _const_cache[const_name] = digits
    return digits


def get_digit_sequence(key, count):
    """
    根据序列键获取十进制数字序列
    key: 'pi', 'e', 'phi' 或自定义数字字符串
    count: 需要的非零数字数量（实际生成数量会更多以补偿0的跳过）
    """
    needed = max(math.ceil(count * 1.5), 1000)
    
    if key == 'pi':
        return _get_const_digits('pi', needed)
    elif key == 'e':
        return _get_const_digits('e', needed)
    elif key == 'phi':
        return _get_const_digits('phi', needed)
    else:
        # 自定义数字序列
        return [int(c) for c in key if c.isdigit()]


# ============================================================
# 遍历顺序生成函数
# ============================================================

def _spiral_cw_standard(rows, cols):
    """标准顺时针螺旋遍历（从左上角开始）"""
    result = []
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    while top <= bottom and left <= right:
        # 上边：从左到右
        for c in range(left, right + 1):
            result.append((top, c))
        top += 1
        # 右边：从上到下
        for r in range(top, bottom + 1):
            result.append((r, right))
        right -= 1
        # 下边：从右到左
        if top <= bottom:
            for c in range(right, left - 1, -1):
                result.append((bottom, c))
            bottom -= 1
        # 左边：从下到上
        if left <= right:
            for r in range(bottom, top - 1, -1):
                result.append((r, left))
            left += 1
    return result


def _spiral_ccw_standard(rows, cols):
    """标准逆时针螺旋遍历（从左上角开始）"""
    result = []
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    while top <= bottom and left <= right:
        # 上边：从右到左
        for c in range(right, left - 1, -1):
            result.append((top, c))
        top += 1
        # 左边：从上到下
        for r in range(top, bottom + 1):
            result.append((r, left))
        left += 1
        # 下边：从左到右
        if top <= bottom:
            for c in range(left, right + 1):
                result.append((bottom, c))
            bottom -= 1
        # 右边：从下到上
        if left <= right:
            for r in range(bottom, top - 1, -1):
                result.append((r, right))
            right -= 1
    return result


def _transform_cells(cells, rows, cols, start):
    """根据起点位置变换遍历序列"""
    if start == 1:  # 左上角
        return cells
    elif start == 2:  # 右上角
        return [(r, cols - 1 - c) for r, c in cells]
    elif start == 3:  # 右下角
        return [(rows - 1 - r, cols - 1 - c) for r, c in cells]
    elif start == 4:  # 左下角
        return [(rows - 1 - r, c) for r, c in cells]
    return cells


def _row_forward_standard(rows, cols):
    """标准逐行前进遍历"""
    result = []
    for r in range(rows):
        for c in range(cols):
            result.append((r, c))
    return result


def _col_forward_standard(rows, cols):
    """标准逐列前进遍历"""
    result = []
    for c in range(cols):
        for r in range(rows):
            result.append((r, c))
    return result


def _row_zigzag_standard(rows, cols):
    """标准逐行迂回遍历"""
    result = []
    for r in range(rows):
        if r % 2 == 0:
            for c in range(cols):
                result.append((r, c))
        else:
            for c in range(cols - 1, -1, -1):
                result.append((r, c))
    return result


def _col_zigzag_standard(rows, cols):
    """标准逐列迂回遍历"""
    result = []
    for c in range(cols):
        if c % 2 == 0:
            for r in range(rows):
                result.append((r, c))
        else:
            for r in range(rows - 1, -1, -1):
                result.append((r, c))
    return result


def get_traversal_order(rows, cols, start, order):
    """
    获取遍历顺序
    start: 1=左上角, 2=右上角, 3=右下角, 4=左下角
    order: 1=顺时针螺旋, 2=逆时针螺旋, 3=逐行前进, 4=逐列前进, 5=逐行迂回, 6=逐列迂回
    返回: [(row, col), ...] 遍历坐标列表
    """
    if order == 1:
        cells = _spiral_cw_standard(rows, cols)
        return _transform_cells(cells, rows, cols, start)
    elif order == 2:
        cells = _spiral_ccw_standard(rows, cols)
        return _transform_cells(cells, rows, cols, start)
    elif order == 3:
        # 逐行前进：TR=逆时针旋转90°, BR=逆时针旋转180°, BL=逆时针旋转270°
        # 等效于将标准逐行前进按起点变换
        if start == 1:
            return _row_forward_standard(rows, cols)
        elif start == 2:  # 逆时针旋转90°
            cells = []
            for c in range(cols - 1, -1, -1):
                for r in range(rows):
                    cells.append((r, c))
            return cells
        elif start == 3:  # 逆时针旋转180°
            cells = []
            for r in range(rows - 1, -1, -1):
                for c in range(cols - 1, -1, -1):
                    cells.append((r, c))
            return cells
        elif start == 4:  # 逆时针旋转270°
            cells = []
            for c in range(cols):
                for r in range(rows - 1, -1, -1):
                    cells.append((r, c))
            return cells
    elif order == 4:
        # 逐列前进：BL=顺时针旋转90°, BR=顺时针旋转180°, TR=顺时针旋转270°
        if start == 1:
            return _col_forward_standard(rows, cols)
        elif start == 4:  # 顺时针旋转90°
            cells = []
            for r in range(rows - 1, -1, -1):
                for c in range(cols):
                    cells.append((r, c))
            return cells
        elif start == 3:  # 顺时针旋转180°
            cells = []
            for c in range(cols - 1, -1, -1):
                for r in range(rows - 1, -1, -1):
                    cells.append((r, c))
            return cells
        elif start == 2:  # 顺时针旋转270°
            cells = []
            for r in range(rows):
                for c in range(cols - 1, -1, -1):
                    cells.append((r, c))
            return cells
    elif order == 5:
        # 逐行迂回：TR=逆时针旋转90°, BR=逆时针旋转180°, BL=逆时针旋转270°
        if start == 1:
            return _row_zigzag_standard(rows, cols)
        elif start == 2:
            cells = []
            for c in range(cols - 1, -1, -1):
                if (cols - 1 - c) % 2 == 0:
                    for r in range(rows):
                        cells.append((r, c))
                else:
                    for r in range(rows - 1, -1, -1):
                        cells.append((r, c))
            return cells
        elif start == 3:
            cells = []
            for r in range(rows - 1, -1, -1):
                if (rows - 1 - r) % 2 == 0:
                    for c in range(cols - 1, -1, -1):
                        cells.append((r, c))
                else:
                    for c in range(cols):
                        cells.append((r, c))
            return cells
        elif start == 4:
            cells = []
            for r in range(rows - 1, -1, -1):
                if (rows - 1 - r) % 2 == 0:
                    for c in range(cols):
                        cells.append((r, c))
                else:
                    for c in range(cols - 1, -1, -1):
                        cells.append((r, c))
            return cells
    elif order == 6:
        # 逐列迂回：BL=顺时针旋转90°, BR=顺时针旋转180°, TR=顺时针旋转270°
        if start == 1:
            return _col_zigzag_standard(rows, cols)
        elif start == 4:
            cells = []
            for r in range(rows - 1, -1, -1):
                if (rows - 1 - r) % 2 == 0:
                    for c in range(cols):
                        cells.append((r, c))
                else:
                    for c in range(cols - 1, -1, -1):
                        cells.append((r, c))
            return cells
        elif start == 3:
            cells = []
            for c in range(cols - 1, -1, -1):
                if (cols - 1 - c) % 2 == 0:
                    for r in range(rows - 1, -1, -1):
                        cells.append((r, c))
                else:
                    for r in range(rows):
                        cells.append((r, c))
            return cells
        elif start == 2:
            cells = []
            for r in range(rows):
                if r % 2 == 0:
                    for c in range(cols - 1, -1, -1):
                        cells.append((r, c))
                else:
                    for c in range(cols):
                        cells.append((r, c))
            return cells
    
    raise ValueError(f"无效的起点({start})或顺序({order})参数")


# ============================================================
# 加密函数
# ============================================================

def encrypt_image(input_path, block_w, block_h, extract_start, extract_order,
                  output_start, output_order, sequence_key, output_path):
    """
    加密图片
    
    参数:
        input_path: 原始图片路径
        block_w: 块宽度(a)
        block_h: 块高度(b)
        extract_start: 提取起点(1-4)
        extract_order: 提取顺序(1-6)
        output_start: 输出起点(1-4)
        output_order: 输出顺序(1-6)
        sequence_key: 数字序列键('pi', 'e', 'phi' 或自定义数字字符串)
        output_path: 输出加密图片路径
    """
    # 1. 读取原始图片
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"无法读取图片: {input_path}")
    
    # 处理RGBA转为RGB
    if len(img.shape) == 3 and img.shape[2] == 4:
        # 保留alpha通道
        pass
    elif len(img.shape) == 2:
        # 灰度图转为3通道
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    orig_h, orig_w = img.shape[:2]
    
    # 获取原始图片格式
    orig_format = os.path.splitext(input_path)[1].lstrip('.')
    if not orig_format:
        orig_format = 'jpg'
    
    # 2. Padding处理
    pad_w = (block_w - orig_w % block_w) % block_w
    pad_h = (block_h - orig_h % block_h) % block_h
    
    if pad_w > 0 or pad_h > 0:
        # 使用相邻像素颜色填充padding区域（BORDER_REPLICATE复制边缘像素），增加破解难度
        # 右侧padding：复制每行最右侧像素的颜色值填充该行padding像素
        # 底部padding：复制每列最下部像素的颜色值填充该列padding像素
        # OpenCV的copyMakeBorder: top, bottom, left, right
        img_padded = cv2.copyMakeBorder(img, 0, pad_h, 0, pad_w,
                                         cv2.BORDER_REPLICATE)
    else:
        img_padded = img.copy()
    
    padded_h, padded_w = img_padded.shape[:2]
    m = padded_h // block_h  # 行数
    n = padded_w // block_w  # 列数
    
    print(f"原始图片: {orig_w}x{orig_h}, 填充后: {padded_w}x{padded_h}")
    print(f"块大小: {block_w}x{block_h}, 网格: {m}x{n} = {m*n}块")
    print(f"Padding: 水平{pad_w}像素, 垂直{pad_h}像素")
    
    # 3. 分块提取
    extract_cells = get_traversal_order(m, n, extract_start, extract_order)
    
    # 从图片中提取子图块，按遍历顺序组成1D数组A
    array_a = []
    for r, c in extract_cells:
        y1 = r * block_h
        y2 = y1 + block_h
        x1 = c * block_w
        x2 = x1 + block_w
        block = img_padded[y1:y2, x1:x2].copy()
        array_a.append(block)
    
    # 4. 数字序列驱动填充
    digits = get_digit_sequence(sequence_key, m * n)
    
    # 获取输出遍历序列
    output_cells = get_traversal_order(m, n, output_start, output_order)
    total = m * n
    
    # 创建空白二维数组B（用None表示空位）
    grid_b = [[None for _ in range(n)] for _ in range(m)]
    
    # 填充过程
    pos_idx = 0  # 当前在output_cells中的索引
    digit_idx = 0
    
    for input_idx in range(total):
        placed = False
        while not placed and digit_idx < len(digits):
            d = digits[digit_idx]
            digit_idx += 1
            
            if d == 0:
                continue  # 跳过0
            
            # 前进d步
            for _ in range(d):
                pos_idx += 1
                if pos_idx >= total:
                    pos_idx = 0
            
            # 查找第一个空白位置
            attempts = 0
            while grid_b[output_cells[pos_idx][0]][output_cells[pos_idx][1]] is not None:
                pos_idx += 1
                if pos_idx >= total:
                    pos_idx = 0
                attempts += 1
                if attempts > total * 2:
                    raise RuntimeError("填充过程出错：无法找到空白位置")
            
            r, c = output_cells[pos_idx]
            grid_b[r][c] = array_a[input_idx]
            placed = True
        
        if not placed:
            raise RuntimeError("数字序列不足，无法完成填充")
    
    # 5. 将数组B拼接为加密图片
    encrypted_img = np.zeros_like(img_padded)
    for r in range(m):
        for c in range(n):
            y1 = r * block_h
            y2 = y1 + block_h
            x1 = c * block_w
            x2 = x1 + block_w
            encrypted_img[y1:y2, x1:x2] = grid_b[r][c]
    
    # 6. 保存加密图片（PNG格式，含解密参数）
    param_str = f"{pad_w}x{pad_h}_{block_w}x{block_h}_{extract_start}{extract_order}_{output_start}{output_order}.{orig_format}.{sequence_key}"
    
    # PNG不支持直接用piexif写入EXIF，使用Pillow的PngInfo写入元数据
    from PIL import Image as PILImage, PngImagePlugin
    
    # 将OpenCV图片(BGR)转为PIL图片(RGB)再保存PNG
    if len(encrypted_img.shape) == 3 and encrypted_img.shape[2] == 4:
        encrypted_rgb = cv2.cvtColor(encrypted_img, cv2.COLOR_BGRA2RGBA)
    elif len(encrypted_img.shape) == 3:
        encrypted_rgb = cv2.cvtColor(encrypted_img, cv2.COLOR_BGR2RGB)
    else:
        encrypted_rgb = encrypted_img
    
    pil_img = PILImage.fromarray(encrypted_rgb)
    
    # 使用PngInfo存储解密参数（tEXt块，key为Parameters）
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text('Parameters', param_str)
    
    pil_img.save(output_path, 'PNG', pnginfo=pnginfo)
    
    print(f"加密完成，解密参数: {param_str}")
    print(f"加密图片已保存到: {output_path}")


# ============================================================
# 解密函数
# ============================================================

def decrypt_image(input_path, output_path):
    """
    解密图片
    
    参数:
        input_path: 加密PNG图片路径
        output_path: 输出解密图片路径
    """
    # 1. 从EXIF或PNG元数据中读取解密参数
    from PIL import Image as PILImage
    
    pil_meta = PILImage.open(input_path)
    param_str = None
    
    # 首先尝试从PNG tEXt块读取（Parameters键）
    if 'Parameters' in pil_meta.info:
        param_str = pil_meta.info['Parameters']
    elif 'parameters' in pil_meta.info:
        param_str = pil_meta.info['parameters']
    # 兼容旧版本的UserComment键
    elif 'UserComment' in pil_meta.info:
        param_str = pil_meta.info['UserComment']
    # 尝试从EXIF读取（仅JPEG或旧版PNG）
    elif HAS_PIEXIF and 'exif' in pil_meta.info:
        try:
            exif_dict = piexif.load(pil_meta.info['exif'])
            user_comment_bytes = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment, None)
            if user_comment_bytes is not None:
                if isinstance(user_comment_bytes, bytes):
                    if user_comment_bytes[:8] == b'ASCII\x00\x00\x00':
                        param_str = user_comment_bytes[8:].decode('ascii')
                    else:
                        param_str = user_comment_bytes.decode('ascii', errors='ignore')
        except Exception:
            pass
    
    if param_str is None:
        raise RuntimeError("加密图片中未找到解密参数（PNG tEXt块中无Parameters字段）")
    
    print(f"解密参数: {param_str}")
    
    # 解析参数字符串: <padW>x<padH>_<blockW>x<blockH>_<extractStart><extractOrder>_<outputStart><outputOrder>.<origFormat>.<sequenceKey>
    try:
        parts = param_str.split('_')
        pad_dims = parts[0]  # padWxpadH
        block_dims = parts[1]  # blockWxblockH
        extract_params = parts[2]  # extractStart+extractOrder
        rest = parts[3]  # outputStart+outputOrder.origFormat.sequenceKey
        
        pad_w, pad_h = map(int, pad_dims.split('x'))
        block_w, block_h = map(int, block_dims.split('x'))
        extract_start = int(extract_params[0])
        extract_order = int(extract_params[1])
        
        rest_parts = rest.split('.')
        output_start = int(rest_parts[0][0])
        output_order = int(rest_parts[0][1])
        orig_format = rest_parts[1]
        sequence_key = rest_parts[2]
    except (IndexError, ValueError) as e:
        raise RuntimeError(f"解密参数格式错误: {param_str}, 错误: {e}")
    
    print(f"块大小: {block_w}x{block_h}, 提取: 起点{extract_start}顺序{extract_order}, "
          f"输出: 起点{output_start}顺序{output_order}")
    print(f"Padding: 水平{pad_w}像素, 垂直{pad_h}像素, 原始格式: {orig_format}")
    
    # 2. 读取加密图片
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"无法读取图片: {input_path}")
    
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    padded_h, padded_w = img.shape[:2]
    m = padded_h // block_h
    n = padded_w // block_w
    total = m * n
    
    # 3. 从加密图片中提取子图块（按网格位置）
    # grid_b[r][c] = 子图块
    grid_b = [[None for _ in range(n)] for _ in range(m)]
    for r in range(m):
        for c in range(n):
            y1 = r * block_h
            y2 = y1 + block_h
            x1 = c * block_w
            x2 = x1 + block_w
            grid_b[r][c] = img[y1:y2, x1:x2].copy()
    
    # 4. 逆向恢复数组A
    # 重新模拟加密填充过程，记录每个位置放入的是第几个子图片
    digits = get_digit_sequence(sequence_key, total)
    output_cells = get_traversal_order(m, n, output_start, output_order)
    
    # 记录放置顺序：placement[i] = (r, c) 表示第i个子图片放在grid_b的位置
    placement = [None] * total
    
    filled = [[False for _ in range(n)] for _ in range(m)]
    pos_idx = 0
    digit_idx = 0
    
    for input_idx in range(total):
        placed = False
        while not placed and digit_idx < len(digits):
            d = digits[digit_idx]
            digit_idx += 1
            
            if d == 0:
                continue
            
            for _ in range(d):
                pos_idx += 1
                if pos_idx >= total:
                    pos_idx = 0
            
            attempts = 0
            while filled[output_cells[pos_idx][0]][output_cells[pos_idx][1]]:
                pos_idx += 1
                if pos_idx >= total:
                    pos_idx = 0
                attempts += 1
                if attempts > total * 2:
                    raise RuntimeError("解密过程出错：无法找到已填充位置")
            
            r, c = output_cells[pos_idx]
            placement[input_idx] = (r, c)
            filled[r][c] = True
            placed = True
        
        if not placed:
            raise RuntimeError("数字序列不足，无法完成逆向恢复")
    
    # 从grid_b中按placement顺序提取，恢复array_a
    array_a = []
    for i in range(total):
        r, c = placement[i]
        array_a.append(grid_b[r][c])
    
    # 5. 逆提取：将array_a按提取顺序的逆映射恢复到原始位置
    extract_cells = get_traversal_order(m, n, extract_start, extract_order)
    
    # array_a[i] 对应 extract_cells[i] 位置的子图块
    decrypted_padded = np.zeros_like(img)
    for i, (r, c) in enumerate(extract_cells):
        y1 = r * block_h
        y2 = y1 + block_h
        x1 = c * block_w
        x2 = x1 + block_w
        decrypted_padded[y1:y2, x1:x2] = array_a[i]
    
    # 6. 去除Padding
    orig_h = padded_h - pad_h
    orig_w = padded_w - pad_w
    decrypted_img = decrypted_padded[:orig_h, :orig_w]
    
    # 7. 保存解密图片
    cv2.imwrite(output_path, decrypted_img)
    print(f"解密完成，图片已保存到: {output_path}")
    print(f"原始尺寸: {orig_w}x{orig_h}")


# ============================================================
# 命令行接口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='基于视觉扰乱与数字序列驱动的图片加密解密工具 (OpenCV版本)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  加密: python imgcrypto_opencv.py encrypt -i photo.jpg -o encrypted.png -bw 8 -bh 8 -es 1 -eo 2 -os 1 -oo 3 -sq pi
  解密: python imgcrypto_opencv.py decrypt -i encrypted.png -o decrypted.jpg

起点编号: 1=左上角, 2=右上角, 3=右下角, 4=左下角
顺序编号: 1=顺时针螺旋, 2=逆时针螺旋, 3=逐行前进, 4=逐列前进, 5=逐行迂回, 6=逐列迂回
数字序列: pi, e, phi 或自定义数字字符串(如 31415926535)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 加密子命令
    enc_parser = subparsers.add_parser('encrypt', help='加密图片')
    enc_parser.add_argument('-i', '--input', required=True, help='输入图片路径')
    enc_parser.add_argument('-o', '--output', required=True, help='输出加密图片路径')
    enc_parser.add_argument('-bw', '--block-width', type=int, default=8, help='块宽度(默认8)')
    enc_parser.add_argument('-bh', '--block-height', type=int, default=8, help='块高度(默认8)')
    enc_parser.add_argument('-es', '--extract-start', type=int, default=1, choices=[1,2,3,4], help='提取起点(默认1)')
    enc_parser.add_argument('-eo', '--extract-order', type=int, default=1, choices=[1,2,3,4,5,6], help='提取顺序(默认1)')
    enc_parser.add_argument('-os', '--output-start', type=int, default=1, choices=[1,2,3,4], help='输出起点(默认1)')
    enc_parser.add_argument('-oo', '--output-order', type=int, default=3, choices=[1,2,3,4,5,6], help='输出顺序(默认3)')
    enc_parser.add_argument('-sq', '--sequence', default='pi', help='数字序列键(默认pi)')
    
    # 解密子命令
    dec_parser = subparsers.add_parser('decrypt', help='解密图片')
    dec_parser.add_argument('-i', '--input', required=True, help='输入加密图片路径')
    dec_parser.add_argument('-o', '--output', required=True, help='输出解密图片路径')
    
    args = parser.parse_args()
    
    if args.command == 'encrypt':
        encrypt_image(
            args.input, args.block_width, args.block_height,
            args.extract_start, args.extract_order,
            args.output_start, args.output_order,
            args.sequence, args.output
        )
    elif args.command == 'decrypt':
        decrypt_image(args.input, args.output)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
