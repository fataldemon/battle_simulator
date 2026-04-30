# main.py
# 战斗模拟器 v44.5 - 主程序 (全员能量与高级状态重构版 + 物理挤压引擎 + 朝向与背刺系统 + 装备管家集成 + UI增强)
# 核心改进：
# 1. 【v44.4 新增】装备系统集成：在回合开始阶段调用装备管家，触发被动/回合初特效。
# 2. 【v44.5 新增】装备 UI 增强：初始化时打印装备效果说明 + 状态栏醒目显示。
# 3. 保留了此前的能量系统、高级状态、朝向系统等所有功能。

import argparse
import random
from monster import MONSTERS_DATA, Monster
from player import PLAYERS_DATA, Player
from utils import squeeze_move
# ============================================================
# 【v44.4 新增】导入装备系统的调度器
# ============================================================
from equipment import scan_and_trigger, BattleEvents


def print_equipment_summary(party):
    """
    【v44.5 新增】打印全队装备清单（游戏初始化时调用一次）
    """
    print("\n" + "=" * 50)
    print("🎒 队伍装备配置一览")
    print("=" * 50)
    
    for p in party:
        if p.equipment_list:
            eq_details = []
            for eq in p.equipment_list:
                detail = f"{eq.rarity.icon}{eq.name} | {eq.description}"
                if eq.is_unique:
                    detail += " ★唯一"
                eq_details.append(detail)
            
            print(f"\n👤 {p.name}:")
            for detail in eq_details:
                print(f"   ├─ {detail}")
        else:
            print(f"\n👤 {p.name}: (无装备)")
    
    print("\n" + "-" * 50)


def init_game_random():
    """初始化游戏 - 随机副本模式"""
    print("=" * 50)
    print("📜 团队副本模拟器 v44.5 (装备管家集成版 + UI增强)")
    print("=" * 50)
    
    low_level_pool = [m for m in MONSTERS_DATA if m['level'] <= 5]
    mid_level_pool = [m for m in MONSTERS_DATA if 6 <= m['level'] <= 10]
    high_level_pool = [m for m in MONSTERS_DATA if m['level'] > 10]
    
    mode = random.choice(['sea_king', 'dual_elite', 'solo_boss'])
    enemy_team = []
    
    if mode == 'sea_king':
        num_enemies = random.randint(3, 4)
        print(f"\n⚠️ 警报！前方遭遇了 {num_enemies} 只低级怪物！(海王模式)")
        for i in range(num_enemies):
            monster_data = random.choice(low_level_pool)
            enemy = Monster(monster_data)
            enemy_team.append(enemy)
            print(f"   - {enemy.name} (LV.{enemy.level}) 出现！")
            
    elif mode == 'dual_elite':
        num_enemies = 2
        print(f"\n⚠️ 警报！前方遭遇了 {num_enemies} 只中级精英怪！(双精英模式)")
        for i in range(num_enemies):
            monster_data = random.choice(mid_level_pool)
            enemy = Monster(monster_data)
            enemy_team.append(enemy)
            print(f"   - {enemy.name} (LV.{enemy.level}) 出现！")
            
    elif mode == 'solo_boss':
        num_enemies = 1
        print(f"\n⚠️ 警报！前方遭遇了 1 只高级Boss！(独狼模式)")
        monster_data = random.choice(high_level_pool)
        enemy = Monster(monster_data)
        enemy_team.append(enemy)
        print(f"   - {enemy.name} (LV.{enemy.level}) 出现！")
        
    print("-" * 50)
    for m in enemy_team:
        if m.is_alive():
            m.print_status()
    
    party = []
    for p_data in PLAYERS_DATA:
        party.append(Player(p_data))
        
    print(f"我方小队：{', '.join([p.name for p in party])}")
    
    # 【v44.5 新增】打印装备配置清单
    print_equipment_summary(party)
    
    return enemy_team, party

