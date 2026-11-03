import os
import shutil
from collections import defaultdict


def unflatten_directory(
    src_dir: str,
    dst_dir: str,
) -> None:
    """
    将扁平化的文件还原成原始目录结构（纯启发式，无 manifest）。

    策略：
    1. 把文件名中所有 '-' 都当作潜在分隔符
    2. 贪心最大化目录深度：把最后一段（含扩展名）作为文件名，前面的所有段都作为目录
    3. 利用全局路径共享推断：多个文件共享的前缀更可能是真实目录
       （实际上贪心策略下这一步自然满足，因为相同前缀自然落到同一目录）
    4. 处理连续 '-' 或首尾 '-' 产生的空段

    Args:
        src_dir: 扁平化文件所在的文件夹
        dst_dir: 还原后的输出文件夹
    """
    if not os.path.isdir(src_dir):
        raise ValueError(f"源文件夹不存在或不是文件夹: {src_dir}")

    os.makedirs(dst_dir, exist_ok=True)

    # 第一步：收集所有文件名并拆分为"潜在路径段"
    files_to_process = []
    for filename in os.listdir(src_dir):
        file_path = os.path.join(src_dir, filename)
        if not os.path.isfile(file_path):
            continue
        files_to_process.append(filename)

    if not files_to_process:
        print("源文件夹中没有文件，无需还原")
        return

    # 第二步：逐文件确定拆分方案
    # 记录每种"拆分深度"的统计，用于全局决策
    plan = _build_split_plan(files_to_process)

    # 第三步：按方案复制文件
    stats = {"restored": 0, "single_level": 0}
    for filename, segments in plan.items():
        src_file = os.path.join(src_dir, filename)
        dst_file = os.path.join(dst_dir, *segments)
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        shutil.copy2(src_file, dst_file)
        stats["restored"] += 1
        if len(segments) == 1:
            stats["single_level"] += 1

    print(f"还原完成！")
    print(f"  源文件夹: {os.path.abspath(src_dir)}")
    print(f"  目标文件夹: {os.path.abspath(dst_dir)}")
    print(f"  共还原 {stats['restored']} 个文件")
    print(f"  其中 {stats['single_level']} 个文件无子目录（顶层文件）")


def _build_split_plan(filenames: list) -> dict:
    """
    根据"最大化目录深度合理性"策略，为每个文件生成路径段列表。

    返回: {原始扁平文件名: [段1, 段2, ..., 文件名段]}
    """
    # 1. 先做单文件贪心拆分
    candidates = {}  # filename -> list of segments (贪心：全部拆开)
    for fn in filenames:
        segments = _split_by_dash(fn)
        candidates[fn] = segments

    # 2. 全局推断：统计每个"前缀段"被多少文件共享
    #    如果某个前缀只对应一个文件，且这个前缀不在其他文件的中间出现，
    #    那么它更可能是"原文件名的一部分"而非"目录名"。
    #
    #    但纯贪心策略下，我们无法区分。这里采用更实用的办法：
    #    - 若段数为 1（无 '-'），直接作为顶层文件
    #    - 若段数 > 1，全部按贪心拆分（最后一段为文件名，前面全是目录）
    #
    #    为了让"最大化目录深度"更合理，我们再做一个优化：
    #    如果某段是纯数字或纯字母，且出现在多个文件的同一位置，
    #    则保留为目录；否则也保留为目录（无法区分时倾向于拆开）。
    #
    #    实际上贪心拆分本身已经满足了"最大化目录深度"。
    #    这里额外的"合理性"体现在：把连续 '-' 产生的空段合并。

    plan = {}
    for fn, segments in candidates.items():
        # 合并空段（连续 '-' 或首尾 '-' 产生）
        cleaned = _merge_empty_segments(segments)
        plan[fn] = cleaned

    # 3. 优化：如果某个"目录段"实际上只对应一个文件，且与其他文件无共享，
    #    且这个目录段后面还有多个段... 这里保持贪心，不额外回退。
    #    但我们可以做一个"安全检查"：如果拆分后文件名为空（比如 'a-' 这种），
    #    则回退到不拆分。
    for fn in list(plan.keys()):
        if not plan[fn] or not plan[fn][-1]:
            plan[fn] = [fn]

    return plan


def _split_by_dash(filename: str) -> list:
    """
    把 'a-b-c.txt' 拆成 ['a', 'b', 'c.txt']。
    '-' 是分隔符，但扩展名前的部分视为文件名主体。
    """
    return filename.split('-')


def _merge_empty_segments(segments: list) -> list:
    """
    合并空段。
    - 连续的 '-' 产生的多个空段合并为一个
    - 首尾的空段去掉
    - 如果合并后为空，返回 [原文件名]（在调用方处理）
    """
    cleaned = []
    for seg in segments:
        if seg == '':
            # 空段：如果前一个不是空，保留一个空标记（表示原文件名里有连续 -）
            # 这里选择"直接跳过"，因为目录名通常不为空
            # 但为了保留"连续 - 是文件名一部分"的可能性，我们跳过空段
            continue
        cleaned.append(seg)
    if not cleaned:
        return []
    return cleaned


if __name__ == '__main__':
    # 使用示例
    src_dir = "/Users/teacher/Downloads/260张图片去水印_扁平化"
    dst_dir = f"{src_dir}_还原目录"
    unflatten_directory(
        src_dir=src_dir,
        dst_dir = dst_dir
    )