# player.py
# 战斗模拟器 v44 - 玩家数据与行为逻辑模块 (全员能量化与高级状态版)
# 核心改进：
# 1. 【v43 新增】全员能量化：玩家也拥有 Energy 槽，可以积蓄能量释放大招。
# 2. 【v43 新增】高级状态抗性：完美支持处理 DoT、Blind (致盲)、Energy Block (阻断充能)。
# 3. 【v43 新增】爱丽丝 EX 技能升级：根据充能层数改变致盲效果强度和持续时间。
# 4. 【v43 新增】爱丽丝普攻升级：增加了 30% 几率的致盲效果。
# 5. 【v43.2 修复】移除了 EX 技能释放前的冗余手动打印，统一交由 skill 模块输出。
# 6. 【v44 修复】修正了爱丽丝普攻的技能 ID 引用错误，确保与 skill.py 中的注册表一致。
# 7. 【v44 紧急修复】修正了爱丽丝普攻 UI 显示的致盲概率描述错误 (从错误的 80% 修正为真实的 30%)。

import random
from skill import SKILL_REGISTRY, get_skill, AttackEffect, BuffEffect, DebuffEffect, StunEffect, HealEffect, ImmobilizeEffect, SequenceEffect, BlindEffect

class Player:
    def __init__(self, data):
        self.name = data["name"]
        self.role = data["role"]
        self.max_hp = data["hp"]
        self.hp = self.max_hp
        self.atk = data["atk"]
        self.defense = data["defense"]
        self.skill_name = data["skill"]
        
        # 新增：基础暴击率，供技能模块调用
        self.crit_rate = 0.1 
        
        # 【v43 新增】能量系统
        self.energy = 0 
        self.max_energy = 5
        
        self.has_used_super = False # 柚子专用：记录大招是否已使用
        self.is_stunned = False # 眩晕状态（无法行动）
        self.is_immobilized = False # 束缚状态（无法移动，但可以行动）
        self.is_blinded = False # 【v43 新增】致盲状态
        self.death_msg = data.get("death_msg", "") 
        
        # 【v22 新增】定位系统
        self.position = 0  

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
        # 1. 处理 DoT (持续伤害)
        for status in list(self.status_effects):
            if status["effect"] == "dot":
                dmg = status["value"]
                self.take_damage(dmg)
                print(f"   ☠️ {self.name} 受到了 {dmg} 点持续伤害！")

        # 2. 正常倒计时与清理
        for status in self.status_effects:
            status["duration"] -= 1
            
        self.status_effects = [s for s in self.status_effects if s["duration"] > 0]
        
        # 3. 重置临时状态标志
        has_immobilized = any(s["effect"] == "immobilized" for s in self.status_effects)
        if not has_immobilized:
            self.is_immobilized = False
            
        has_blinded = any(s["effect"] == "blind" for s in self.status_effects)
        if not has_blinded:
            self.is_blinded = False
            
        # 4. 应用数值修正
        for status in self.status_effects:
            if status["effect"] == "atk_up":
                self.atk = int(self.atk * (1 + status["value"]))
            elif status["effect"] == "defense_up":
                self.defense = self.defense + status["value"]
            elif status["effect"] == "atk_down":
                self.atk = int(self.atk * (1 - status["value"]))
            elif status["effect"] == "defense_down":
                self.defense = int(self.defense * (1 - status["value"]))

    def gain_energy(self, amount=1):
        """【v43 新增】获取能量，如果处于能量封锁状态则无效"""
        has_block = False
        for status in self.status_effects:
            if status["effect"] == "energy_block":
                has_block = True
                break
                
        if has_block:
            print(f"   🔋🚫 {self.name} 试图充能，但被阻断了！")
            return False
            
        self.energy = min(self.max_energy, self.energy + amount)
        return True

    def print_status(self):
        """打印状态信息：名字、血条、数值、状态图标、能量条"""
        bar_length = 20
        filled = int(self.hp / self.max_hp * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        status_str = ""
        if self.status_effects:
            icons = " ".join([s['icon'] for s in self.status_effects])
            status_str = f" {icons}"
        
        # 【v43 新增】能量条显示
        energy_bar = "⚡" * self.energy + "☆" * (self.max_energy - self.energy)
        
        print(f"   {self.name}: [{bar}] {self.hp}/{self.max_hp} [{energy_bar}]{status_str}")

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
        获取玩家行动 (高度模块化重构版 v44)
        """
        # 【v43 新增】检查是否处于致盲状态
        if self.is_blinded:
            print(f"   👁️❌ {self.name} 陷入了致盲状态！视野全黑，正在慌乱地原地踏步...")
            # 简单模拟一下乱撞（这里不做实际位置变动，只体现无法行动）
            return {"type": "blinded", "msg": f"{self.name} 无法看清战场，无法行动"}

        # 检查是否处于眩晕状态（无法行动）
        if self.is_stunned:
            print(f"   🕸️ {self.name} 被蛛网束缚住了！无法行动！")
            self.is_stunned = False 
            return {"type": "stunned", "msg": f"{self.name} 无法行动"}

        # 检查是否处于束缚状态（无法移动，但可以行动）
        if self.is_immobilized:
            print(f"   🕸️ {self.name} 被束缚住了！本回合无法移动，但可以正常行动！")

        if self.name == "爱丽丝":
            # === 交互逻辑：爱丽丝 ===
            alive_enemies = [m for m in enemies if m.is_alive()] if enemies else []
            
            if not alive_enemies:
                print("   ❌ 场上没有可攻击的目标！")
                return {"type": "no_target", "msg": "没有目标"}

            # 获取技能对象
            charge_skill = get_skill("alice_charge")
            ex_skill = get_skill("alice_ex")
            # 【v44 修复】修正技能 ID 为 "alice_physical"，与 skill.py 保持一致
            phys_skill = get_skill("alice_physical")

            # --- 电池样式能量槽 ---
            max_display = 10
            if self.energy > max_display:
                energy_bar = "[" + " ".join(["█"] * max_display) + "...]"
            else:
                total_cells = max(2, self.energy)
                cells = ["█" if i < self.energy else "░" for i in range(total_cells)]
                energy_bar = "[" + " ".join(cells) + "]"

            ex_targets = alive_enemies 
            phys_targets = self._find_valid_targets(enemies, phys_skill.range)
            
            ex_target_str = ", ".join([f"{e.name}[{e.position}]" for e in ex_targets]) if ex_targets else "无"
            phys_target_str = ", ".join([f"{t.name}[{t.position}]" for t in phys_targets]) if phys_targets else "无"

            immobilized_note = " (🕸️ 束缚中：无法移动)" if self.is_immobilized else ""
            print(f"\n   >> 爱丽丝，请做出你的行动！(能量: {energy_bar}){immobilized_note}")
            
            # [1] 普通攻击 (现在自带致盲特效)
            print(f"   [1] {phys_skill.name} [普通攻击]")
            # 【v44 紧急修复】修正这里的描述错误，从 80% 改为正确的 30%
            print(f"       说明: {phys_skill.desc} (附带 30% 几率致盲)")
            print(f"       射程: {phys_skill.range}")
            print(f"       可攻击目标: {phys_target_str}")
            
            # [2] 充能
            print(f"   [2] {charge_skill.name} [充能]")
            print(f"       说明: {charge_skill.desc}")
            print(f"       射程: N/A")

            # [3] EX技能 (现在会根据能量层数改变致盲持续时间)
            base_multiplier = ex_skill.multiplier
            energy_bonus = 0.5 
            stack_bonus = 1.0 + (self.energy * energy_bonus)
            final_multiplier = base_multiplier * stack_bonus
            
            # 【v43 新增】EX 技能的附加效果描述
            blind_desc = "致盲 1 回合"
            if self.energy >= 5:
                blind_desc = "致盲 2 回合 (高亮强化!)"
                
            ex_status = f" (倍率 x{final_multiplier:.2f}, {blind_desc})"
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
                            target_pos = int(parts[0])
                            skill_idx = int(parts[1])
                        except ValueError:
                            print("   ❌ 输入格式错误，请使用 '敌人位置-技能' 格式 (例如 4-1)")
                            continue
                    else:
                        try:
                            skill_idx = int(combined_input)
                            target_pos = None 
                        except ValueError:
                            print("   ❌ 输入无效，请输入数字")
                            continue

                    potential_target = None
                    if target_pos is not None:
                        for enemy in alive_enemies:
                            if enemy.position == target_pos:
                                potential_target = enemy
                                break
                        
                        if potential_target is None:
                            print(f"   ❌ 警告：第 {target_pos} 号位没有找到敌人！(可能是空位或队友)")
                            continue
                    else:
                        if alive_enemies:
                            potential_target = alive_enemies[0]
                        else:
                            potential_target = None
                    
                    # 检查射程
                    if skill_idx == 1: 
                        skill_range = phys_skill.range
                        if potential_target:
                            dist = abs(potential_target.position - self.position)
                            if dist > skill_range:
                                print(f"   ❌ 目标太远啦！射程只有 {skill_range}，距离是 {dist}！")
                                continue
                        
                    if skill_idx not in [1, 2, 3]:
                        print(f"   技能序号无效 (1-3)，默认执行普通攻击")
                        skill_idx = 1
                    
                    if skill_idx == 3 and self.energy < 2: 
                        print(f"   ❌ 能量不足！无法发动必杀技！(当前能量: {self.energy})")
                        print(f"   请重新输入指令。")
                        continue 
                    
                    break 

                except ValueError:
                    print("   输入格式错误，默认目标1，技能1 (普通攻击)")
                    potential_target = alive_enemies[0] if alive_enemies else None
                    skill_idx = 1
                    break

            # --- 执行技能 (统一移交 control 给 skill.py) ---
            
            if skill_idx == 1:
                # 物理攻击 (自带致盲的 SequenceEffect)
                logs = phys_skill.execute(self, [potential_target], {})
                for log in logs:
                    print(log)
                return {"type": "skill_module_handled", "msg": "Skill executed via module", "target": potential_target}
            
            elif skill_idx == 2:
                # 充能逻辑
                self.gain_energy(1)
                print(f"   ⚡ {self.name} 喊道: \"{charge_skill.quote}\" -> 能量充填层数 -> {self.energy}")
                return {
                    "type": "alice_charge",
                    "msg": f"⚡ {self.name} 喊道: \"{charge_skill.quote}\" -> 能量充填层数 -> {self.energy}"
                }
            
            else: # skill_idx == 3
                # 释放大招
                total_multiplier = base_multiplier * (1.0 + (self.energy * energy_bonus))
                
                # 【v43 新增】根据能量决定致盲时长
                blind_duration = 1
                if self.energy >= 5:
                    blind_duration = 2
                    
                # 构造参数包：传递致盲参数给 SequenceEffect 中的子技能
                params = {
                    'multiplier': total_multiplier, 
                    'crit_rate': 0.15,
                    'variance': 0,
                    'blind_duration': blind_duration, # 传递给 BlindEffect
                    'blind_chance': 0.6              # 传递给 BlindEffect
                }
                
                self.energy = 0
                
                # 创建一个专门用于 Alice EX 的 SequenceEffect 实例，以便动态注入参数
                # 注意：由于 Registry 里的实例是固定的，我们这里手动构建一个临时的 SequenceEffect
                # 或者直接在 params 里传参并在 SkillRegistry 里的 alice_ex 定义时处理好接收逻辑。
                # 为了兼容性，我们直接使用之前注册的 "alice_ex"，但它本身是个 AoEAttackEffect。
                # 所以我们需要在这里把它包装成一个 SequenceEffect 来执行。
                
                from skill import SequenceEffect, BlindEffect
                sequence_ex = SequenceEffect(
                    name="世界的法则即将崩坏！光哟！！！ (强化版)",
                    desc="全屏打击并致盲",
                    effects=[
                        ex_skill, # 注册表里的原始伤害技能
                        BlindEffect("强光致盲", "爱丽丝的光芒刺瞎了双眼", chance=0.6, duration=blind_duration, range=99)
                    ],
                    range=99
                )
                
                logs = sequence_ex.execute(self, alive_enemies, params)
                for log in logs:
                    print(log)
                
                return {
                    "type": "skill_module_handled",
                    "msg": "EX Skill executed via module",
                    "target": potential_target
                }

        elif self.name == "柚子":
            super_skill = get_skill("yuzu_super")
            normal_skill = get_skill("yuzu_normal")
            
            valid_targets = self._find_valid_targets(enemies, normal_skill.range)
            
            if not valid_targets:
                print(f"   ⚠️ {self.name} 发现周围没有射程内的敌人！")
                return {"type": "no_target", "msg": "没有目标"}

            target = min(valid_targets, key=lambda x: x.hp)
            
            if not self.has_used_super and random.random() < super_skill.chance:
                self.has_used_super = True
                # 检查大招射程
                valid_super_targets = self._find_valid_targets(enemies, super_skill.range)
                if valid_super_targets:
                    logs = super_skill.execute(self, [target], {})
                    for log in logs:
                        print(log)
                    return {
                        "type": "super_attack",
                        "msg": "Super executed via module",
                        "effect": "stun"
                    }
            
            # 普通攻击 -> 统一调用
            params = {'multiplier': 1.0, 'variance': 0, 'crit_rate': self.crit_rate}
            logs = normal_skill.execute(self, [target], params)
            for log in logs:
                print(log)
            return {
                "type": "normal_attack",
                "msg": "Normal attack executed via module",
                "target": target
            }
                
        elif self.name == "小绿":
            injured_players = [p for p in party if p != self and p.hp < p.max_hp]
            
            if injured_players:
                heal_skill = get_skill("midori_heal")
                # 治疗也交给 skill 模块处理
                logs = heal_skill.execute(self, injured_players, {})
                for log in logs:
                    print(log)
                return {"type": "skill_module_handled", "msg": "Heal executed via module"}
            else:
                valid_targets = self._find_valid_targets(enemies, get_skill('midori_normal').range)
                if valid_targets:
                    target = random.choice(valid_targets)
                    # 统一调用攻击
                    params = {'multiplier': 1.0, 'variance': 5, 'crit_rate': self.crit_rate}
                    logs = get_skill('midori_normal').execute(self, [target], params)
                    for log in logs:
                        print(log)
                    return {"type": "normal_attack", "msg": "Attacked via module", "target": target}
                else:
                    return {"type": "no_target", "msg": "没有目标"}
            
        elif self.name == "桃井":
            roll = random.random()
            valid_targets = self._find_valid_targets(enemies, get_skill('momoi_normal').range)
            
            if not valid_targets:
                return {"type": "no_target", "msg": "没有目标"}

            if roll < 0.3:
                target = random.choice(valid_targets)
                params = {'multiplier': 1.0, 'variance': 5, 'crit_rate': self.crit_rate}
                logs = get_skill('momoi_normal').execute(self, [target], params)
                for log in logs:
                    print(log)
                return {"type": "normal_attack", "msg": "Attacked via module", "target": target}
            elif roll < 0.6:
                effect_type = random.choice(["attack_down", "defense_down"])
                skill_id = "momoi_debuff_atk" if effect_type == "attack_down" else "momoi_debuff_def"
                skill = get_skill(skill_id)
                # 随机选择一个目标施加 Debuff
                target = random.choice(valid_targets)
                logs = skill.execute(self, [target], {})
                for log in logs:
                    print(log)
                return {"type": "skill_module_handled", "msg": "Debuff applied via module", "effect": effect_type}
            else:
                effect_type = random.choice(["heal", "atk_up"])
                amount = random.randint(15, 25)
                if effect_type == "heal":
                     heal_skill = get_skill("momoi_heal")
                     # 治疗自己
                     logs = heal_skill.execute(self, [self], {})
                     for log in logs:
                         print(log)
                     return {"type": "skill_module_handled", "msg": "Buffed via module", "effect": "heal", "amount": amount}
                else:
                    skill = get_skill("momoi_buff")
                    logs = skill.execute(self, [self], {})
                    for log in logs:
                        print(log)
                    return {"type": "skill_module_handled", "msg": "Buffed via module", "effect": "atk_up", "amount": int(self.atk * 0.2)}
            
        else:
            return {"type": "normal_attack", "msg": "Unknown character", "damage": self.atk}

# --- 数据常量 ---
PLAYERS_DATA = [
    {"name": "爱丽丝", "role": "勇者", "hp": 100, "atk": 50, "defense": 5, "skill": "光哟！！！" , "death_msg": "光... 熄灭了... 老师... 对不起..."},
    {"name": "桃井", "role": "编剧", "hp": 80, "atk": 40, "defense": 2, "skill": "剧情杀", "death_msg": "好不甘心啊——！剧本...怎么可以停在这里...大家...快逃啊..."},
    {"name": "小绿", "role": "原画", "hp": 120, "atk": 35, "defense": 10, "skill": "艺术润色", "death_msg": "画笔...断了...最后的颜色...是..."},
    {"name": "柚子", "role": "部长", "hp": 90, "atk": 45, "defense": 3, "skill": "通关指令", "death_msg": "Game...Over...但...爱丽丝...要赢..."},
]