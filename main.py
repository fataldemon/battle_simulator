# main.py
# 战斗模拟器 v21 - 主程序 (修复状态栏与重复台词 + 即时刷新)

import argparse
import random
from monster import MONSTERS_DATA, Monster
from player import PLAYERS_DATA, Player

def init_game_random():
    """初始化游戏 - 随机副本模式"""
    print("=" * 50)
    print("📜 团队副本模拟器 v21 (随机模式)")
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
    print("-" * 50)
    
    return enemy_team, party

def init_game_custom(args):
    """初始化游戏 - 自定义模式"""
    if not args.monster and not args.level:
        return init_game_random()

    print("=" * 50)
    print("📜 团队副本模拟器 v21 (自定义模式)")
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
                        # 【修复】将桃井的 Debuff 持续时间从 1 改为 3，以便在状态栏显示
                        m.add_status_effect("📉", "攻击力下降", 3, "attack_down", 0.3)
                        m.current_atk = int(m.base_atk * 0.7)
                        m.atk = m.current_atk
                        print(f"   > {m.name} 的攻击力下降了！")
                    elif effect == "defense_down":
                        # 【修复】将桃井的 Debuff 持续时间从 1 改为 3
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
        
        # 【v21 追加】行动结束后，立即刷新一次状态显示，让玩家能即时看到 buff/debuff
        print("\n   [即时状态刷新]")
        for m in enemy_team:
            if m.is_alive():
                m.print_status()

def process_monster_action(enemy_team, party):
    """处理怪物行动"""
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
        boss.decide_action(party)

def main():
    parser = argparse.ArgumentParser(description="战斗模拟器 v21")
    parser.add_argument('--level', type=int, help='指定怪物总等级')
    parser.add_argument('--monster', type=str, help='指定怪物列表')
    args = parser.parse_args()
    
    enemy_team, party = init_game_custom(args)
    
    turn = 1
    MAX_TURNS = 50
    
    while not check_game_over(enemy_team, party):
        if turn > MAX_TURNS:
            print(f"\n⚠️ 警告！回合数已达到上限 ({MAX_TURNS})！")
            print("💥 战斗陷入僵局！")
            break
            
        print(f"\n--- 第 {turn} 回合 ---")
        
        # 显示所有怪物血条
        print("\n[敌方状态]", flush=True)
        for m in enemy_team:
            if m.is_alive():
                m.print_status()
        
        # 显示玩家血条和状态图标
        print("[我方状态]", flush=True)
        for p in party:
            if p.is_alive():
                p.print_status()
        
        process_player_actions(enemy_team, party)
        
        if check_game_over(enemy_team, party):
            break
            
        process_monster_action(enemy_team, party)
        
        for p in party:
            if p.is_alive():
                p.update_status_effects()
        for m in enemy_team:
            if m.is_alive():
                m.update_status_effects()
        
        turn += 1

if __name__ == "__main__":
    main()