def init_game_custom(args):
    """初始化游戏 - 自定义模式"""
    if not args.monster and not args.level:
        return init_game_random()

    print("=" * 50)
    print("📜 团队副本模拟器 v44.5 (装备管家集成版 + UI增强)")
    print("=" * 50)
    
    enemy_team = []
    
    if args.monster:
        targets = [t.strip() for t in args.monster.split(',')]
        print(f"\n⚠️ 警报！前方遭遇了指定怪物！")
        
        for target in targets:
            found_monster = None
            try:
                idx = int(target)
                if 0 <= idx < len(MONSTERS_DATA):
                    found_monster = MONSTERS_DATA[idx]
                else:
                    print(f"   ❌ 索引 {idx} 超出范围，跳过。")
                    continue
            except ValueError:
                for m_data in MONSTERS_DATA:
                    if target in m_data['name']:
                        found_monster = m_data
                        break
            
            if found_monster:
                enemy = Monster(found_monster)
                enemy_team.append(enemy)
                print(f"   - {enemy.name} (LV.{enemy.level}) 出现！")
            else:
                print(f"   ❌ 未找到怪物: {target}")
                
    elif args.level:
        target_level = int(args.level)
        current_level = 0
        print(f"\n⚠️ 警报！前方遭遇了等级总和约为 {target_level} 的怪物群！")
        
        while current_level < target_level:
            valid_candidates = [m for m in MONSTERS_DATA if m['level'] <= target_level]
            if not valid_candidates:
                break
            monster_data = random.choice(valid_candidates)
            enemy = Monster(monster_data)
            enemy_team.append(enemy)
            current_level += enemy.level
            print(f"   - {enemy.name} (LV.{enemy.level}) 出现！")
            
        print(f"   (当前总等级: {current_level})")
        
    print("-" * 50)
    for m in enemy_team:
        if m.is_alive():
            m.print_status()
    
    party = []
    for p_data in PLAYERS_DATA:
        party.append(Player(p_data))
        
    print(f"我方小队：{', '.join([p.name for p in party])}")
    
    # 【v44.5 新增】打印装备配置清单
    print_equipment_summary(party)
    
    return enemy_team, party

def check_game_over(enemy_team, party):
    """检查游戏结束条件"""
    if all(not m.is_alive() for m in enemy_team):
        print("\n🏆 恭喜！团队副本攻略成功！")
        return True
    if not any(p.is_alive() for p in party):
        print("\n💔 战败... 所有队员都倒下了...")
        return True
    return False

def setup_battle_field(enemy_team, party):
    """
    【v22/v44.2 新增】初始化战场队列
    将玩家和怪物混合成一个列表，并根据阵营分配初始位置。
    【v44.2 增强】确保朝向已正确初始化 (Player: 1, Monster: -1)
    """
    # 初始状态：玩家在前，怪物在后
    battle_field = party + enemy_team
    
    # 校准所有人的 position
    for i, unit in enumerate(battle_field):
        unit.position = i
        
    # 【v44.2 确认】再次确认朝向设置 (虽然类初始化已经做了，但这里再保险一下)
    for p in party:
        p.facing = 1
    for m in enemy_team:
        m.facing = -1
        
    print("\n📍 战场队列已初始化！")
    print(f"   我方站位：{[p.name for p in party]}")
    print(f"   敌方站位：{[m.name for m in enemy_team]}")
    
    return battle_field

def print_battle_formation(battle_field, party):
    """【v44.2 新增】打印战场站位概览的辅助函数"""
    print("\n[战场站位概览]")
    for i, unit in enumerate(battle_field):
        if unit.is_alive():
            prefix = "🟢" if unit in party else "🔴"
            # 【v44.2 新增】显示朝向
            unit_facing = "➡️" if getattr(unit, 'facing', 1) == 1 else "⬅️"
            print(f"   {prefix} [{i}] {unit.name} {unit_facing}")

