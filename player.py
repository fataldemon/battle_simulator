# player.py
# 战斗模拟器 v39 - 玩家数据与行为逻辑模块 (技能顺序调整 v2 & 描述增强版 & 格式统一修复版)

import random
from skill import SKILL_REGISTRY, get_skill, AttackEffect, BuffEffect, DebuffEffect, StunEffect, HealEffect

class Player:
    def __init__(self, data):
        self.name = data["name"]
        self.role = data["role"]
        self.max_hp = data["hp"]
        self.hp = self.max_hp
        self.atk = data["atk"]
        self.defense = data["defense"]
        self.skill_name = data["skill"]
        self.energy = 0 # 爱丽丝专用能量
        self.has_used_super = False # 柚子专用：记录大招是否已使用
        self.is_stunned = False # 新增：被束缚状态
        self.death_msg = data.get("death_msg", "") # 新增：倒地台词
        
        # 【v22 新增】定位系统
        self.position = 0  # 初始位置默认为 0，将在游戏初始化时重新分配

        # v12 新增：状态列表 (Buff/Debuff)
        self.status_effects = []

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, damage):
        """受到攻击时的处理 (修正版：返回字典以兼容技能模块)"""
        actual_damage = max(1, damage - self.defense)
        actual_damage = int(actual_damage * random.uniform(0.9, 1.1))
        self.hp -= actual_damage
        if self.hp < 0:
            self.hp = 0
        return {"final_dmg": actual_damage}

    def add_status_effect(self, icon, name, duration, effect_type, value=0):
        """添加状态效果"""
        for i, status in enumerate(self.status_effects):
            if status["effect"] == effect_type:
                self.status_effects[i] = {"icon": icon, "name": name, "duration": duration, "effect": effect_type, "value": value}
                return
        self.status_effects.append({"icon": icon, "name": name, "duration": duration, "effect": effect_type, "value": value})

    def update_status_effects(self):
        """每回合结束时更新状态效果"""
        for status in self.status_effects:
            status["duration"] -= 1
            
        self.status_effects = [s for s in self.status_effects if s["duration"] > 0]
        
        for status in self.status_effects:
            if status["effect"] == "atk_up":
                self.atk = int(self.atk * (1 + status["value"]))
            elif status["effect"] == "defense_up":
                self.defense = self.defense + status["value"]
            elif status["effect"] == "atk_down":
                # 【修复】增加 Debuff 处理逻辑
                self.atk = int(self.atk * (1 - status["value"]))
            elif status["effect"] == "defense_down":
                # 【修复】增加 Debuff 处理逻辑
                self.defense = int(self.defense * (1 - status["value"]))

    def print_status(self):
        """打印状态信息：名字、血条、数值、状态图标"""
        bar_length = 20
        filled = int(self.hp / self.max_hp * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        status_str = ""
        if self.status_effects:
            icons = " ".join([s['icon'] for s in self.status_effects])
            status_str = f" {icons}"
        
        print(f"   {self.name}: [{bar}] {self.hp}/{self.max_hp}{status_str}")

    def _find_valid_targets(self, enemies, skill_range):
        """
        【v22 新增】根据射程寻找有效目标
        """
        valid_targets = []
        for enemy in enemies:
            if enemy.is_alive():
                distance = abs(enemy.position - self.position)
                if distance <= skill_range:
                    valid_targets.append(enemy)
        return valid_targets

    def get_action(self, enemies=None, party=None):
        """
        获取玩家行动 (模块化版 + 射程索敌 + 按位置索敌 v31 + 语音台词增强版 v32 + 普攻格式修正版 v34 + 全员台词替换版 v35 + 全面启用 Quote 版 v36 & 修复柚子重复台词版 v37 & 技能顺序调整 v38 & 技能顺序调整 v2 v39 & 格式统一修复版)
        """
        # 检查是否处于束缚状态
        if self.is_stunned:
            print(f"   🕸️ {self.name} 被蛛网束缚住了！无法行动！")
            self.is_stunned = False 
            return {"type": "stunned", "msg": f"{self.name} 无法行动"}

        if self.name == "爱丽丝":
            # === 交互逻辑：爱丽丝 ===
            alive_enemies = [m for m in enemies if m.is_alive()] if enemies else []
            
            if not alive_enemies:
                print("   ❌ 场上没有可攻击的目标！")
                return {"type": "no_target", "msg": "没有目标"}

            # 获取技能描述
            charge_skill = get_skill("alice_charge")
            ex_skill = get_skill("alice_ex")
            phys_skill = get_skill("alice_physical")

            # --- 修改：电池样式能量槽 (复古方块风格 - 无上限) ---
            # 动态生成能量槽
            # 限制最大显示长度，防止 UI 溢出屏幕，比如最多显示 10 个格子
            max_display = 10
            
            if self.energy > max_display:
                energy_bar = "[" + " ".join(["█"] * max_display) + "...]"
            else:
                # 确定显示的格子总数：至少 2 个，最多 max_display
                total_cells = max(2, self.energy)
                cells = ["█" if i < self.energy else "░" for i in range(total_cells)]
                energy_bar = "[" + " ".join(cells) + "]"
            # --------------------------------

            # 【v31 新增】计算可攻击的目标列表
            # 充能不需要目标
            # EX 技能是全图 AOE，可以攻击所有活着的敌人
            # 物理攻击需要检测射程
            
            ex_targets = alive_enemies # EX 技能全图
            phys_targets = self._find_valid_targets(enemies, phys_skill.range)
            
            # 格式化目标列表字符串
            ex_target_str = ", ".join([f"{e.name}[{e.position}]" for e in ex_targets]) if ex_targets else "无"
            phys_target_str = ", ".join([f"{t.name}[{t.position}]" for t in phys_targets]) if phys_targets else "无"

            print(f"\n   >> 爱丽丝，请做出你的行动！(能量: {energy_bar})")
            
            # 【v39 修改】技能顺序调整：光之剑(普攻) -> 充能 -> 光哟(EX)
            # [1] 普通攻击
            print(f"   [1] {phys_skill.name} [普通攻击]")
            print(f"       说明: {phys_skill.desc}")
            print(f"       射程: {phys_skill.range}")
            print(f"       可攻击目标: {phys_target_str}")
            
            # [2] 充能
            print(f"   [2] {charge_skill.name} [充能]")
            print(f"       说明: {charge_skill.desc}")
            print(f"       射程: N/A")

            # [3] EX技能
            # 计算大招倍率
            base_multiplier = ex_skill.multiplier
            energy_bonus = 0.5 
            stack_bonus = 1.0 + (self.energy * energy_bonus)
            final_multiplier = base_multiplier * stack_bonus
            
            ex_status = f" (倍率 x{final_multiplier:.2f})"
            if self.energy < 2:
                ex_status += " (❌ 能量不足)"
            
            print(f"   [3] {ex_skill.name} [EX技能]{ex_status}")
            print(f"       说明: {ex_skill.desc}")
            print(f"       射程: 全图")
            print(f"       可攻击目标: {ex_target_str}")
            
            print(f"\n   >>> 请输入指令：")
            print(f"   格式：敌人位置编号-技能序号 (例如：4-1)")
            
            while True:
                try:
                    combined_input = input().strip()
                    target_pos = None 
                    skill_idx = 1  
                    
                    if '-' in combined_input:
                        parts = combined_input.split('-')
                        try:
                            # 新逻辑：直接读取位置坐标
                            target_pos = int(parts[0])
                            skill_idx = int(parts[1])
                        except ValueError:
                            print("   ❌ 输入格式错误，请使用 '敌人位置-技能' 格式 (例如 4-1)")
                            continue
                    else:
                        try:
                            skill_idx = int(combined_input)
                            target_pos = None # 未指定位置
                        except ValueError:
                            print("   ❌ 输入无效，请输入数字")
                            continue

                    # 根据位置寻找目标
                    potential_target = None
                    if target_pos is not None:
                        # 遍历敌人列表，寻找 position 匹配的对象
                        for enemy in alive_enemies:
                            if enemy.position == target_pos:
                                potential_target = enemy
                                break
                        
                        if potential_target is None:
                            print(f"   ❌ 警告：第 {target_pos} 号位没有找到敌人！(可能是空位或队友)")
                            continue
                    else:
                        # 如果没指定位置，默认攻击第一个敌人（兼容旧习惯）
                        if alive_enemies:
                            potential_target = alive_enemies[0]
                        else:
                            potential_target = None
                    
                    # 检查射程
                    if skill_idx == 1: # 物理攻击
                        skill_range = phys_skill.range
                        if potential_target:
                            dist = abs(potential_target.position - self.position)
                            if dist > skill_range:
                                print(f"   ❌ 目标太远啦！射程只有 {skill_range}，距离是 {dist}！")
                                print(f"   请选择射程内的目标，或者取消攻击。")
                                continue
                        
                    elif skill_idx == 3: # EX技能 (全屏) -> 注意索引变为3
                        pass # 不需要检查，因为是 AOE

                    if skill_idx not in [1, 2, 3]:
                        print(f"   技能序号无效 (1-3)，默认执行普通攻击")
                        skill_idx = 1
                    
                    if skill_idx == 3 and self.energy < 2: # 注意索引变为3
                        print(f"   ❌ 能量不足！无法发动必杀技！(当前能量: {self.energy})")
                        print(f"   请重新输入指令。")
                        continue 
                    
                    break 

                except ValueError:
                    print("   输入格式错误，默认目标1，技能1 (普通攻击)")
                    potential_target = alive_enemies[0] if alive_enemies else None
                    skill_idx = 1
                    break

            # 执行技能
            if skill_idx == 1:
                # 物理攻击 (修复版：真正造成伤害 + 标准格式 v34 + 台词修正 v35 + Quote 版 v36 & v38/v39感叹号修复)
                dmg = int(random.randint(self.atk - 5, self.atk + 5))
                
                # 【修复】真正调用 take_damage 进行伤害结算
                result = potential_target.take_damage(dmg)
                actual_dmg = result['final_dmg']
                
                # 暴击判定
                is_crit = random.random() < 0.1
                if is_crit:
                    actual_dmg = int(actual_dmg * 1.5)
                    msg = f"✨ {self.name} 对 {potential_target.name} 进行了暴击攻击! 造成 {actual_dmg} 点伤害!"
                else:
                    msg = f"✨ {self.name} 对 {potential_target.name} 进行了普通攻击! 造成 {actual_dmg} 点伤害!"
                
                # 【v39 修正】统一使用双引号，去掉外部感叹号
                print(f"   🗡️ {self.name} 喊道: \"{phys_skill.quote}\"")
                print(f"   > {msg}")
                
                return {"type": "normal_attack", "msg": msg, "damage": actual_dmg, "target": potential_target}
            
            elif skill_idx == 2: # 注意索引变为2
                # 充能逻辑
                self.energy += 1
                # 【修复】增加打印语句
                # 【v39 修正】使用双引号，去掉外部感叹号
                print(f"   ⚡ {self.name} 喊道: \"{charge_skill.quote}\"")
                return {
                    "type": "alice_charge",
                    "msg": f"⚡ {self.name} 喊道: \"{charge_skill.quote}\" -> 能量充填层数 -> {self.energy}"
                }
            
            else: # skill_idx == 3
                # 释放大招 (特殊逻辑：消耗能量并增加伤害)
                base_multiplier = ex_skill.multiplier
                energy_bonus = 0.5 
                crit_chance = 0.15
                crit_mult = 2.0
                
                base_dmg = self.atk * base_multiplier
                stack_bonus = 1.0 + (self.energy * energy_bonus)
                final_multiplier = base_dmg * stack_bonus
                
                is_crit = random.random() < crit_chance
                if is_crit:
                    final_multiplier *= crit_mult
                
                damage = int(final_multiplier)
                self.energy = 0 
                
                # 执行伤害 (修改为AOE逻辑)
                # 【v39 修正】使用双引号，去掉外部感叹号
                print(f"   🌟 {self.name} 喊道: \"{ex_skill.quote}\"")
                print(f"   > 释放出覆盖全场的巨大电磁炮！")
                
                for target in alive_enemies:
                    result = target.take_damage(damage)
                    print(f"   > 对 {target.name} 造成 {result['final_dmg']} 点巨额伤害!")
                    if not target.is_alive():
                        # 获取倒地台词，如果没有则使用默认文本
                        death_msg = getattr(target, 'death_msg', f"{target.name} 倒下了...")
                        print(f"   💀 {target.name} 倒下了... \"{death_msg}\"")
                
                return {
                    "type": "alice_ex",
                    "msg": f"🌟 {self.name} 喊道: \"{ex_skill.quote}\"",
                    "damage": damage,
                    "is_crit": is_crit,
                    "target": potential_target
                }

        elif self.name == "柚子":
            # 柚子 AI (修复版：智能选择目标 + 射程检测 + 语音台词增强版 v32 + 台词修正 v35 + Quote 版 v36 & 修复重复台词版 v37 & 格式统一修复版)
            super_skill = get_skill("yuzu_super")
            normal_skill = get_skill("yuzu_normal")
            
            # 寻找射程内的敌人
            valid_targets = self._find_valid_targets(enemies, normal_skill.range)
            
            if not valid_targets:
                print(f"   ⚠️ {self.name} 发现周围没有射程内的敌人！")
                return {"type": "no_target", "msg": "没有目标"}

            # 优先攻击 HP 最低的
            target = min(valid_targets, key=lambda x: x.hp)
            
            if not self.has_used_super and random.random() < super_skill.chance:
                self.has_used_super = True
                # 检查大招射程
                valid_super_targets = self._find_valid_targets(enemies, super_skill.range)
                if valid_super_targets:
                    # 【v37 修复】不再手动打印喊话，因为 execute 内部已经处理了
                    # print(f"   🎮 {self.name} 喊道: '{super_skill.quote}'!")
                    
                    # 执行眩晕效果
                    logs = super_skill.execute(self, [target], {})
                    for log in logs:
                        print(log)
                    return {
                        "type": "super_attack",
                        # 【格式统一】改为双引号，去掉感叹号
                        "msg": f"🎮 {self.name} 喊道: \"{super_skill.name}\" 造成了眩晕！",
                        "effect": "stun"
                    }
            
            # 普通攻击
            # 【v37 修复】不再手动打印喊话，因为 execute 内部已经处理了
            # print(f"   🎮 {self.name} 喊道: '{normal_skill.quote}'!")
            
            logs = normal_skill.execute(self, [target], {})
            for log in logs:
                print(log)
            return {
                "type": "normal_attack",
                "msg": f"💥 {self.name} 进行普通攻击。造成 {self.atk} 点伤害！",
                "damage": self.atk
            }
                
        elif self.name == "小绿":
            # 小绿 AI (修复版：看全队血量 + 射程检测 + 台词修正 v35 + Quote 版 v36 & 格式统一修复版)
            # 检查是否有队友受伤
            injured_players = [p for p in party if p != self and p.hp < p.max_hp]
            
            if injured_players:
                # 有伤员，进行治疗
                heal_skill = get_skill("midori_heal")
                # 【格式统一】改为双引号，去掉感叹号
                print(f"   🎨 {self.name} 喊道: \"{heal_skill.quote}\"")
                
                # 治疗不需要目标列表，直接在 main.py 处理全队
                return {
                    "type": "heal",
                    "msg": f"🎨 {self.name} 发动【{heal_skill.name}】！画出了治愈的颜料！",
                    "amount": 25 # 默认治疗量
                }
            else:
                # 大家都满血，进行普通攻击
                valid_targets = self._find_valid_targets(enemies, get_skill('midori_normal').range)
                if valid_targets:
                    target = random.choice(valid_targets)
                    dmg = self.atk
                    result = target.take_damage(dmg)
                    # 【格式统一】改为双引号，去掉感叹号
                    print(f"   🎨 {self.name} 喊道: \"{get_skill('midori_normal').quote}\" 对 {target.name} 造成 {result['final_dmg']} 点伤害！")
                    return {
                        "type": "normal_attack",
                        "msg": f"🎨 {self.name} 进行了普通的画笔攻击。造成 {result['final_dmg']} 点伤害！",
                        "damage": result['final_dmg']
                    }
                else:
                    return {"type": "no_target", "msg": "没有目标"}
            
        elif self.name == "桃井":
            # 桃井 AI (修复版：真正的普通攻击 + 射程检测 + 语音台词增强版 v32 + 格式修正 v34 + 台词修正 v35 + Quote 版 v36 & 格式统一修复版)
            roll = random.random()
            
            # 查找射程内的敌人
            valid_targets = self._find_valid_targets(enemies, get_skill('momoi_normal').range)
            
            if not valid_targets:
                return {"type": "no_target", "msg": "没有目标"}

            if roll < 0.3:
                # 普通攻击 (修复版：真正造成伤害 + 标准格式 v34 + 台词修正 v35 + Quote 版 v36)
                target = random.choice(valid_targets)
                dmg = self.atk
                result = target.take_damage(dmg)
                # 【格式统一】改为双引号，去掉感叹号
                print(f"   📝 {self.name} 喊道: \"{get_skill('momoi_normal').quote}\" 对 {target.name} 造成 {result['final_dmg']} 点伤害！")
                return {
                    "type": "normal_attack",
                    "msg": f"📝 {self.name} 进行了普通的投掷攻击。造成 {result['final_dmg']} 点伤害！",
                    "damage": result['final_dmg']
                }
            elif roll < 0.6:
                # Debuff
                effect_type = random.choice(["attack_down", "defense_down"])
                skill_id = "momoi_debuff_atk" if effect_type == "attack_down" else "momoi_debuff_def"
                skill = get_skill(skill_id)
                
                # 【修复】增加打印语句
                # 【格式统一】改为双引号，去掉感叹号
                print(f"   📝 {self.name} 喊道: \"{skill.quote}\"")
                
                return {
                    "type": "plot_debuff",
                    # 【格式统一】改为双引号，去掉感叹号
                    "msg": f"📝 {self.name} 大喊：\"{skill.name}\"",
                    "effect": effect_type
                }
            else:
                # Buff
                effect_type = random.choice(["heal", "atk_up"])
                amount = random.randint(15, 25)
                if effect_type == "heal":
                     # 【修复】增加打印语句，引用 skill.py 中的技能
                     heal_skill = get_skill("momoi_heal")
                     # 【格式统一】改为双引号，去掉感叹号
                     print(f"   📝 {self.name} 喊道: \"{heal_skill.quote}\"")
                     
                     return {
                        "type": "plot_buff",
                        # 【格式统一】改为双引号，去掉感叹号
                        "msg": f"📝 {self.name} 大喊：\"{heal_skill.name}\"",
                        "effect": "heal",
                        "amount": amount
                    }
                else:
                    # Atk Up Buff
                    skill = get_skill("momoi_buff")
                    # 【修复】增加打印语句
                    # 【格式统一】改为双引号，去掉感叹号
                    print(f"   📝 {self.name} 喊道: \"{skill.quote}\"")
                    
                    return {
                        "type": "plot_buff",
                        # 【格式统一】改为双引号，去掉感叹号
                        "msg": f"📝 {self.name} 大喊：\"{skill.name}\"",
                        "effect": "atk_up",
                        "amount": int(self.atk * 0.2)
                    }
            
        else:
            # 默认普通攻击
            return {
                "type": "normal_attack",
                "msg": f"💥 {self.name} 进行普通攻击。造成 {self.atk} 点伤害！",
                "damage": self.atk
            }

# --- 数据常量 ---
PLAYERS_DATA = [
    {"name": "爱丽丝", "role": "勇者", "hp": 100, "atk": 50, "defense": 5, "skill": "光哟！！！" , "death_msg": "光... 熄灭了... 老师... 对不起..."},
    {"name": "桃井", "role": "编剧", "hp": 80, "atk": 40, "defense": 2, "skill": "剧情杀", "death_msg": "好不甘心啊——！剧本...怎么可以停在这里...大家...快逃啊..."},
    {"name": "小绿", "role": "原画", "hp": 120, "atk": 35, "defense": 10, "skill": "艺术润色", "death_msg": "画笔...断了...最后的颜色...是..."},
    {"name": "柚子", "role": "部长", "hp": 90, "atk": 45, "defense": 3, "skill": "通关指令", "death_msg": "Game...Over...但...爱丽丝...要赢..."},
]