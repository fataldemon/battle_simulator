# utils.py
# 战斗模拟器 v44.3 - 辅助工具模块 (含物理挤压与朝向更新)

def squeeze_move(battle_field, unit_to_move, new_pos):
    """
    【v44.3 修复】物理挤压移动算法 (平移填充版)
    采用“全员平移”策略：移动单位离开后，中间单位填补空缺，形成目标位。
    
    :param battle_field: 完整的战场列表 (按位置排序)
    :param unit_to_move: 要移动的单位对象
    :param new_pos: 目标位置索引
    :return: bool 是否成功移动
    """
    current_pos = unit_to_move.position
    
    # 边界检查
    new_pos = max(0, min(len(battle_field) - 1, new_pos))
    
    # 如果位置没变，直接返回
    if new_pos == current_pos:
        return False
    
    # 确定移动方向以更新朝向
    moving_right = new_pos > current_pos
    
    # --------------------------------------------------------------------------
    # 【新方案】全员平移填补空缺
    # --------------------------------------------------------------------------
    
    # 1. 暂存移动单位（模拟离开座位）
    temp_unit = battle_field[current_pos]
    
    if moving_right:
        # 向右移动：[current_pos, new_pos-1] 区间内的单位向左挪一格
        # 例如：从0移到3，则1->0, 2->1, 3->2
        for i in range(current_pos, new_pos):
            battle_field[i] = battle_field[i+1]
    else:
        # 向左移动：[new_pos, current_pos-1] 区间内的单位向右挪一格
        # 例如：从3移到0，则2->3, 1->2, 0->1
        for i in range(current_pos, new_pos, -1):
            battle_field[i] = battle_field[i-1]
            
    # 2. 将移动单位填入现在空出来的目标位置
    battle_field[new_pos] = temp_unit
    
    # 3. 【关键修复】重新校准全场 position
    # 列表内容变了，必须同步属性
    for i, unit in enumerate(battle_field):
        unit.position = i
        
    # 4. 更新朝向
    if hasattr(unit_to_move, 'facing'):
        if moving_right:
            unit_to_move.facing = 1
        else:
            unit_to_move.facing = -1
            
    return True