def process_movement_phase(battle_field, enemy_team, party):
    """
    【v43/v44.2 重构】移动阶段
    新增：
    1. 检查 is_immobilized 状态，被束缚者无法移动。
    2. 检查 is_blinded 状态，被致盲者无法控制移动，只能随机乱撞。
    3. 【v44.2】移动后朝向由 utils.squeeze_move 自动更新。
    """
    print("\n--- 🏃 移动阶段 ---")
    
    # 1. 玩家（爱丽丝）移动逻辑
    alice = None
    for unit in battle_field:
        if unit.name == "爱丽丝":
            alice = unit
            break
            
    if alice and alice.is_alive():
        # 【v43 新增】检查是否被致盲
        if alice.is_blinded:
            print(f"   👁️❌ 爱丽丝陷入了致盲状态！眼前一片漆黑，她只能凭着感觉乱撞！")
            # 随机移动逻辑：原地或向左右随机移动 0-2 格
            move_dist = random.randint(0, 2)
            direction = random.choice([-1, 1])
            new_pos = alice.position + (move_dist * direction)
            
            # 简单的边界限制 (不能跑出队列)
            new_pos = max(0, min(len(battle_field)-1, new_pos))
            
            if new_pos != alice.position:
                squeeze_move(battle_field, alice, new_pos)
                print(f"   🏃 爱丽丝 踉跄地挤到了第 {new_pos} 号位！")
                # 【v44.2 修复】只有真正移动了才打印概览
                print_battle_formation(battle_field, party)
            else:
                print(f"   >> 爱丽丝在原地焦急地转了一圈，哪儿也没去成。")
                
        # 【v40 新增】检查是否被束缚
        elif alice.is_immobilized:
            print(f"   🕸️ 爱丽丝被蛛网束缚住了！本回合无法移动！")
            
        else:
            # 【v25 优化】简化输入：直接输入数字，相同即不动
            # 【v26 修复】确保提示信息清晰可见
            facing_icon = "➡️" if alice.facing == 1 else "⬅️"
            print(f"   >>> 爱丽丝当前位于第 {alice.position} 号位，朝向 {facing_icon} <<<")
            print(f"   >>> 请输入目标位置索引 (0-{len(battle_field)-1})，相同位置表示不动 <<<", flush=True)
            try:
                raw_input = input()
                target_pos = int(raw_input)
                
                if target_pos == alice.position:
                    print(f"   >> 爱丽丝选择了坚守。")
                else:
                    squeeze_move(battle_field, alice, target_pos)
                    # 【v44.2 修复】补充移动成功的文字反馈，保持 UI 一致性
                    print(f"   >> 爱丽丝 移动到了第 {alice.position} 号位！")
                    # 【v44.2 修复】只有真正移动了才打印概览，避免重复刷屏
                    print_battle_formation(battle_field, party)
            except ValueError:
                print("   输入无效，爱丽丝坚守。")
                    
    # 2. 队友 (桃井、小绿、柚子) 不移动 (保持阵型)
            
    # 3. 【v29 修复】移除了这里的怪物移动逻辑！
    # 怪物现在只会在我方的"怪物行动阶段"才会移动。
    # 这样可以保证玩家回合的稳定性。
    print("   >> 此时并非怪物的回合，它们正在原地虎视眈眈……")

def process_player_actions(battle_field, enemy_team, party):
    """处理玩家行动"""
    alice = None
    others = []
    for p in party:
        if p.name == "爱丽丝":
            alice = p
        else:
            others.append(p)
            
    if alice and alice.is_alive():
        alice.get_action(enemies=enemy_team)
        if not any(m.is_alive() for m in enemy_team):
            return

    for player in others:
        if not player.is_alive():
            continue
            
        if player.is_stunned:
            print(f"\n   >> {player.name} 的行动:")
            print(f"   🕸️ {player.name} 被束缚住了，无法行动！")
            player.is_stunned = False 
            continue

        print(f"\n   >> {player.name} 的行动:")
        action = player.get_action(enemies=enemy_team, party=party)
        
        if not any(m.is_alive() for m in enemy_team):
            break

        if action["type"] == "heal":
            heal_amount = action["amount"]
            for p in party:
                if p.is_alive():
                    p.hp = min(p.max_hp, p.hp + heal_amount)
                    p.add_status_effect("💚", "治愈", 1, "heal", heal_amount)
            print(f"   > 全队恢复了 {heal_amount} HP！")
            
        elif action["type"] == "plot_debuff":
            effect = action["effect"]
            for m in enemy_team:
                if m.is_alive():
                    if effect == "attack_down":
                        m.add_status_effect("📉", "攻击力下降", 3, "attack_down", 0.3)
                        m.current_atk = int(m.base_atk * 0.7)
                        m.atk = m.current_atk
                        print(f"   > {m.name} 的攻击力下降了！")
                    elif effect == "defense_down":
                        m.add_status_effect("📉", "防御力下降", 3, "defense_down", 0.2)
                        m.defense = int(m.base_defense * 0.8)
                        print(f"   > {m.name} 的防御力下降了！")
                        
        elif action["type"] == "plot_buff":
            effect = action["effect"]
            if effect == "heal":
                heal_amount = action["amount"]
                for p in party:
                    if p.is_alive():
                        p.hp = min(p.max_hp, p.hp + heal_amount)
                print(f"   > 全队恢复了 {heal_amount} HP！")
            elif effect == "atk_up":
                buff_amount = action["amount"]
                for p in party:
                    if p.is_alive():
                        p.atk += buff_amount
                        p.add_status_effect("⚔️", "攻击力提升", 2, "atk_up", 0.2)
                print(f"   > 全队攻击力提升了！")
        
        # 【v21 追加】行动结束后，立即刷新一次状态显示
        print("\n   [即时状态刷新]")
        for m in enemy_team:
            if m.is_alive():
                m.print_status()

