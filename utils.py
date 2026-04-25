# utils.py
# 战斗模拟器 v27 - 战场辅助工具模块 (推挤版)

def squeeze_move(all_units, unit_to_move, new_position):
    """
    挤压式换位核心逻辑 v27
    
    参数:
    all_units: 包含所有存活单位 (玩家和怪物) 的列表
    unit_to_move: 要移动的单位对象
    new_position: 目标位置的索引 (int)
    
    逻辑:
    1. 从当前位置移除该单位。
    2. 插入到新位置。
    3. 重新遍历整个列表，更新每个单位的 position 属性。
    """
    old_position = unit_to_move.position
    
    # 边界检查：防止移动到不存在的索引
    if new_position < 0 or new_position >= len(all_units):
        print(f"   ❌ {unit_to_move.name} 的移动目标无效！")
        return False

    # 1. 移除旧位置
    if unit_to_move in all_units:
        all_units.remove(unit_to_move)
    else:
        print(f"   ⚠️ 警告：{unit_to_move.name} 不在战场列表中！")
        return False

    # 2. 插入新位置 —— 这就是“插队”的感觉！
    # Python 的 insert 方法会自动把目标位置及之后的元素往后挪，完美复刻“推挤”效果
    all_units.insert(new_position, unit_to_move)

    # 3. 重新校准所有人的 position 索引（这就是“挤压”的过程！）
    for i, u in enumerate(all_units):
        u.position = i

    # 反馈信息
    direction = "向前" if new_position > old_position else ("向后" if new_position < old_position else "原地")
    print(f"   🏃 {unit_to_move.name} 挤到了第 {new_position} 号位 ({direction}移动)！")
    
    return True