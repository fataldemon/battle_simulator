# team_battle_v12.0_main.py
# 战斗模拟器 v12.0 - 随机副本模式 (含血条、增益图标、详细技能说明)

import random
from monster import MONSTERS_DATA, Monster
from player import PLAYERS_DATA, Player

def init_game():
    """初始化游戏 - 随机副本模式"""
    print("=" * 50)
    print("📜 团队副本模拟器 v12.0 (随机副本模式)")
    print("=" * 50)
    
    # 1. 筛选不同等级的怪物池
    low_level_pool = [m for m in MONSTERS_DATA if m['level'] <= 5]
    mid_level_pool = [m for m in MONSTERS_DATA if 6 <= m['level'] <= 10]
    high_level_pool = [m for m in MONSTERS_DATA if m['level'] > 10]
    
    # 2. 随机选择副本模式
    # 模式：'sea_king' (海王), 'dual_elite' (双精英), 'solo_boss' (独狼Boss)
    mode = random.choice(['sea_king', 'dual_elite', 'solo_boss'])
    
    enemy_team = []
    
    if mode == 'sea_king':
        # 海王模式：3-4只低级怪
        num_enemies = random.randint(3, 4)
        print(f"\n⚠️ 警报！前方遭遇了 {num_enemies} 只低级怪物！(海王模式)")
        for i in range(num_enemies):
            monster_data = random.choice(low_level_pool)
            enemy = Monster(monster_data)
            enemy_team.append(enemy)
            print(f"   - {enemy.name} (LV.{enemy.level}) 出现！")
            
    elif mode == 'dual_elite':
        # 双精英模式：2只中级怪
        num_enemies = 2
        print(f"\n⚠️ 警报！前方遭遇了 {num_enemies} 只中级精英怪！(双精英模式)")
        for i in range(num_enemies):
            monster_data = random.choice(mid_level_pool)
            enemy = Monster(monster_data)
            enemy_team.append(enemy)
            print(f"   - {enemy.name} (LV.{enemy.level}) 出现！")
            
    elif mode == 'solo_boss':
        # 独狼Boss模式：1只高级怪
        num_enemies = 1
        print(f"\n⚠️ 警报！前方遭遇了 1 只高级Boss！(独狼模式)")
        monster_data = random.choice(high_level_pool)
        enemy = Monster(monster_data)
        enemy_team.append(enemy)
        print(f"   - {enemy.name} (LV.{enemy.level}) 出现！")
        
    # 打印初始状态 (使用新方法)
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
    # 胜利条件：所有怪物都死了
    if all(not m.is_alive() for m in enemy_team):
        print("\n🏆 恭喜！团队副本攻略成功！")
        return True
    # 失败条件：所有玩家都死了
    if not any(p.is_alive() for p in party):
        print("\n💔 战败... 所有队员都倒下了...")
        return True
    return False

def process_monster_action(enemy_team, party):
    """处理怪物行动"""
    for boss in enemy_team:
        if not boss.is_alive():
            continue
            
        # 检查 Boss 是否被眩晕
        if boss.is_stunned:
            print(f"\n--- {boss.name} 的行动 ---")
            print(f"💫 {boss.name} 处于眩晕状态，无法行动！")
            boss.is_stunned = False # 解除眩晕
            continue

        print(f"\n--- {boss.name} 的行动 ---")
        print(f"「{boss.quote}」")
        
        action = boss.decide_action(party)
        
        if action is None:
            continue

        # --- 处理特殊技能类型 (复用之前的逻辑) ---
        
        # 1. 陷阱类
        if action["type"] == "trap":
            alive_players = [p for p in party if p.is_alive()]
            if alive_players:
                target = random.choice(alive_players)
                target.is_stunned = True
                print(f"🕸️ {target.name} 被 {boss.name} 的【蛛网束缚】了！下回合无法行动！")
            continue

        # 2. 群体伤害类
        if action["type"] == "aoe_attack":
            total_dmg = action["total_damage"]
            print(f"💥 全员受到了波及！")
            for p in party:
                if p.is_alive():
                    dmg = p.take_damage(total_dmg)
                    print(f"   💢 {p.name} 受到了地震冲击，造成 {dmg} 点伤害！(剩余HP: {p.hp})")
                    # 修复：在打印伤害后，检查是否死亡
                    if not p.is_alive():
                        print(f"   💀 {p.name} 倒下了... ({p.death_msg})")
            continue

        # 3. 群体状态下降类
        if action["type"] == "debuff_all_stat":
            stat = action["stat"]
            ratio = action["ratio"]
            print(f"⚡ {boss.name} 释放了电磁脉冲！")
            for p in party:
                if p.is_alive():
                    if stat == "defense":
                        p.defense = int(p.defense * ratio)
                        print(f"   📉 {p.name} 的防御力下降了！(当前: {p.defense})")
                    elif stat == "attack":
                        p.atk = int(p.atk * ratio)
                        print(f"   📉 {p.name} 的攻击力下降了！(当前: {p.atk})")
            continue

        # 4. 群体攻击力下降类
        if action["type"] == "debuff_all_atk":
            for p in party:
                p.atk = int(p.atk * 0.8)
            print("😱 大家的攻击力下降了！")
            continue

        # --- 原有逻辑：单体攻击 ---
        if action["type"] == "attack":
            alive_players = [p for p in party if p.is_alive()]
            if not alive_players:
                continue
            target = random.choice(alive_players)
            
            dmg = action["damage"]
            
            # 简单的防御计算
            if target.name == "爱丽丝" and target.energy > 0:
                dmg = int(dmg * 0.8) 
            
            actual_dmg = target.take_damage(dmg)
            print(f"💥 击中了 {target.name}，造成 {actual_dmg} 点伤害！(剩余HP: {target.hp})")
            
            # 修复：在打印伤害后，检查是否死亡
            if not target.is_alive():
                print(f"   💀 {target.name} 倒下了... ({target.death_msg})")