def process_monster_action(battle_field, enemy_team, party):
    """
    【v43.1/v44.2 升级】处理怪物行动
    重大改动：向怪物决策函数传递完整的战场列表 (battle_field)，以支持物理挤压移动。
    """
    for boss in enemy_team:
        if not boss.is_alive():
            continue
            
        if boss.is_stunned:
            print(f"\n--- {boss.name} 的行动 ---")
            print(f"💫 {boss.name} 处于眩晕状态，无法行动！")
            boss.is_stunned = False 
            continue

        print(f"\n--- {boss.name} 的行动 ---")
        print(f"「{boss.quote}」")
        # 【v43.1 核心修复】将 battle_field 传递给怪物，让它们能看到全局并进行推挤
        boss.decide_action(party, battle_field)

def sync_battle_field_positions(battle_field):
    """
    【v43 紧急修复】根据各单位当前的 position 属性重新排序战场队列，并校正索引。
    解决怪物移动后未同步更新列表顺序导致的显示 Bug。
    """
    # 按 position 从小到大排序
    battle_field.sort(key=lambda u: u.position)
    
    # 重新分配连续的 index 给每个人，确保没有空缺或重叠
    for i, unit in enumerate(battle_field):
        unit.position = i

def main():
    parser = argparse.ArgumentParser(description="战斗模拟器 v44.5")
    parser.add_argument('--level', type=int, help='指定怪物总等级')
    parser.add_argument('--monster', type=str, help='指定怪物列表')
    args = parser.parse_args()
    
    enemy_team, party = init_game_custom(args)
    
    # 【v22 新增】初始化战场队列
    battle_field = setup_battle_field(enemy_team, party)
    
    turn = 1
    MAX_TURNS = 50
    
    while not check_game_over(enemy_team, party):
        if turn > MAX_TURNS:
            print(f"\n⚠️ 警告！回合数已达到上限 ({MAX_TURNS})！")
            print("💥 战斗陷入僵局！")
            break
            
        print(f"\n--- 第 {turn} 回合 ---")
        
        # ============================================================
        # 【v44.4 新增】装备管家介入：回合初扫描 (Pre-Turn Scan)
        # 触发所有带有 PRE_TURN 标签的装备特效（如每回合回血、充能等）
        # ============================================================
        for p in party:
            if p.is_alive():
                try:
                    scan_and_trigger(p, BattleEvents.PRE_TURN, context_info=None)
                except Exception as e:
                    print(f"   ⚠️ 回合初装备扫描异常: {str(e)}")

        # 【v30 新增】战场清理与重排
        # 移除所有死亡的单位，确保队列紧凑，防止僵尸单位挡住路径
        previous_len = len(battle_field)
        battle_field = [u for u in battle_field if u.is_alive()]
        
        if len(battle_field) < previous_len:
            print("\n🧹 战场清扫完成！倒下的队员已离场，剩余人员向前靠拢！")
            # 重新校准位置索引
            for i, unit in enumerate(battle_field):
                unit.position = i
            
        # 【v22 新增】显示全场站位概览
        print_battle_formation(battle_field, party)
        
        # 【v22 新增】移动阶段 (传入 enemy_team 用于补位逻辑，以及 party 用于识别阵营)
        process_movement_phase(battle_field, enemy_team, party)
        
        # 重新刷新血条和状态 (因为站位变了)
        print("\n[敌方状态]", flush=True)
        for m in enemy_team:
            if m.is_alive():
                m.print_status()
        
        print("[我方状态]", flush=True)
        for p in party:
            if p.is_alive():
                p.print_status()
        
        # 行动阶段
        process_player_actions(battle_field, enemy_team, party)
        
        if check_game_over(enemy_team, party):
            break
            
        process_monster_action(battle_field, enemy_team, party)
        
        # 【v43 紧急修复】怪物行动结束后，必须同步更新战场队列顺序！
        # 否则怪物的 position 变动不会反映在下一轮的站位图上
        sync_battle_field_positions(battle_field)
        
        for p in party:
            if p.is_alive():
                p.update_status_effects()
        for m in enemy_team:
            if m.is_alive():
                m.update_status_effects()
        
        turn += 1

if __name__ == "__main__":
    main()