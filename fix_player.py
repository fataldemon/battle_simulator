# 修复 player.py 中的语法错误
with open('player.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 将错误的转义 \\" 修正为正确的 \"
# 错误代码: print(f"   💀 {target.name} 倒下了... \\"{death_msg}\\"")
# 正确代码: print(f"   💀 {target.name} 倒下了... \"{death_msg}\"")
content = content.replace('\\\\"', '\\"')

with open('player.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Bug 已修复！")