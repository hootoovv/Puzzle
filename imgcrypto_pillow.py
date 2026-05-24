#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于视觉扰乱与数字序列驱动的图片加密解密工具 (Pillow版本)

用法:
  加密: python imgcrypto_pillow.py encrypt -i input.jpg -o encrypted.png -bw 8 -bh 8 -es 1 -eo 2 -os 1 -oo 3 -sq pi
  解密: python imgcrypto_pillow.py decrypt -i encrypted.png -o decrypted.jpg
"""

import os
import sys
import math
import argparse

try:
    from PIL import Image
except ImportError:
    print("错误: 需要安装Pillow: pip install Pillow")
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
    """根据序列键获取十进制数字序列"""
    needed = max(math.ceil(count * 1.5), 1000)
    
    if key == 'pi':
        return _get_const_digits('pi', needed)
    elif key == 'e':
        return _get_const_digits('e', needed)
    elif key == 'phi':
        return _get_const_digits('phi', needed)
    else:
        return [int(c) for c in key if c.isdigit()]


# ============================================================
# 遍历顺序生成函数
# ============================================================

def _spiral_cw_standard(rows, cols):
    """标准顺时针螺旋遍历（从左上角开始）"""
    result = []
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            result.append((top, c))
        top += 1
        for r in range(top, bottom + 1):
            result.append((r, right))
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                result.append((bottom, c))
            bottom -= 1
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
        for c in range(right, left - 1, -1):
            result.append((top, c))
        top += 1
        for r in range(top, bottom + 1):
            result.append((r, left))
        left += 1
        if top <= bottom:
            for c in range(left, right + 1):
                result.append((bottom, c))
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                result.append((r, right))
            right -= 1
    return result


def _transform_cells(cells, rows, cols, start):
    """根据起点位置变换遍历序列"""
    if start == 1:
        return cells
    elif start == 2:
        return [(r, cols - 1 - c) for r, c in cells]
    elif start == 3:
        return [(rows - 1 - r, cols - 1 - c) for r, c in cells]
    elif start == 4:
        return [(rows - 1 - r, c) for r, c in cells]
    return cells


def _row_forward_standard(rows, cols):
    result = []
    for r in range(rows):
        for c in range(cols):
            result.append((r, c))
    return result


def _col_forward_standard(rows, cols):
    result = []
    for c in range(cols):
        for r in range(rows):
            result.append((r, c))
    return result


def _row_zigzag_standard(rows, cols):
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
    """
    if order == 1:
        cells = _spiral_cw_standard(rows, cols)
        return _transform_cells(cells, rows, cols, start)
    elif order == 2:
        cells = _spiral_ccw_standard(rows, cols)
        return _transform_cells(cells, rows, cols, start)
    elif order == 3:
        if start == 1:
            return _row_forward_standard(rows, cols)
        elif start == 2:
            cells = []
            for c in range(cols - 1, -1, -1):
                for r in range(rows):
                    cells.append((r, c))
            return cells
        elif start == 3:
            cells = []
            for r in range(rows - 1, -1, -1):
                for c in range(cols - 1, -1, -1):
                    cells.append((r, c))
            return cells
        elif start == 4:
            cells = []
            for c in range(cols):
                for r in range(rows - 1, -1, -1):
                    cells.append((r, c))
            return cells
    elif order == 4:
        if start == 1:
            return _col_forward_standard(rows, cols)
        elif start == 4:
            cells = []
            for r in range(rows - 1, -1, -1):
                for c in range(cols):
                    cells.append((r, c))
            return cells
        elif start == 3:
            cells = []
            for c in range(cols - 1, -1, -1):
                for r in range(rows - 1, -1, -1):
                    cells.append((r, c))
            return cells
        elif start == 2:
            cells = []
            for r in range(rows):
                for c in range(cols - 1, -1, -1):
                    cells.append((r, c))
            return cells
    elif order == 5:
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
    加密图片（Pillow版本）
    """
    # 1. 读取原始图片
    img = Image.open(input_path)
    
    # 统一转为RGB模式（保留alpha通道时用RGBA）
    if img.mode == 'RGBA':
        pass  # 保持RGBA
    elif img.mode == 'P':
        img = img.convert('RGBA')
    elif img.mode == 'L':
        img = img.convert('RGB')
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    orig_w, orig_h = img.size
    
    # 获取原始图片格式
    SUPPORTED_FORMATS = {'bmp', 'png', 'jpg', 'jpeg', 'webp'}
    orig_format = os.path.splitext(input_path)[1].lstrip('.').lower()
    if not orig_format or orig_format not in SUPPORTED_FORMATS:
        orig_format = (img.format or 'jpg').lower()
    # 统一格式名
    if orig_format in ('jpeg',):
        orig_format = 'jpg'
    if orig_format not in SUPPORTED_FORMATS:
        print(f"警告: 不支持的图片格式 '{orig_format}'，将使用jpg格式保存")
        orig_format = 'jpg'
    
    # 2. Padding处理
    pad_w = (block_w - orig_w % block_w) % block_w
    pad_h = (block_h - orig_h % block_h) % block_h
    
    if pad_w > 0 or pad_h > 0:
        # 创建新画布并粘贴原图
        padded_w = orig_w + pad_w
        padded_h = orig_h + pad_h
        img_padded = Image.new(img.mode, (padded_w, padded_h), (0, 0, 0) if img.mode == 'RGB' else (0, 0, 0, 255))
        img_padded.paste(img, (0, 0))
        
        # 使用相邻像素颜色填充padding区域（而非纯黑色），增加破解难度
        # 右侧padding：复制每行最右侧像素的颜色值填充该行padding像素
        if pad_w > 0:
            right_col = img.crop((orig_w - 1, 0, orig_w, orig_h))
            right_pad = right_col.resize((pad_w, orig_h), Image.NEAREST)
            img_padded.paste(right_pad, (orig_w, 0))
        
        # 底部padding：复制每列最下部像素的颜色值填充该列padding像素（包含已填充的右侧区域）
        if pad_h > 0:
            bottom_row = img_padded.crop((0, orig_h - 1, padded_w, orig_h))
            bottom_pad = bottom_row.resize((padded_w, pad_h), Image.NEAREST)
            img_padded.paste(bottom_pad, (0, orig_h))
    else:
        img_padded = img.copy()
    
    padded_w, padded_h = img_padded.size
    m = padded_h // block_h  # 行数
    n = padded_w // block_w  # 列数
    
    print(f"原始图片: {orig_w}x{orig_h}, 填充后: {padded_w}x{padded_h}")
    print(f"块大小: {block_w}x{block_h}, 网格: {m}x{n} = {m*n}块")
    print(f"Padding: 水平{pad_w}像素, 垂直{pad_h}像素")
    
    # 3. 分块提取
    extract_cells = get_traversal_order(m, n, extract_start, extract_order)
    
    array_a = []
    for r, c in extract_cells:
        x1 = c * block_w
        y1 = r * block_h
        x2 = x1 + block_w
        y2 = y1 + block_h
        block = img_padded.crop((x1, y1, x2, y2))
        array_a.append(block.copy())
    
    # 4. 数字序列驱动填充
    digits = get_digit_sequence(sequence_key, m * n)
    output_cells = get_traversal_order(m, n, output_start, output_order)
    total = m * n
    
    grid_b = [[None for _ in range(n)] for _ in range(m)]
    
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
    encrypted_img = Image.new(img.mode, (padded_w, padded_h), (0, 0, 0) if img.mode == 'RGB' else (0, 0, 0, 255))
    for r in range(m):
        for c in range(n):
            x1 = c * block_w
            y1 = r * block_h
            encrypted_img.paste(grid_b[r][c], (x1, y1))
    
    # 6. 保存加密图片（PNG格式，含EXIF解密参数）
    param_str = f"{pad_w}x{pad_h}_{block_w}x{block_h}_{extract_start}{extract_order}_{output_start}{output_order}.{orig_format}.{sequence_key}"
    
    # PNG使用PngInfo存储元数据（tEXt块，key为Parameters）
    from PIL import PngImagePlugin
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text('Parameters', param_str)
    
    encrypted_img.save(output_path, 'PNG', pnginfo=pnginfo)
    
    print(f"加密完成，解密参数: {param_str}")
    print(f"加密图片已保存到: {output_path}")


# ============================================================
# 辅助函数
# ============================================================

def _fix_output_ext(output_path, orig_format):
    """
    修正输出文件名的扩展名，使其与原图格式一致。
    如果输出路径包含扩展名，则替换为原图格式的扩展名；
    如果不包含扩展名，则添加原图格式的扩展名。
    """
    base, ext = os.path.splitext(output_path)
    if ext:
        # 有扩展名，替换为原图格式的扩展名
        return base + '.' + orig_format
    else:
        # 无扩展名，添加原图格式的扩展名
        return output_path + '.' + orig_format


# ============================================================
# 解密函数
# ============================================================

def decrypt_image(input_path, output_path):
    """
    解密图片（Pillow版本）
    """
    # 1. 从EXIF或PNG元数据中读取解密参数
    img_for_meta = Image.open(input_path)
    param_str = None
    
    # 首先尝试从PNG tEXt块读取（Parameters键）
    if 'Parameters' in img_for_meta.info:
        param_str = img_for_meta.info['Parameters']
    elif 'parameters' in img_for_meta.info:
        param_str = img_for_meta.info['parameters']
    # 兼容旧版本的UserComment键
    elif 'UserComment' in img_for_meta.info:
        param_str = img_for_meta.info['UserComment']
    # 尝试从EXIF读取（仅JPEG或旧版PNG）
    elif HAS_PIEXIF and 'exif' in img_for_meta.info:
        try:
            exif_dict = piexif.load(img_for_meta.info['exif'])
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
    
    try:
        parts = param_str.split('_')
        pad_dims = parts[0]
        block_dims = parts[1]
        extract_params = parts[2]
        rest = parts[3]
        
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
    img = Image.open(input_path)
    if img.mode != 'RGB' and img.mode != 'RGBA':
        img = img.convert('RGB')
    
    padded_w, padded_h = img.size
    m = padded_h // block_h
    n = padded_w // block_w
    total = m * n
    
    # 3. 从加密图片中提取子图块
    grid_b = [[None for _ in range(n)] for _ in range(m)]
    for r in range(m):
        for c in range(n):
            x1 = c * block_w
            y1 = r * block_h
            x2 = x1 + block_w
            y2 = y1 + block_h
            grid_b[r][c] = img.crop((x1, y1, x2, y2))
    
    # 4. 逆向恢复数组A
    digits = get_digit_sequence(sequence_key, total)
    output_cells = get_traversal_order(m, n, output_start, output_order)
    
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
    
    # 5. 逆提取：将array_a按提取顺序恢复到原始位置
    extract_cells = get_traversal_order(m, n, extract_start, extract_order)
    
    decrypted_padded = Image.new(img.mode, (padded_w, padded_h), (0, 0, 0) if img.mode == 'RGB' else (0, 0, 0, 255))
    for i, (r, c) in enumerate(extract_cells):
        x1 = c * block_w
        y1 = r * block_h
        decrypted_padded.paste(array_a[i], (x1, y1))
    
    # 6. 去除Padding
    orig_w = padded_w - pad_w
    orig_h = padded_h - pad_h
    decrypted_img = decrypted_padded.crop((0, 0, orig_w, orig_h))
    
    # 7. 保存解密图片
    # 根据原始格式修正输出文件名扩展名，并选择保存方式
    output_path = _fix_output_ext(output_path, orig_format)
    save_format = orig_format.upper()
    if save_format == 'JPG':
        save_format = 'JPEG'
    
    if save_format == 'JPEG':
        # JPEG不支持RGBA，需要转换
        if decrypted_img.mode == 'RGBA':
            decrypted_img = decrypted_img.convert('RGB')
        decrypted_img.save(output_path, 'JPEG', quality=95)
    elif save_format == 'WEBP':
        if decrypted_img.mode == 'RGBA':
            pass  # WebP支持RGBA
        decrypted_img.save(output_path, 'WEBP', quality=95)
    else:
        decrypted_img.save(output_path, save_format)
    
    print(f"解密完成，图片已保存到: {output_path}")
    print(f"原始尺寸: {orig_w}x{orig_h}")


# ============================================================
# 命令行接口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='基于视觉扰乱与数字序列驱动的图片加密解密工具 (Pillow版本)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  加密: python imgcrypto_pillow.py encrypt -i photo.jpg -o encrypted.png -bw 8 -bh 8 -es 1 -eo 2 -os 1 -oo 3 -sq pi
  解密: python imgcrypto_pillow.py decrypt -i encrypted.png -o decrypted.jpg

起点编号: 1=左上角, 2=右上角, 3=右下角, 4=左下角
顺序编号: 1=顺时针螺旋, 2=逆时针螺旋, 3=逐行前进, 4=逐列前进, 5=逐行迂回, 6=逐列迂回
数字序列: pi, e, phi 或自定义数字字符串(如 31415926535)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
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
