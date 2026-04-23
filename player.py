# player.py
# 战斗模拟器 v14 - 玩家数据与行为逻辑模块 (模块化重构版)

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

    def get_action(self, enemies=None):
        """
        获取玩家行动 (模块化版)
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

            print(f"\n   >> 爱丽丝，请做出你的行动！(当前能量: {self.energy})")
            print(f"   [1] {charge_skill.name}")
            print(f"       说明: {charge_skill.desc}")
            
            ex_status = ""
            if self.energy < 2:
                ex_status = " (❌ 能量不足)"
            
            print(f"   [2] {ex_skill.name}{ex_status}")
            print(f"       说明: {ex_skill.desc}")
            print(f"   [3] {phys_skill.name}")
            print(f"       说明: {phys_skill.desc}")
            
            print(f"\n   >>> 请输入指令：")
            print(f"   格式：目标序号-技能序号 (例如：1-2)")
            
            while True:
                try:
                    combined_input = input().strip()
                    target_idx = 0 
                    skill_idx = 1  
                    
                    if '-' in combined_input:
                        parts = combined_input.split('-')
                        target_idx = int(parts[0]) - 1
                        skill_idx = int(parts[1])
                    else:
                        skill_idx = int(combined_input)
                        target_idx = 0

                    if 0 <= target_idx < len(alive_enemies):
                        self.selected_target = alive_enemies[target_idx]
                    else:
                        print(f"   目标序号无效 (1-{len(alive_enemies)})，默认攻击第一个目标")
                        self.selected_target = alive_enemies[0]
                    
                    if skill_idx not in [1, 2, 3]:
                        print(f"   技能序号无效 (1-3)，默认执行充能")
                        skill_idx = 1
                    
                    if skill_idx == 2 and self.energy < 2:
                        print(f"   ❌ 能量不足！无法发动必杀技！(当前能量: {self.energy})")
                        print(f"   请重新输入指令。")
                        continue 
                    
                    break 

                except ValueError:
                    print("   输入格式错误，默认目标1，技能1 (充能)")
                    self.selected_target = alive_enemies[0]
                    skill_idx = 1
                    break

            # 执行技能
            if skill_idx == 2:
                # 释放大招 (特殊逻辑：消耗能量并增加伤害)
                # 为了保持模块化，我们尽量复用 AttackEffect 的描述，但计算逻辑需要单独处理
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
                
                # 执行伤害
                result = self.selected_target.take_damage(damage)
                print(f"   🌟 {self.name} 喊道: {ex_skill.name}!")
                print(f"   > 对 {self.selected_target.name} 造成 {result['final_dmg']} 点巨额伤害!")
                if not self.selected_target.is_alive():
                    print(f"   💀 {self.selected_target.name} 倒下了...")
                
                return {
                    "type": "alice_ex",
                    "msg": f"🌟 {self.name} 喊道: {ex_skill.name}",
                    "damage": damage,
                    "is_crit": is_crit,
                    "target": self.selected_target
                }
            
            elif skill_idx == 3:
                # 物理攻击
                # 复用 AttackEffect 逻辑
                dmg = int(random.randint(self.atk - 5, self.atk + 5))
                if random.random() < 0.1:
                    dmg = int(dmg * 1.5)
                    return {"type": "normal_attack", "msg": f"✨ 爱丽丝物理攻击! 暴击! 造成 {dmg} 点伤害!", "damage": dmg, "target": self.selected_target}
                else:
                    return {"type": "normal_attack", "msg": f"✨ 爱丽丝物理攻击! 造成 {dmg} 点伤害!", "damage": dmg, "target": self.selected_target}
            
            else:
                # 充能逻辑
                self.energy += 1
                return {
                    "type": "alice_charge",
                    "msg": f"⚡ {self.name} 喊道: {charge_skill.name} -> 能量充填层数 -> {self.energy}"
                }

        elif self.name == "柚子":
            # 柚子 AI
            super_skill = get_skill("yuzu_super")
            normal_skill = get_skill("yuzu_normal")
            
            if not self.has_used_super and random.random() < super_skill.chance:
                self.has_used_super = True
                # 执行眩晕效果
                target = random.choice([m for m in enemies if m.is_alive()]) if enemies else None
                if target:
                    logs = super_skill.execute(self, [target], {})
                    for log in logs:
                        print(log)
                return {
                    "type": "super_attack",
                    "msg": f"🎮 {self.name} 喊道: '{super_skill.name}' 造成了眩晕！",
                    "effect": "stun"
                }
            else:
                # 普通攻击
                target = random.choice([m for m in enemies if m.is_alive()]) if enemies else None
                if target:
                    logs = normal_skill.execute(self, [target], {})
                    for log in logs:
                        print(log)
                return {
                    "type": "normal_attack",
                    "msg": f"💥 {self.name} 进行普通攻击。造成 {self.atk} 点伤害！",
                    "damage": self.atk
                }
                
        elif self.name == "小绿":
            # 小绿 AI
            heal_skill = get_skill("midori_heal")
            # 治疗不需要目标列表，直接在 main.py 处理全队
            return {
                "type": "heal",
                "msg": f"🎨 {self.name} 发动【{heal_skill.name}】！画出了治愈的颜料！",
                "amount": 25 # 默认治疗量
            }
            
        elif self.name == "桃井":
            # 桃井 AI
            roll = random.random()
            
            if roll < 0.3:
                # 普通攻击
                return {
                    "type": "normal_attack",
                    "msg": f"📝 {self.name} 进行了普通的投掷攻击。造成 {self.atk} 点伤害！",
                    "damage": self.atk
                }
            elif roll < 0.6:
                # Debuff
                effect_type = random.choice(["attack_down", "defense_down"])
                skill_id = "momoi_debuff_atk" if effect_type == "attack_down" else "momoi_debuff_def"
                skill = get_skill(skill_id)
                return {
                    "type": "plot_debuff",
                    "msg": f"📝 {self.name} 大喊：'{skill.name}'",
                    "effect": effect_type
                }
            else:
                # Buff
                effect_type = random.choice(["heal", "atk_up"])
                amount = random.randint(15, 25)
                if effect_type == "heal":
                     return {
                        "type": "plot_buff",
                        "msg": f"📝 {self.name} 大喊：'剧本里写着大家充满了活力！'",
                        "effect": "heal",
                        "amount": amount
                    }
                else:
                    return {
                        "type": "plot_buff",
                        "msg": f"📝 {self.name} 大喊：'剧本里写着大家获得了力量的加持！'",
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
    {"name": "桃井", "role": "编剧", "hp": 80, "atk": 40, "defense": 2, "skill": "剧情杀", "death_msg": "剧本...还没写完...大家...要继续..."},
    {"name": "小绿", "role": "原画", "hp": 120, "atk": 35, "defense": 10, "skill": "艺术润色", "death_msg": "画笔...断了...最后的颜色...是..."},
    {"name": "柚子", "role": "部长", "hp": 90, "atk": 45, "defense": 3, "skill": "通关指令", "death_msg": "Game...Over...但...爱丽丝...要赢..."},
]