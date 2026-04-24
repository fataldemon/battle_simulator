# main.py
# 战斗模拟器 v14 - 主程序 (最终重构版)

import random
from monster import MONSTERS_DATA, Monster
from player import PLAYERS_DATA, Player

def init_game():
    """初始化游戏 - 随机副本模式"""
    print("=" * 50)
    print("📜 团队副本模拟器 v14 (模块化重构版)")
    print("=" * 50)
    
    # 1. 筛选不同等级的怪物池
    low_level_pool = [m for m in MONSTERS_DATA if m['level'] <= 5]
    mid_level_pool = [m for m in MONSTERS_DATA if 6 <= m['level'] <= 10]
    high_level_pool = [m for m in MONSTERS_DATA if m['level'] > 10]
    
    # 2. 随机选择副本模式
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
        
    # 打印初始状态
    print("-" * 50)
    for m in enemy_team:
        if m.is_alive():
            m.print_status()
    
    # 3. 初始化玩家
    party = []
    for p_data in PLAYERS_DATA:
        party.append(Player(p_data))
        
    print(f"我方小队：{', '.join([p.name for p in party])}")
    print("-" * 50)
    
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

def process_player_actions(enemy_team, party):
    """处理玩家行动 (极简版)"""
    # 分离爱丽丝和其他队友
    alice = None
    others = []
    for p in party:
        if p.name == "爱丽丝":
            alice = p
        else:
            others.append(p)
            
    # 1. 爱丽丝行动 (她自己会处理所有逻辑和打印)
    if alice and alice.is_alive():
        alice.get_action(enemies=enemy_team)
        
        # 如果爱丽丝击败了所有敌人，直接结束行动阶段
        if not any(m.is_alive() for m in enemy_team):
            return

    # 2. 其他队友行动
    for player in others:
        if not player.is_alive():
            continue
            
        # 检查是否被束缚
        if player.is_stunned:
            print(f"\n   >> {player.name} 的行动:")
            print(f"   🕸️ {player.name} 被束缚住了，无法行动！")
            player.is_stunned = False 
            continue

        print(f"\n   >> {player.name} 的行动:")
        # 获取行动结果
        action = player.get_action(enemies=enemy_team)
        
        # 修复：行动前检查敌人是否全灭
        if not any(m.is_alive() for m in enemy_team):
            break

        # --- 模块化处理玩家返回的特殊效果 ---
        # 这里不再判断具体的角色名，而是判断动作类型！
        
        if action["type"] == "heal":
            # 治疗逻辑
            heal_amount = action["amount"]
            for p in party:
                if p.is_alive():
                    p.hp = min(p.max_hp, p.hp + heal_amount)
                    p.add_status_effect("💚", "治愈", 1, "heal", heal_amount)
            print(f"   > 全队恢复了 {heal_amount} HP！")
            
        elif action["type"] == "plot_debuff":
            # 桃井的 Debuff 逻辑
            effect = action["effect"]
            for m in enemy_team:
                if m.is_alive():
                    # 添加状态效果
                    if effect == "attack_down":
                        m.add_status_effect("📉", "攻击力下降", 1, "attack_down", 0.3)
                        # 即时生效：基于base计算，避免与update_status_effects冲突
                        m.current_atk = int(m.base_atk * 0.7)
                        m.atk = m.current_atk # 同步更新
                        print(f"   > {m.name} 的攻击力下降了！")
                    elif effect == "defense_down":
                        m.add_status_effect("📉", "防御力下降", 1, "defense_down", 0.2)
                        # 即时生效
                        m.defense = int(m.base_defense * 0.8)
                        print(f"   > {m.name} 的防御力下降了！")
                        
        elif action["type"] == "plot_buff":
            # 桃井的 Buff 逻辑
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

def process_monster_action(enemy_team, party):
    """处理怪物行动"""
    for boss in enemy_team:
        if not boss.is_alive():
            continue
            
        # 检查 Boss 是否被眩晕
        if boss.is_stunned:
            print(f"\n--- {boss.name} 的行动 ---")
            print(f"💫 {boss.name} 处于眩晕状态，无法行动！")
            boss.is_stunned = False 
            continue

        print(f"\n--- {boss.name} 的行动 ---")
        print(f"「{boss.quote}」")
        
        # 调用怪物自己的 AI
        boss.decide_action(party)

def main():
    enemy_team, party = init_game()
    turn = 1
    MAX_TURNS = 50  # 最大回合数限制
    
    while not check_game_over(enemy_team, party):
        if turn > MAX_TURNS:
            print(f"\n⚠️ 警告！回合数已达到上限 ({MAX_TURNS})！")
            print("💥 战斗陷入僵局，无法击败敌人！")
            break
            
        print(f"\n--- 第 {turn} 回合 ---")
        
        # 显示所有怪物血条
        for m in enemy_team:
            if m.is_alive():
                m.print_status()
        
        # 显示玩家血条和状态图标
        print("\n   【我方状态】")
        for p in party:
            if p.is_alive():
                p.print_status()
        
        # 玩家行动
        process_player_actions(enemy_team, party)
        
        if check_game_over(enemy_team, party):
            break
            
        # 怪物行动
        process_monster_action(enemy_team, party)
        
        # 回合结束，更新状态效果
        for p in party:
            if p.is_alive():
                p.update_status_effects()
        for m in enemy_team:
            if m.is_alive():
                m.update_status_effects()
        
        turn += 1

if __name__ == "__main__":
    main()