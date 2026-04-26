# monster.py
# 战斗模拟器 v25 - 怪物数据与行为逻辑模块 (含智能索敌与追击攻击版)
# 核心改进：
# 1. Debuff/Trap 技能优先选择未受影响的目标。若无目标则切换为攻击技能。
# 2. 怪物在无法攻击时移动后，会在同一回合尝试再次攻击。
# 3. 怪物可以一次性移动到目标位置，而不是每次只移动一格。

import random
# 导入所有需要用到的技能效果类
from skill import SKILL_REGISTRY, get_skill, AttackEffect, BuffEffect, DebuffEffect, TrapEffect, SelfHealEffect, LifestealEffect, HealEffect, StunEffect, CleanseEffect

class Monster:
    def __init__(self, data):
        self.name = data["name"]
        self.level = data["level"]
        self.max_hp = data["hp"]
        self.hp = self.max_hp
        self.base_atk = data["base_atk"]
        self.current_atk = self.base_atk
        self.atk = self.base_atk  # 兼容技能模块
        
        # --- 防御属性 ---
        self.base_defense = data.get("base_defense", 10)
        self.defense = self.base_defense
        
        self.desc = data["desc"]
        self.quote = data["quote"]
        self.skill_type = data["skill_type"]
        
        # 自定义技能表 (引用 skill.py 中的技能ID)
        self.custom_skills = data.get("skills_list", [])

        # 额外属性 (旧逻辑，保留兼容)
        self.defense_buff_turns = 0
        self.attack_debuff_turns = 0
        self.reflect_turns = 0
        self.evade_next = False
        self.is_stunned = False 
        
        # 【v22 新增】定位系统
        self.position = 0  # 初始位置默认为 0，将在游戏初始化时重新分配

        # v12 新增：状态列表 (Buff/Debuff)
        self.status_effects = []

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
            if status["effect"] == "atk_down":
                self.current_atk = int(self.base_atk * (1 - status["value"]))
                self.atk = self.current_atk  # 同步更新 atk
            elif status["effect"] == "atk_up":
                self.current_atk = int(self.base_atk * (1 + status["value"]))
                self.atk = self.current_atk  # 同步更新 atk
            elif status["effect"] == "defense_down":
                self.defense = int(self.base_defense * (1 - status["value"]))
            elif status["effect"] == "defense_up":
                self.defense = self.base_defense + status["value"]

    def _find_valid_targets(self, targets, skill_range, exclude_effect_type=None):
        """
        【v24 新增】根据射程寻找有效目标，并支持排除特定状态效果的目标
        :param exclude_effect_type: 字符串，如 "immobilized" 或 "atk_down"。如果目标有此状态，则不被选为目标。
        """
        valid_targets = []
        for target in targets:
            if target.is_alive():
                distance = abs(target.position - self.position)
                if distance <= skill_range:
                    # 如果需要排除特定状态，检查目标是否已有该状态
                    if exclude_effect_type:
                        has_status = False
                        for status in target.status_effects:
                            if status['effect'] == exclude_effect_type:
                                has_status = True
                                break
                        
                        # 特殊处理：Stun 是独立属性，不在 status_effects 列表中
                        if exclude_effect_type == "stunned" and getattr(target, 'is_stunned', False):
                            has_status = True

                        if has_status:
                            continue
                    
                    valid_targets.append(target)
        return valid_targets

    def get_available_skills(self):
        """根据怪物特性返回可用的技能ID列表"""
        # 优先使用自定义技能表
        if self.custom_skills:
            return self.custom_skills
        
        # 如果没有自定义表，则沿用旧的通用逻辑 (生成技能ID)
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

    def _move_towards_target(self, party_members, target_position=None):
        """
        【v25 新增】追击逻辑：向最近的敌人移动，或者直接移动到指定位置
        """
        alive_players = [p for p in party_members if p.is_alive()]
        if not alive_players:
            return False

        # 如果没有指定目标位置，则寻找距离最近的目标
        if target_position is None:
            nearest_player = min(alive_players, key=lambda p: abs(p.position - self.position))
            target_position = nearest_player.position
        
        # 记录旧位置用于打印
        old_pos = self.position
        
        # 计算需要移动的步数和方向
        distance = target_position - self.position
        steps = distance // 1  # 向下取整，确保不超过目标位置
        
        # 限制最大移动步数（假设怪物最多移动5格，可以根据需要调整）
        max_move_steps = 5
        if abs(steps) > max_move_steps:
            steps = max_move_steps if steps > 0 else -max_move_steps
            
        self.position += steps
        
        print(f"   👹 {self.name} 发现无法攻击，决定向目标逼近！(从 {old_pos} 移动到 {self.position})")
        return True

    def decide_action(self, party_members):
        """
        怪物AI：决定本回合行动 (模块化版 + 智能索敌 + 追击攻击 v25)
        """
        # 检查是否处于晕眩状态
        if self.is_stunned:
            print(f"💫 {self.name} 处于眩晕状态，无法行动！")
            self.is_stunned = False 
            return None 

        # 如果血量很低，优先尝试回血 (除非它是虚空吞噬者)
        if self.hp < self.max_hp * 0.3 and self.skill_type != "life_steal":
            # 尝试使用自我修复技能
            if "auto_repair" in self.get_available_skills():
                skill = get_skill("auto_repair")
                logs = skill.execute(self, [], {})
                for log in logs:
                    print(log)
                return None 

        # 随机选择技能ID
        available_skill_ids = self.get_available_skills()
        chosen_skill_id = random.choice(available_skill_ids)
        skill = get_skill(chosen_skill_id)
        
        if not skill:
            print(f"👹 {self.name} 发动了【未知技能】！")
            return None

        print(f"👹 {self.name} 发动了【{skill.name}】！")

        # 执行技能效果
        logs = []
        targets = []
        needs_external_target = False

        # 根据技能类型确定索敌策略
        if isinstance(skill, AttackEffect):
            needs_external_target = True
            is_aoe = skill.name in ["地震术", "龙息吐息"] 
            
            if is_aoe:
                targets = [p for p in party_members if p.is_alive()]
            else:
                # 普通攻击直接索敌
                targets = self._find_valid_targets(party_members, skill.range)

        elif isinstance(skill, BuffEffect):
            # 增益技能 (对自己)，不需要外部目标
            targets = [self]
            
        elif isinstance(skill, DebuffEffect):
            needs_external_target = True
            # 优先选择没有该 Debuff 的目标
            exclude_type = f"{skill.stat}_down"
            targets = self._find_valid_targets(party_members, skill.range, exclude_effect_type=exclude_type)
            
        elif isinstance(skill, TrapEffect):
            needs_external_target = True
            # 优先选择没有被束缚的目标
            targets = self._find_valid_targets(party_members, skill.range, exclude_effect_type="immobilized")
            
        elif isinstance(skill, StunEffect):
            needs_external_target = True
            # 优先选择没有眩晕的目标
            targets = self._find_valid_targets(party_members, skill.range, exclude_effect_type="stunned")

        elif isinstance(skill, CleanseEffect):
            needs_external_target = True
            targets = self._find_valid_targets(party_members, skill.range)
            
        elif isinstance(skill, LifestealEffect):
            needs_external_target = True
            targets = self._find_valid_targets(party_members, skill.range)
            
        elif isinstance(skill, SelfHealEffect):
            # 自我恢复，不需要外部目标
            pass
            
        else:
            # 其他未知技能
            logs.append(f"   {self.name} 使用了特殊技能！")

        # 【v25 核心逻辑】如果找不到目标，尝试移动后再试一次
        if needs_external_target and not targets:
            # 如果是 Debuff/Trap/Stun 等控制技能，且没有符合条件的目标，则切换为攻击技能
            if isinstance(skill, (DebuffEffect, TrapEffect, StunEffect)):
                print(f"   ⚠️ {self.name} 发现没有合适的目标施加【{skill.name}】，切换为普通攻击！")
                skill = get_skill("basic_attack")
                targets = self._find_valid_targets(party_members, skill.range)
            
            # 如果还是没有目标，则移动后再试一次
            if not targets:
                self._move_towards_target(party_members)
                
                # 移动后重新索敌
                if isinstance(skill, AttackEffect) and skill.name not in ["地震术", "龙息吐息"]:
                    targets = self._find_valid_targets(party_members, skill.range)
                elif isinstance(skill, DebuffEffect):
                    targets = self._find_valid_targets(party_members, skill.range, exclude_effect_type=f"{skill.stat}_down")
                elif isinstance(skill, TrapEffect):
                    targets = self._find_valid_targets(party_members, skill.range, exclude_effect_type="immobilized")
                elif isinstance(skill, StunEffect):
                    targets = self._find_valid_targets(party_members, skill.range, exclude_effect_type="stunned")
                elif isinstance(skill, CleanseEffect):
                    targets = self._find_valid_targets(party_members, skill.range)
                elif isinstance(skill, LifestealEffect):
                    targets = self._find_valid_targets(party_members, skill.range)

        # 执行技能
        if needs_external_target:
            if targets:
                # 对于单体技能，从有效目标中随机选一个；对于群体技能（如AOE或某些Debuff），可能作用于多个
                # 目前大部分非AOE技能在 execute 里都假设 targets 列表里的都要处理，或者取第一个
                
                if isinstance(skill, AttackEffect) and not skill.is_aoe:
                    # 单体攻击只打一个
                    target = random.choice(targets)
                    logs = skill.execute(self, [target], {})
                elif isinstance(skill, LifestealEffect):
                    # 吸血只吸一个
                    target = random.choice(targets)
                    logs = skill.execute(self, [target], {})
                else:
                    # AOE 或其他群体效果
                    logs = skill.execute(self, targets, {})
            else:
                logs.append(f"   ❌ {self.name} 即使移动后也无法攻击到目标！")
        else:
            # 自我技能
            if isinstance(skill, BuffEffect):
                logs = skill.execute(self, [self], {})
            elif isinstance(skill, SelfHealEffect):
                logs = skill.execute(self, [], {})

        # 打印日志
        for log in logs:
            print(log)
            
        return None

    def take_damage(self, damage):
        """受到攻击时的处理"""
        reflect = 0
        
        final_dmg = max(1, damage - self.defense)
        self.hp -= final_dmg
        if self.hp < 0: self.hp = 0
        
        result = {"final_dmg": final_dmg}
        
        if self.reflect_turns > 0:
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
        
        # 【v21 修复】增加状态图标显示逻辑，与 Player 保持一致
        status_str = ""
        if self.status_effects:
            icons = " ".join([s['icon'] for s in self.status_effects])
            status_str = f" {icons}"
        
        print(f"   {self.name}: [{bar}] {self.hp}/{self.max_hp}{status_str}")

