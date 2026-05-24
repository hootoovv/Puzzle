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
    import piexif
except ImportError:
    print("错误: 需要安装piexif: pip install piexif")
    sys.exit(1)


# ============================================================
# 数学常数数字序列生成
# ============================================================

def get_pi_digits(count):
    """生成圆周率π的十进制数字序列"""
    _pi_str = (
        "31415926535897932384626433832795028841971693993751"
        "05820974944592307816406286208998628034825342117067"
        "98214808651328230664709384460955058223172535940812"
        "84811174502841027019385211055596446229489549303819"
        "64428810975665933446128475648233786783165271201909"
        "14564856692346034861045432664821339360726024914127"
        "37245870066063155881748815209209628292540917153643"
        "67892590360011330530548820466521384146951941511609"
        "43305727036575959195309218611738193261179310511854"
        "80744623799627495673518857527248912279381830119491"
        "29833673362440656643086021394946395224737190702179"
        "86094370277053921717629317675238467481846766940513"
        "20005681271452635608277857713427577896091736371787"
        "21468440901224953430146549585371050792279689258923"
        "54201995611212902196086403441815981362977477130996"
        "05187072113499999983729780499510597317328160963185"
        "95024459455346908302642522308253344685035261931188"
        "17101000313783875288658753320838142061717766914730"
        "35982534904287554687311595628638823537875937519577"
        "81857780532171226806613001927876611195909216420199"
    )
    digits = [int(c) for c in _pi_str[:count]]
    if len(digits) < count:
        digits.extend([int(c) for c in str(math.pi)[2:2 + count - len(digits)]])
    return digits[:count]


def get_e_digits(count):
    """生成自然常数e的十进制数字序列"""
    _e_str = (
        "27182818284590452353602874713526624977572470936999"
        "59574966967627724076630353547594571382178525166427"
        "42746639193200305992181741359662904357290033429526"
        "05956307381323286279434907632338298807531952510190"
        "11573834187930702154089149934884167509244761460668"
        "08226480016847741185374234544243710753907774499206"
        "95517027618386062613313845830007520449338265602976"
        "06737113200709328709144255358269157639937530207204"
        "07432135940875632512342961329618944624572474385618"
        "80445769630679270072276405467759647093872530906336"
        "60853271144849344369706395264456867626974554982280"
        "67825282664387829540464154361058037561640134771063"
        "84590947807934644094798998894859901944062711346569"
        "67103207225738379301928384381807150601557993690547"
        "44981992122393218917643549125866533816842673636836"
        "73359554973686851407215420885251681391627212854090"
        "06875057884530968391682084321466026654482871053316"
        "52979347446722657704997049678454675684526839947517"
        "47554124083244095206777075656545283494309394126758"
        "69846961269766125536814587019434803603347871781790"
    )
    digits = [int(c) for c in _e_str[:count]]
    return digits[:count]


def get_phi_digits(count):
    """生成黄金比例φ的十进制数字序列"""
    _phi_str = (
        "16180339887498948482045868343656381177203091798057"
        "62862135448622705260462818902449707207204189391137"
        "48475408807538689175212663386222353693179318006076"
        "67263544333890865959395829056383226613199282902678"
        "80675208766892501711696207032221043216269548626296"
        "31361443814975870122034080588795445474924618569536"
        "48006440972011691714755431680753379565646592729587"
        "09010767324751074167361764073129340740829693607895"
        "58615484252645224017643250348206476658092862091273"
        "49630339344686862540150116922082618572844938463656"
        "58698229636851160204858729366754090364536294004498"
        "75876326451034163030067474577231875946504543606480"
        "40645745132911402786653489893713905471740320470398"
        "65323294154917064055308643428664752556567479092957"
        "82304489740087287859649669303139075318665694683542"
        "69564876994036406534155194284246567126219867160221"
        "23050546459726437715429602047007441250023175843957"
        "52957109209163681516024451579488747183597567859464"
        "42445898614990776465706334693205330535580315564967"
        "36585664424173534071763547750565569814335786562418"
    )
    digits = [int(c) for c in _phi_str[:count]]
    return digits[:count]


def get_digit_sequence(key, count):
    """根据序列键获取十进制数字序列"""
    needed = max(count * 3, 1000)
    
    if key == 'pi':
        return get_pi_digits(needed)
    elif key == 'e':
        return get_e_digits(needed)
    elif key == 'phi':
        return get_phi_digits(needed)
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
    orig_format = os.path.splitext(input_path)[1].lstrip('.')
    if not orig_format:
        orig_format = img.format or 'jpg'
    # 统一格式名
    if orig_format.lower() in ('jpeg',):
        orig_format = 'jpg'
    
    # 2. Padding处理
    pad_w = (block_w - orig_w % block_w) % block_w
    pad_h = (block_h - orig_h % block_h) % block_h
    
    if pad_w > 0 or pad_h > 0:
        # 创建新的黑色画布并粘贴原图
        padded_w = orig_w + pad_w
        padded_h = orig_h + pad_h
        img_padded = Image.new(img.mode, (padded_w, padded_h), (0, 0, 0) if img.mode == 'RGB' else (0, 0, 0, 255))
        img_padded.paste(img, (0, 0))
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
    
    # PNG使用PngInfo存储元数据，同时尝试写入EXIF
    from PIL import PngImagePlugin
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text('UserComment', param_str)
    
    # 同时构建EXIF数据嵌入PNG
    try:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "Interop": {}}
        user_comment = b'ASCII\x00\x00\x00' + param_str.encode('ascii')
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = user_comment
        exif_bytes = piexif.dump(exif_dict)
        encrypted_img.info['exif'] = exif_bytes
    except Exception:
        pass
    
    encrypted_img.save(output_path, 'PNG', pnginfo=pnginfo)
    
    print(f"加密完成，解密参数: {param_str}")
    print(f"加密图片已保存到: {output_path}")


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
    
    # 首先尝试从PNG tEXt块读取
    if 'UserComment' in img_for_meta.info:
        param_str = img_for_meta.info['UserComment']
    
    # 然后尝试从EXIF读取
    if param_str is None:
        try:
            exif_dict = piexif.load(input_path)
            user_comment_bytes = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment, None)
            if user_comment_bytes is not None:
                if isinstance(user_comment_bytes, bytes):
                    if user_comment_bytes[:8] == b'ASCII\x00\x00\x00':
                        param_str = user_comment_bytes[8:].decode('ascii')
                    else:
                        param_str = user_comment_bytes.decode('ascii', errors='ignore')
                else:
                    param_str = str(user_comment_bytes)
        except Exception:
            pass
    
    # 最后尝试从PNG文件的exif数据读取
    if param_str is None and 'exif' in img_for_meta.info:
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
        raise RuntimeError("加密图片中未找到解密参数（UserComment标签缺失）")
    
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
    # 根据原始格式选择保存方式
    save_format = orig_format.upper()
    if save_format == 'JPG':
        save_format = 'JPEG'
    
    if save_format == 'JPEG':
        # JPEG不支持RGBA，需要转换
        if decrypted_img.mode == 'RGBA':
            decrypted_img = decrypted_img.convert('RGB')
        decrypted_img.save(output_path, 'JPEG', quality=95)
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
