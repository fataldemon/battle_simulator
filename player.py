# player.py
# 战斗模拟器 v13 - 玩家数据与行为逻辑模块 (含血条、增益图标、详细技能说明、交互优化)

import random
from skill import PLAYER_SKILLS_META

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
        actual_damage = max(1, damage - self.defense)
        actual_damage = int(actual_damage * random.uniform(0.9, 1.1))
        self.hp -= actual_damage
        if self.hp < 0:
            self.hp = 0
        return actual_damage

    def add_status_effect(self, icon, name, duration, effect_type, value=0):
        """添加状态效果"""
        # 检查是否已经存在相同类型的状态，如果存在则覆盖
        for i, status in enumerate(self.status_effects):
            if status["effect"] == effect_type:
                self.status_effects[i] = {"icon": icon, "name": name, "duration": duration, "effect": effect_type, "value": value}
                return
        self.status_effects.append({"icon": icon, "name": name, "duration": duration, "effect": effect_type, "value": value})

    def update_status_effects(self):
        """每回合结束时更新状态效果"""
        # 修改点：先减少持续时间
        for status in self.status_effects:
            status["duration"] -= 1
            
        # 移除过期状态
        self.status_effects = [s for s in self.status_effects if s["duration"] > 0]
        
        # 再应用效果
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
            # 提取图标，不带名称，直接拼接
            icons = " ".join([s['icon'] for s in self.status_effects])
            status_str = f" {icons}"
        
        print(f"   {self.name}: [{bar}] {self.hp}/{self.max_hp}{status_str}")

    def get_action(self, enemies=None):
        """
        获取玩家行动。
        """
        # 检查是否处于束缚状态
        if self.is_stunned:
            print(f"   🕸️ {self.name} 被蛛网束缚住了！无法行动！")
            self.is_stunned = False # 回合结束解除束缚
            return {"type": "stunned", "msg": f"{self.name} 无法行动"}

        if self.name == "爱丽丝":
            # === 交互逻辑：爱丽丝 ===
            # 新增：手动选择目标 & 技能合并输入
            
            alive_enemies = [m for m in enemies if m.is_alive()] if enemies else []
            
            if not alive_enemies:
                print("   ❌ 场上没有可攻击的目标！")
                return {"type": "no_target", "msg": "没有目标"}

            # 修改点：删除了这里打印目标血条的代码，防止刷屏
            # 统一由主循环在回合开始时打印状态
            
            # 打印技能列表 - v13 优化：显示技能可用性
            charge_desc = PLAYER_SKILLS_META["alice"]["charge"]["desc"]
            charge_detail = PLAYER_SKILLS_META["alice"]["charge"]["detail"]
            ex_desc = PLAYER_SKILLS_META["alice"]["ex"]["desc"]
            ex_detail = PLAYER_SKILLS_META["alice"]["ex"]["detail"]
            physical_desc = PLAYER_SKILLS_META["alice"]["physical"]["desc"]
            physical_detail = PLAYER_SKILLS_META["alice"]["physical"]["detail"]
            
            print(f"\n   >> 爱丽丝，请做出你的行动！(当前能量: {self.energy})")
            print(f"   [1] {charge_desc}")
            print(f"       说明: {charge_detail}")
            
            # v13 新增：检查大招能量是否足够
            ex_status = ""
            if self.energy < 2:
                ex_status = " (❌ 能量不足)"
            
            print(f"   [2] {ex_desc}{ex_status}")
            print(f"       说明: {ex_detail}")
            print(f"   [3] {physical_desc}")
            print(f"       说明: {physical_detail}")
            
            # v12 新增：优化输入提示排版
            print(f"\n   >>> 请输入指令：")
            print(f"   格式：目标序号-技能序号 (例如：1-2)")
            
            while True:
                try:
                    # 合并输入逻辑：格式为 "目标序号-技能序号"，例如 "1-2"
                    combined_input = input().strip()
                    
                    target_idx = 0 # 默认第一个
                    skill_idx = 1  # 默认充能
                    
                    if '-' in combined_input:
                        parts = combined_input.split('-')
                        target_idx = int(parts[0]) - 1
                        skill_idx = int(parts[1])
                    else:
                        # 兼容旧输入，如果只输入数字，视为技能序号，目标默认为第一个
                        skill_idx = int(combined_input)
                        target_idx = 0

                    # 验证目标
                    if 0 <= target_idx < len(alive_enemies):
                        self.selected_target = alive_enemies[target_idx]
                    else:
                        print(f"   目标序号无效 (1-{len(alive_enemies)})，默认攻击第一个目标")
                        self.selected_target = alive_enemies[0]
                    
                    # 验证技能
                    if skill_idx not in [1, 2, 3]:
                        print(f"   技能序号无效 (1-3)，默认执行充能")
                        skill_idx = 1
                    
                    # v13 新增：前置校验大招能量
                    if skill_idx == 2 and self.energy < 2:
                        print(f"   ❌ 能量不足！无法发动必杀技！(当前能量: {self.energy})")
                        print(f"   请重新输入指令。")
                        continue # 重新输入
                    
                    break # 输入合法，跳出循环

                except ValueError:
                    print("   输入格式错误，默认目标1，技能1 (充能)")
                    self.selected_target = alive_enemies[0]
                    skill_idx = 1
                    break

            # 根据 skill_idx 执行逻辑
            if skill_idx == 2:
                # 释放大招 (需要 2 层能量)
                # 从 skill.py 获取参数
                ex_meta = PLAYER_SKILLS_META["alice"]["ex"]
                base_multiplier = ex_meta.get("base_multiplier", 5.91)
                energy_bonus = ex_meta.get("energy_bonus", 0.5)
                crit_chance = ex_meta.get("crit_chance", 0.15)
                crit_multiplier = ex_meta.get("crit_multiplier", 2.0)

                base_dmg = self.atk * base_multiplier
                stack_bonus = 1.0 + (self.energy * energy_bonus)
                final_multiplier = base_dmg * stack_bonus
                
                is_crit = random.random() < crit_chance
                if is_crit:
                    final_multiplier *= crit_multiplier
                
                damage = int(final_multiplier)
                self.energy = 0 
                
                return {
                    "type": "alice_ex",
                    "msg": f"🌟 {self.name} 喊道: {ex_desc}",
                    "damage": damage,
                    "is_crit": is_crit,
                    "target": self.selected_target
                }
            
            elif skill_idx == 3:
                # 物理攻击
                # 从 skill.py 获取参数
                phys_meta = PLAYER_SKILLS_META["alice"]["physical"]
                variance = phys_meta.get("variance", 5)
                crit_chance = phys_meta.get("crit_chance", 0.1)
                crit_multiplier = phys_meta.get("crit_multiplier", 1.5)

                dmg_var = random.randint(self.atk - variance, self.atk + variance)
                if random.random() < crit_chance:
                    dmg_var = int(dmg_var * crit_multiplier)
                    return {
                        "type": "normal_attack",
                        "msg": f"✨ 爱丽丝物理攻击! 暴击! 造成 {dmg_var} 点伤害!",
                        "damage": dmg_var,
                        "target": self.selected_target
                    }
                else:
                    return {
                        "type": "normal_attack",
                        "msg": f"✨ 爱丽丝物理攻击! 造成 {dmg_var} 点伤害!",
                        "damage": dmg_var,
                        "target": self.selected_target
                    }
            
            else:
                # 充能逻辑
                # 从 skill.py 获取参数
                charge_meta = PLAYER_SKILLS_META["alice"]["charge"]
                gain = charge_meta.get("gain_energy", 1)
                self.energy += gain
                return {
                    "type": "alice_charge",
                    "msg": f"⚡ {self.name} 喊道: {charge_desc} -> 能量充填层数 -> {self.energy}"
                }

        elif self.name == "柚子":
            # 柚子 AI (加入了大招逻辑)
            # 从 skill.py 获取参数
            super_meta = PLAYER_SKILLS_META["yuzu"]["super"]
            stun_chance = super_meta.get("stun_chance", 0.4)
            
            # 如果还没用过且随机数命中，使用大招
            if not self.has_used_super and random.random() < stun_chance:
                self.has_used_super = True
                return {
                    "type": "super_attack",
                    "msg": f"🎮 {self.name} 喊道: '{super_meta['desc']}' 造成了眩晕！",
                    "effect": "stun"
                }
            else:
                # 普通攻击
                return {
                    "type": "normal_attack",
                    "msg": f"💥 {self.name} 进行普通攻击。造成 {self.atk} 点伤害！",
                    "damage": self.atk
                }
                
        elif self.name == "小绿":
            # 小绿 AI (治疗)
            # 从 skill.py 获取参数
            heal_meta = PLAYER_SKILLS_META["midori"]["heal"]
            min_heal = heal_meta.get("min_heal", 20)
            max_heal = heal_meta.get("max_heal", 30)
            
            heal_amount = random.randint(min_heal, max_heal)
            return {
                "type": "heal",
                "msg": f"🎨 {self.name} 发动【{heal_meta['desc']}】！画出了治愈的颜料！",
                "amount": heal_amount
            }
            
        elif self.name == "桃井":
            # 桃井 AI (盲盒模式：随机 Buff/Debuff/普攻)
            roll = random.random()
            
            if roll < 0.3:
                # 30% 概率：普通攻击
                return {
                    "type": "normal_attack",
                    "msg": f"📝 {self.name} 进行了普通的投掷攻击。造成 {self.atk} 点伤害！",
                    "damage": self.atk
                }
            elif roll < 0.6:
                # 30% 概率：给敌人上 Debuff
                effect_type = random.choice(["attack_down", "defense_down"])
                # 从 skill.py 获取描述
                debuff_desc = PLAYER_SKILLS_META["momoi"]["debuff"]["desc"]
                msg_map = {
                    "attack_down": "剧本里写着BOSS力气变小了！",
                    "defense_down": "剧本里写着BOSS的盔甲碎了！"
                }
                return {
                    "type": "plot_debuff",
                    "msg": f"📝 {self.name} 大喊：'{msg_map[effect_type]}'",
                    "effect": effect_type
                }
            else:
                # 40% 概率：给队友上 Buff
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
                        "amount": int(self.atk * 0.2) # 增加20%攻击力
                    }
            
        else:
            # 默认普通攻击
            return {
                "type": "normal_attack",
                "msg": f"💥 {name} 进行普通攻击。造成 {self.atk} 点伤害！",
                "damage": self.atk
            }

# --- 数据常量 ---
PLAYERS_DATA = [
    {"name": "爱丽丝", "role": "勇者", "hp": 100, "atk": 50, "defense": 5, "skill": "光哟！！！" , "death_msg": "光... 熄灭了... 老师... 对不起..."},
    {"name": "桃井", "role": "编剧", "hp": 80, "atk": 40, "defense": 2, "skill": "剧情杀", "death_msg": "剧本...还没写完...大家...要继续..."},
    {"name": "小绿", "role": "原画", "hp": 120, "atk": 35, "defense": 10, "skill": "艺术润色", "death_msg": "画笔...断了...最后的颜色...是..."},
    {"name": "柚子", "role": "部长", "hp": 90, "atk": 45, "defense": 3, "skill": "通关指令", "death_msg": "Game...Over...但...爱丽丝...要赢..."},
]