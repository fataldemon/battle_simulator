# monster.py
# 战斗模拟器 v12 - 怪物数据与行为逻辑模块 (含独特机制技能 + 完整防御系统 + 状态管理)

import random
from skill import MONSTER_SKILLS

# --- 技能效果定义 (已移至 skill.py) ---
# SKILLS = MONSTER_SKILLS 

class Monster:
    def __init__(self, data):
        self.name = data["name"]
        self.level = data["level"]
        self.max_hp = data["hp"]
        self.hp = self.max_hp
        self.base_atk = data["base_atk"]
        self.current_atk = self.base_atk
        
        # --- 新增：防御属性 ---
        self.base_defense = data.get("base_defense", 10) # 默认防御10
        self.defense = self.base_defense
        
        self.desc = data["desc"]
        self.quote = data["quote"]
        self.skill_type = data["skill_type"]
        
        # 自定义技能表
        self.custom_skills = data.get("skills_list", [])

        # 额外属性 (旧逻辑，保留兼容)
        self.defense_buff_turns = 0 # 防御Buff剩余回合
        self.attack_debuff_turns = 0
        self.reflect_turns = 0
        self.evade_next = False
        self.is_stunned = False 

        # v12.1 新增：状态列表 (Buff/Debuff)
        self.status_effects = []

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
            if status["effect"] == "atk_down":
                self.current_atk = int(self.base_atk * (1 - status["value"]))
            elif status["effect"] == "atk_up":
                self.current_atk = int(self.base_atk * (1 + status["value"]))
            elif status["effect"] == "defense_down":
                self.defense = int(self.base_defense * (1 - status["value"]))
            elif status["effect"] == "defense_up":
                self.defense = self.base_defense + status["value"]

    def get_available_skills(self):
        """根据怪物特性返回可用的技能池"""
        # 优先使用自定义技能表
        if self.custom_skills:
            return self.custom_skills
        
        # 如果没有自定义表，则沿用旧的通用逻辑
        skills = ["basic_attack"]
        if self.level >= 3:
            skills.append("heavy_strike")
        if self.level >= 5:
            skills.append("fireball")
        if self.level >= 4:
            skills.append("shield")
        if self.level >= 6:
            skills.append("cry")
        if self.level >= 8:
            skills.append("berserk")
            
        return skills

    def decide_action(self, party_members):
        """
        怪物AI：决定本回合行动
        """
        # 检查是否处于晕眩状态
        if self.is_stunned:
            print(f"💫 {self.name} 处于眩晕状态，无法行动！")
            self.is_stunned = False 
            return None 

        # 如果血量很低，优先尝试回血 (除非它是虚空吞噬者)
        if self.hp < self.max_hp * 0.3 and self.skill_type != "life_steal":
            heal_skill = MONSTER_SKILLS.get("heal")
            if heal_skill:
                heal_amount = int(self.max_hp * 0.2)
                self.hp = min(self.max_hp, self.hp + heal_amount)
                print(f"🧛‍♂️ {self.name} 使用了【自我治愈】，恢复了 {heal_amount} HP！")
                return None 

        # 随机选择技能
        available = self.get_available_skills()
        chosen_skill_key = random.choice(available)
        skill_info = MONSTER_SKILLS[chosen_skill_key]
        
        print(f"👹 {self.name} 发动了【{skill_info['desc']}】！")

        # 执行效果
        if skill_info["type"] == "damage":
            raw_dmg = int(self.current_atk * skill_info["multiplier"])
            actual_dmg = max(1, raw_dmg + random.randint(-5, 5))
            return {"type": "attack", "damage": actual_dmg, "target": None} 
            
        elif skill_info["type"] == "buff":
            if skill_info["stat"] == "defense":
                # --- 修改：真正增加防御力 ---
                buff_value = skill_info.get("value", 15)
                self.defense += buff_value
                self.defense_buff_turns = skill_info.get("duration", 2)
                print(f"🛡️ {self.name} 开启了护盾！(防御力提升了 {buff_value} 点)")
            elif skill_info["stat"] == "defense_reflect":
                # --- 修改：缩壳防御增加防御并反弹 ---
                buff_value = skill_info.get("value", 20)
                self.defense += buff_value
                self.reflect_turns = skill_info.get("duration", 2)
                self.defense_buff_turns = skill_info.get("duration", 2)
                print(f"🛡️ {self.name} 缩进了壳里！(防御力提升了 {buff_value} 点，并反弹伤害)")
            elif skill_info["stat"] == "evade_next":
                self.evade_next = True
                print(f"👻 {self.name} 融入了阴影！(即将闪避下一次攻击)")
            return None

        elif skill_info["type"] == "debuff":
            print(f"😱 {self.name} 发出了可怕的嚎叫！大家的攻击力下降了！")
            return {"type": "debuff_all_atk", "ratio": 0.8}
            
        elif skill_info["type"] == "debuff_all_stat":
            stat = skill_info["stat"]
            ratio = skill_info["ratio"]
            print(f"⚡ {self.name} 释放了电磁脉冲！{stat}降低了！")
            return {"type": f"debuff_all_{stat}", "ratio": ratio}

        elif skill_info["type"] == "special":
            if self.name == "铁皮傀儡":
                 self.hp = min(self.max_hp, self.hp + 20)
                 print(f"🔧 {self.name} 自我修复了20点HP！")
                 return None
            else:
                raw_dmg = int(self.current_atk * 1.5)
                return {"type": "attack", "damage": raw_dmg, "target": None}
                
        elif skill_info["type"] == "lifesteal":
            raw_dmg = int(self.current_atk * 1.5)
            actual_dmg = max(1, raw_dmg + random.randint(-5, 5))
            heal_amount = int(actual_dmg * skill_info["ratio"])
            self.hp = min(self.max_hp, self.hp + heal_amount)
            print(f"🩸 {self.name} 吸取了 {actual_dmg} 点生命，恢复了 {heal_amount} HP！")
            return {"type": "attack", "damage": actual_dmg, "target": None}

        elif skill_info["type"] == "crit_damage":
            roll = random.random()
            if roll < skill_info["chance"]:
                dmg = int(self.current_atk * skill_info["multiplier"])
                print(f"📐 {self.name} 进行了【精确计算】！造成了毁灭性打击！")
                return {"type": "attack", "damage": dmg, "target": None}
            else:
                dmg = int(self.current_atk * 1.0)
                return {"type": "attack", "damage": dmg, "target": None}
                
        elif skill_info["type"] == "trap":
            # 蛛网束缚：随机选择一个活着的玩家，使其下回合无法行动
            # 这里我们返回一个指令，让主循环去处理
            return {"type": "trap", "duration": skill_info["duration"]}

        elif skill_info["type"] == "aoe_damage":
            # 对全员造成伤害
            multiplier = skill_info["multiplier"]
            total_dmg = int(self.current_atk * multiplier)
            print(f"💥 {self.name} 的攻击波及了所有人！")
            return {"type": "aoe_attack", "total_damage": total_dmg}

        elif skill_info["type"] == "cleanse_enemy":
            # 视界崩坏：清除我方增益（这里简化为清除全队Buff，实际应该是清除我方Buff，但为了逻辑简单，我们先做成清除敌方Buff，或者反过来？）
            # 既然是Boss技能，通常是害人的。这里我们设计成：清除我方所有Buff（如果是友方视角），或者给玩家施加Debuff。
            # 修正：Boss技能通常是害人的。这里我们改成“混乱”或者“降低命中”。
            # 让我们改为：降低全队命中率（模拟空间扭曲）。
            return {"type": "debuff_all_hit", "ratio": 0.5}

        return None

    def apply_effects(self, effect):
        """应用怪物自身的状态变化"""
        if self.defense_buff_turns > 0:
            self.defense_buff_turns -= 1
        else:
            # --- 新增：回合结束，防御Buff失效，恢复基础防御 ---
            self.defense = self.base_defense # 修正拼写错误
            
        if self.reflect_turns > 0:
            self.reflect_turns -= 1
        if self.attack_debuff_turns > 0:
            self.attack_debuff_turns -= 1
        # evade_next 是一次性的，不在这里扣除，而是在受击时扣除

    def get_effective_atk(self):
        """获取实际攻击力"""
        atk = self.current_atk
        if self.attack_debuff_turns > 0:
            atk = int(atk * 0.8)
        return atk
    
    def take_damage(self, damage):
        """受到攻击时的处理"""
        reflect = 0
        
        # --- 修改：使用当前的防御力 ---
        final_dmg = max(1, damage - self.defense)
        self.hp -= final_dmg
        if self.hp < 0: self.hp = 0
        
        result = {"final_dmg": final_dmg}
        
        # 如果有反弹回合，触发反弹
        if self.reflect_turns > 0:
            # 反弹伤害可以基于防御力或者固定值，这里设定为10点
            result["reflect_dmg"] = 10 
            
        return result

    def is_alive(self):
        """判断是否存活"""
        return self.hp > 0

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