def process_player_actions(enemy_team, party):
    """处理玩家行动"""
    # 新增：如果怪物已经全灭，直接返回，不再执行玩家行动
    if not any(m.is_alive() for m in enemy_team):
        return

    # 分离爱丽丝和其他队友
    alice = None
    others = []
    for p in party:
        if p.name == "爱丽丝":
            alice = p
        else:
            others.append(p)
            
    # 1. 先处理爱丽丝的行动 (调整顺序：爱丽丝第一)
    if alice and alice.is_alive():
        print(f"\n   >> {alice.name} 的行动:")
        
        # 检查爱丽丝是否被束缚
        if alice.is_stunned:
            print(f"   🕸️ {alice.name} 被束缚住了，无法行动！")
            alice.is_stunned = False
        else:
            # 修改点：传入 enemy_team 让爱丽丝可以选择目标
            action = alice.get_action(enemies=enemy_team)
            
            if action["type"] == "alice_ex":
                dmg = action["damage"]
                # 修改点：使用爱丽丝选择的 target
                target = action.get("target")
                if target:
                    result = target.take_damage(dmg)
                    print(f"   🌟 {action['msg']}")
                    print(f"   > 对 {target.name} 造成 {result['final_dmg']} 点巨额伤害!")
                    # 修复：在打印伤害后，检查是否死亡
                    if not target.is_alive():
                        print(f"   💀 {target.name} 倒下了...")
                
            elif action["type"] == "alice_charge":
                print(f"   {action['msg']}")
                
            elif action["type"] in ["normal_attack", "crit_attack"]:
                dmg = action["damage"]
                # 修改点：使用爱丽丝选择的 target
                target = action.get("target")
                if target:
                    result = target.take_damage(dmg)
                    print(f"   {action['msg']} (对 {target.name})")
                    # 修复：在打印伤害后，检查是否死亡
                    if not target.is_alive():
                        print(f"   💀 {target.name} 倒下了...")

    # 修复：如果爱丽丝击败了所有敌人，直接结束行动阶段，防止后续队友报错
    if not any(m.is_alive() for m in enemy_team):
        return

    # 2. 再处理其他队友的行动
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
        action = player.get_action()
        
        # 修复：行动前检查敌人是否全灭，防止报错
        if not any(m.is_alive() for m in enemy_team):
            break

        if action["type"] == "alice_ex":
            # 爱丽丝EX技能 (虽然这里不处理，但为了代码完整性保留)
            dmg = action["damage"]
            # 攻击第一个存活的怪物
            target = random.choice([m for m in enemy_team if m.is_alive()])
            if target:
                result = target.take_damage(dmg)
                print(f"   🌟 {action['msg']}")
                print(f"   > 对 {target.name} 造成 {result['final_dmg']} 点巨额伤害!")
                # 修复：在打印伤害后，检查是否死亡
                if not target.is_alive():
                    print(f"   💀 {target.name} 倒下了...")
            
        elif action["type"] == "alice_charge":
            # 爱丽丝充能
            print(f"   {action['msg']}")
            
        elif action["type"] == "plot_kill":
            # 桃井旧逻辑兼容
            print(f"   {action['msg']}")
            if action["effect"] == "attack_down":
                for m in enemy_team:
                    m.current_atk = int(m.current_atk * 0.7)
                print(f"   > BOSS 攻击力大幅下降！")
            elif action["effect"] == "damage_boost":
                dmg = random.randint(20, 50)
                target = random.choice([m for m in enemy_team if m.is_alive()])
                if target:
                    result = target.take_damage(dmg)
                    print(f"   > {target.name} 受到了 {result['final_dmg']} 点剧情伤害！")
                    # 修复：在打印伤害后，检查是否死亡
                    if not target.is_alive():
                        print(f"   💀 {target.name} 倒下了...")
                
        elif action["type"] == "plot_debuff":
            # 桃井新逻辑：Debuff
            print(f"   {action['msg']}")
            if action["effect"] == "attack_down":
                for m in enemy_team:
                    m.current_atk = int(m.current_atk * 0.7)
                print(f"   > BOSS 攻击力大幅下降！")
            elif action["effect"] == "defense_down":
                for m in enemy_team:
                    m.defense = int(m.defense * 0.8)
                print(f"   > BOSS 防御力下降了！")
                
        elif action["type"] == "plot_buff":
            # 桃井新逻辑：Buff - v12 新增：添加状态图标
            print(f"   {action['msg']}")
            if action["effect"] == "heal":
                heal_amount = action["amount"]
                for p in party:
                    if p.is_alive():
                        p.hp = min(p.max_hp, p.hp + heal_amount)
                print(f"   > 全队恢复了 {heal_amount} HP！")
            elif action["effect"] == "atk_up":
                buff_amount = action["amount"]
                for p in party:
                    if p.is_alive():
                        p.atk += buff_amount
                        # v12 新增：添加增益图标
                        p.add_status_effect("⚔️", "攻击力提升", 2, "atk_up", 0.2)
                print(f"   > 全队攻击力提升了！")
            
        elif action["type"] == "heal":
            # 小绿治疗 - v12 新增：添加状态图标
            heal_amount = action["amount"]
            for p in party:
                if p.is_alive():
                    p.hp = min(p.max_hp, p.hp + heal_amount)
                    # v12 新增：添加增益图标
                    p.add_status_effect("💚", "治愈", 1, "heal", heal_amount)
            print(f"   {action['msg']} (全队恢复 {heal_amount} HP)")
            
        elif action["type"] in ["normal_attack", "crit_attack"]:
            # 柚子/普通攻击
            dmg = action["damage"]
            # 攻击第一个存活的怪物
            target = random.choice([m for m in enemy_team if m.is_alive()])
            if target:
                result = target.take_damage(dmg)
                print(f"   {action['msg']} (对 {target.name})")
                # 修复：在打印伤害后，检查是否死亡
                if not target.is_alive():
                    print(f"   💀 {target.name} 倒下了...")
            
        elif action["type"] == "super_attack":
            # 柚子大招：眩晕
            print(f"   {action['msg']}")
            # 眩晕第一个存活的怪物
            target = random.choice([m for m in enemy_team if m.is_alive()])
            if target:
                target.is_stunned = True
                print(f"   > {target.name} 被眩晕了！")
            
        elif action["type"] == "support":
            print(f"   {action['msg']}")