# --- 数据常量 ---
MONSTERS_DATA = [
    {
        "name": "黏糊糊史莱姆", "level": 1, "hp": 100, "base_atk": 10, "base_defense": 5,
        "desc": "软绵绵的家伙，虽然弱但是数量多！", "quote": "喵呜喵呜~", "skill_type": "gel_form",
        "skills_list": ["slime_bounce", "acid_spit"]
    },
    {
        "name": "哥布林斥候", "level": 2, "hp": 97, "base_atk": 17, "base_defense": 8,
        "desc": "拿着生锈斧头的小个子怪物，总是鬼鬼祟祟。", "quote": "呲！看这边！", "skill_type": "goblin_rage",
        "skills_list": ["throw_rock", "scratch"]
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
        "skills_list": ["phase_shift", "scratch"]
    },
    {
        "name": "巨型螃蟹", "level": 4, "hp": 247, "base_atk": 24, "base_defense": 30,
        "desc": "拥有坚硬甲壳的巨大生物，钳子能夹碎岩石。", "quote": "咔嚓咔嚓...咔嚓！", "skill_type": "hard_shell",
        "skills_list": ["crush_claw", "shell_defense"]
    },
    {
        "name": "铁皮傀儡", "level": 5, "hp": 204, "base_atk": 23, "base_defense": 25,
        "desc": "工程部制造的失败品？全身都是坚硬的装甲。", "quote": "哔哔... 警告... 故障...", "skill_type": "auto_repair",
        "skills_list": ["emp_hammer", "auto_repair"]
    },
    {
        "name": "暗影忍者", "level": 6, "hp": 181, "base_atk": 40, "base_defense": 15,
        "desc": "漆身漆黑的神秘战士，擅长暗杀。", "quote": "...!", "skill_type": "vanish",
        "skills_list": ["shadow_kick", "cry"]
    },
    {
        "name": "机械蜘蛛", "level": 7, "hp": 292, "base_atk": 42, "base_defense": 20,
        "desc": "精密的机械构造体，腿上有锋利的刀刃。", "quote": "滴滴滴... 锁定目标...", "skill_type": "web_trap",
        "skills_list": ["web_trap", "acid_bite"]
    },
    {
        "name": "石头巨人", "level": 8, "hp": 512, "base_atk": 51, "base_defense": 50,
        "desc": "由岩石构成的巨大生命体，防御力极高。", "quote": "轰隆隆...", "skill_type": "stone_skin",
        "skills_list": ["heavy_stomp", "shield"]
    },
    {
        "name": "古代巨龙·炎", "level": 10, "hp": 500, "base_atk": 60, "base_defense": 40,
        "desc": "拥有极高火抗性的终极BOSS！", "quote": "吼——————！！！ ", "skill_type": "dragon_fury",
        "skills_list": ["dragon_wing_slap", "dragon_breath", "shield"]
    },
    {
        "name": "虚空吞噬者", "level": 11, "hp": 995, "base_atk": 80, "base_defense": 60,
        "desc": "来自深渊的终极Boss，所过之处一片虚无。", "quote": "吞噬... 一切...", "skill_type": "life_steal",
        "skills_list": ["void_collapse", "abyssal_gaze", "life_steal"]
    },
    {
        "name": "虚空吞噬者·终焉", "level": 12, "hp": 2500, "base_atk": 95, "base_defense": 80,
        "desc": "吸收了团队能量的强化版虚空吞噬者，正在不断恢复！", "quote": "吞噬... 你们的力量...", "skill_type": "life_steal",
        "skills_list": ["void_collapse", "abyssal_gaze", "life_steal", "shield"]
    },
    {
        "name": "优香大魔王", "level": 99, "hp": 9999, "base_atk": 100, "base_defense": 100,
        "desc": "体重100kg的重装法师，计算精确到小数点后三位！", "quote": "按照计算，消失吧！", "skill_type": "calculation",
        "skills_list": ["calculation", "high_speed_calculation", "critical_hit", "shield"]
    }
]