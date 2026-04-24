# player.py
# 战斗模拟器 v19 - 玩家数据与行为逻辑模块 (全员台词人设强化版)

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

    def get_action(self, enemies=None, party=None):
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

            print(f"\n   >> 爱丽丝，请做出你的行动！(能量: {energy_bar})")
            print(f"   [1] {charge_skill.name}")
            print(f"       说明: {charge_skill.desc}")
            
            # 计算大招倍率
            base_multiplier = ex_skill.multiplier
            energy_bonus = 0.5 
            stack_bonus = 1.0 + (self.energy * energy_bonus)
            final_multiplier = base_multiplier * stack_bonus
            
            ex_status = f" (倍率 x{final_multiplier:.2f})"
            if self.energy < 2:
                ex_status += " (❌ 能量不足)"
            
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
                
                # 执行伤害 (修改为AOE逻辑)
                print(f"   🌟 {self.name} 喊道: {ex_skill.name}!")
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
                    "msg": f"🌟 {self.name} 喊道: {ex_skill.name}",
                    "damage": damage,
                    "is_crit": is_crit,
                    "target": self.selected_target
                }
            
            elif skill_idx == 3:
                # 物理攻击 (修复版：真正造成伤害)
                dmg = int(random.randint(self.atk - 5, self.atk + 5))
                
                # 【修复】真正调用 take_damage 进行伤害结算
                result = self.selected_target.take_damage(dmg)
                actual_dmg = result['final_dmg']
                
                # 暴击判定
                is_crit = random.random() < 0.1
                if is_crit:
                    actual_dmg = int(actual_dmg * 1.5)
                    msg = f"✨ 爱丽丝物理攻击! 暴击! 造成 {actual_dmg} 点伤害!"
                else:
                    msg = f"✨ 爱丽丝物理攻击! 造成 {actual_dmg} 点伤害!"
                
                print(f"   🗡️ {self.name} 喊道: {phys_skill.name}! {phys_skill.desc}")
                print(f"   > {msg}")
                
                return {"type": "normal_attack", "msg": msg, "damage": actual_dmg, "target": self.selected_target}
            
            else:
                # 充能逻辑
                self.energy += 1
                # 【修复】增加打印语句
                print(f"   ⚡ {self.name} 喊道: {charge_skill.name}! {charge_skill.desc}")
                return {
                    "type": "alice_charge",
                    "msg": f"⚡ {self.name} 喊道: {charge_skill.name} -> 能量充填层数 -> {self.energy}"
                }

        elif self.name == "柚子":
            # 柚子 AI (修复版：智能选择目标)
            super_skill = get_skill("yuzu_super")
            normal_skill = get_skill("yuzu_normal")
            
            alive_enemies = [m for m in enemies if m.is_alive()]
            if not alive_enemies:
                return {"type": "no_target", "msg": "没有目标"}

            # 寻找 HP 最低（威胁最大/最需要控制）的敌人
            target = min(alive_enemies, key=lambda x: x.hp)
            
            if not self.has_used_super and random.random() < super_skill.chance:
                self.has_used_super = True
                # 执行眩晕效果
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
                logs = normal_skill.execute(self, [target], {})
                for log in logs:
                    print(log)
                return {
                    "type": "normal_attack",
                    "msg": f"💥 {self.name} 进行普通攻击。造成 {self.atk} 点伤害！",
                    "damage": self.atk
                }
                
        elif self.name == "小绿":
            # 小绿 AI (修复版：看全队血量)
            # 检查是否有队友受伤
            injured_players = [p for p in party if p != self and p.hp < p.max_hp]
            
            if injured_players:
                # 有伤员，进行治疗
                heal_skill = get_skill("midori_heal")
                print(f"   🎨 {self.name} 喊道: {heal_skill.name}! {heal_skill.desc}")
                
                # 治疗不需要目标列表，直接在 main.py 处理全队
                return {
                    "type": "heal",
                    "msg": f"🎨 {self.name} 发动【{heal_skill.name}】！画出了治愈的颜料！",
                    "amount": 25 # 默认治疗量
                }
            else:
                # 大家都满血，进行普通攻击
                alive_enemies = [m for m in enemies if m.is_alive()]
                if alive_enemies:
                    target = random.choice(alive_enemies)
                    dmg = self.atk
                    result = target.take_damage(dmg)
                    # 【v19 更新】使用新的台词
                    print(f"   🎨 {self.name} 喊道: {get_skill('midori_normal').name}! 造成 {result['final_dmg']} 点伤害！")
                    return {
                        "type": "normal_attack",
                        "msg": f"🎨 {self.name} 进行了普通的画笔攻击。造成 {result['final_dmg']} 点伤害！",
                        "damage": result['final_dmg']
                    }
                else:
                    return {"type": "no_target", "msg": "没有目标"}
            
        elif self.name == "桃井":
            # 桃井 AI (修复版：真正的普通攻击)
            roll = random.random()
            alive_enemies = [m for m in enemies if m.is_alive()]
            if not alive_enemies:
                return {"type": "no_target", "msg": "没有目标"}

            if roll < 0.3:
                # 普通攻击 (修复版：真正造成伤害)
                target = random.choice(alive_enemies)
                dmg = self.atk
                result = target.take_damage(dmg)
                # 【v19 更新】使用新的台词
                print(f"   📝 {self.name} 喊道: {get_skill('momoi_normal').name}! 造成 {result['final_dmg']} 点伤害！")
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
                print(f"   📝 {self.name} 喊道: {skill.name}! {skill.desc}")
                
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
                     # 【修复】增加打印语句，引用 skill.py 中的技能
                     heal_skill = get_skill("momoi_heal")
                     print(f"   📝 {self.name} 喊道: {heal_skill.name}! {heal_skill.desc}")
                     
                     return {
                        "type": "plot_buff",
                        "msg": f"📝 {self.name} 大喊：'{heal_skill.name}'",
                        "effect": "heal",
                        "amount": amount
                    }
                else:
                    # Atk Up Buff
                    skill = get_skill("momoi_buff")
                    # 【修复】增加打印语句
                    print(f"   📝 {self.name} 喊道: {skill.name}! {skill.desc}")
                    
                    return {
                        "type": "plot_buff",
                        "msg": f"📝 {self.name} 大喊：'{skill.name}'",
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