# --- 数据常量 ---
MONSTERS_DATA = [
    {
        "name": "黏糊糊史莱姆", "level": 1, "hp": 100, "base_atk": 10, "base_defense": 5,
        "desc": "软绵绵的家伙，虽然弱但是数量多！", "quote": "喵呜喵呜~", "skill_type": "gel_form",
        "skills_list": ["slime_bounce", "acid_spit", "heavy_strike"]
    },
    {
        "name": "哥布林斥候", "level": 2, "hp": 97, "base_atk": 17, "base_defense": 8,
        "desc": "拿着生锈斧头的小个子怪物，总是鬼鬼祟祟。", "quote": "呲！看这边！", "skill_type": "goblin_rage",
        "skills_list": ["heavy_strike", "throw_rock"]
    },
    {
        "name": "森林鹿", "level": 2, "hp": 80, "base_atk": 7, "base_defense": 3,
        "desc": "通常很温顺，但如果被激怒也会用角顶人。", "quote": "哞~", "skill_type": "horn_charge",
        "skills_list": ["horn_charge", "charge"]
    },
    {
        "name": "食人花", "level": 3, "hp": 145, "base_atk": 24, "base_defense": 10,
        "desc": "巨大的花朵，张开满是利齿的嘴巴等待猎物。", "quote": "啊呜！", "skill_type": "bite",
        "skills_list": ["vine_lash", "bite"]
    },
    {
        "name": "幽灵猫", "level": 4, "hp": 135, "base_atk": 21, "base_defense": 12,
        "desc": "半透明的猫咪，会发出让人毛骨悚然的叫声。", "quote": "喵呜~~~~", "skill_type": "phase_shift",
        "skills_list": ["scratch", "phase_shift", "cry"]
    },
    {
        "name": "巨型螃蟹", "level": 4, "hp": 247, "base_atk": 24, "base_defense": 30,
        "desc": "拥有坚硬甲壳的巨大生物，钳子能夹碎岩石。", "quote": "咔嚓咔嚓...咔嚓！", "skill_type": "hard_shell",
        "skills_list": ["crush_claw", "shell_defense"]
    },
    {
        "name": "铁皮傀儡", "level": 5, "hp": 204, "base_atk": 23, "base_defense": 25,
        "desc": "工程部制造的失败品？全身都是坚硬的装甲。", "quote": "哔哔... 警告... 故障...", "skill_type": "auto_repair",
        "skills_list": ["emp_hammer", "auto_repair", "emp_pulse"]
    },
    {
        "name": "暗影忍者", "level": 6, "hp": 181, "base_atk": 40, "base_defense": 15,
        "desc": "漆身漆黑的神秘战士，擅长暗杀。", "quote": "...!", "skill_type": "vanish",
        "skills_list": ["shadow_kick", "phase_shift", "cry"]
    },
    {
        "name": "机械蜘蛛", "level": 7, "hp": 292, "base_atk": 42, "base_defense": 20,
        "desc": "精密的机械构造体，腿上有锋利的刀刃。", "quote": "滴滴滴... 锁定目标...", "skill_type": "web_trap",
        "skills_list": ["acid_bite", "web_trap", "acid_spit"]
    },
    {
        "name": "石头巨人", "level": 8, "hp": 512, "base_atk": 51, "base_defense": 50,
        "desc": "由岩石构成的巨大生命体，防御力极高。", "quote": "轰隆隆...", "skill_type": "stone_skin",
        "skills_list": ["heavy_stomp", "earthquake", "throw_rock"]
    },
    {
        "name": "古代巨龙·炎", "level": 10, "hp": 500, "base_atk": 60, "base_defense": 40,
        "desc": "拥有极高火抗性的终极BOSS！", "quote": "吼——————！！！ ", "skill_type": "dragon_fury",
        "skills_list": ["dragon_wing_slap", "dragon_breath", "shield"]
    },
    {
        "name": "虚空吞噬者", "level": 11, "hp": 995, "base_atk": 80, "base_defense": 60,
        "desc": "来自深渊的终极Boss，所过之处一片虚无。", "quote": "吞噬... 一切...", "skill_type": "life_steal",
        "skills_list": ["abyssal_gaze", "life_steal", "void_collapse"]
    },
    {
        "name": "虚空吞噬者·终焉", "level": 12, "hp": 2500, "base_atk": 95, "base_defense": 80,
        "desc": "吸收了团队能量的强化版虚空吞噬者，正在不断恢复！", "quote": "吞噬... 你们的力量...", "skill_type": "life_steal",
        "skills_list": ["abyssal_gaze", "life_steal", "void_collapse", "shield", "void_collapse"]
    },
    {
        "name": "优香大魔王", "level": 99, "hp": 9999, "base_atk": 100, "base_defense": 100,
        "desc": "体重100kg的重装法师，计算精确到小数点后三位！", "quote": "按照计算，消失吧！", "skill_type": "calculation",
        "skills_list": ["red_pen_mark", "calculation", "high_speed_calculation", "shield"]
    }
]