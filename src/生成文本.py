# 1. 使用列表推导式生成 XY-01 到 XY-500 的字符串列表
# :02d 表示格式化为两位整数，不足两位前面自动补 0
xy_list = [f"XY-{i:02d}" for i in range(1, 501)]

# 2. 使用逗号将列表中的所有元素拼接成一个长字符串
content = "，".join(xy_list)

# 3. 将结果保存到 txt 文件中
output_filename = "/Users/teacher/Desktop/XY编号列表.txt"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ 成功生成 {output_filename}，共包含 {len(xy_list)} 个编号！")