def main():
    enemy_team, party = init_game()
    turn = 1
    MAX_TURNS = 50  # 新增：最大回合数限制
    
    while not check_game_over(enemy_team, party):
        # 新增：回合数限制检测
        if turn > MAX_TURNS:
            print(f"\n⚠️ 警告！回合数已达到上限 ({MAX_TURNS})！")
            print("💥 战斗陷入僵局，无法击败敌人！")
            break
            
        print(f"\n--- 第 {turn} 回合 ---")
        
        # 显示所有怪物血条 (使用新方法)
        for m in enemy_team:
            if m.is_alive():
                m.print_status()
        
        # v12 新增：显示玩家血条和状态图标 (使用新方法)
        print("\n   【我方状态】")
        for p in party:
            if p.is_alive():
                p.print_status()
        
        # 修改点：玩家先行动，怪物后行动
        # 2. 玩家行动
        process_player_actions(enemy_team, party)
        
        if check_game_over(enemy_team, party):
            break
            
        # 1. 怪物行动
        process_monster_action(enemy_team, party)
        
        # v12 新增：回合结束，更新状态效果
        for p in party:
            if p.is_alive():
                p.update_status_effects()
        for m in enemy_team:
            if m.is_alive():
                m.update_status_effects()
        
        turn += 1

if __name__ == "__main__":
    main()