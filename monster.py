# monster.py
# 战斗模拟器 v43.1 - 怪物数据与行为逻辑模块 (含能量系统与物理挤压版)
# 核心改进：
# 1. 【v43 新增】全员能量化：怪物现在也拥有 Energy 槽，可以积蓄能量释放大招（EX Skill）。
# 2. 【v43 新增】高级状态处理：完美支持 DoT (持续伤害)、Blind (致盲/随机移动)、Energy Block (阻断充能)。
# 3. 【v43 新增】致盲逻辑：致盲状态下无法发动技能，且会强制进行随机位移。
# 4. 【v43.1 重大修复】物理挤压逻辑：怪物移动现在真正调用 squeeze_move，实现了战场上的真实推挤效果！
# 5. 兼容旧有的智能索敌与追击逻辑。

import random
# 导入所有需要用到的技能效果类
# 【v44 修复】补充导入 SequenceEffect，以支持怪物的复合技能
from skill import SKILL_REGISTRY, get_skill, AttackEffect, BuffEffect, DebuffEffect, TrapEffect, SelfHealEffect, LifestealEffect, HealEffect, StunEffect, CleanseEffect, DotEffect, BlindEffect, EnergyBlockEffect, SequenceEffect
# 【v43.1 新增】导入挤压移动工具
from utils import squeeze_move

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
        
        # 【v43 新增】能量系统
        self.energy = 0
        self.max_energy = 5  # 默认满能量为 5 层
        
        self.desc = data["desc"]
        self.quote = data["quote"]
        self.skill_type = data["skill_type"]
        
        # 自定义技能表 (引用 skill.py 中的技能ID)
        self.custom_skills = data.get("skills_list", [])
        
        # 【v43 新增】EX 技能 (大招)
        self.ex_skill_id = data.get("ex_skill_id", None)

        # 额外属性 (旧逻辑，保留兼容)
        self.defense_buff_turns = 0
        self.attack_debuff_turns = 0
        self.reflect_turns = 0
        self.evade_next = False
        self.is_stunned = False 
        self.is_immobilized = False
        self.is_blinded = False  # 【v43 新增】致盲标志
        
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
        
        # 3. 应用数值修正
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
                
        # 4. 重置临时状态标志
        if not any(s["effect"] == "blind" for s in self.status_effects):
            self.is_blinded = False
        if not any(s["effect"] == "immobilized" for s in self.status_effects):
            self.is_immobilized = False

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

    def _move_randomly(self, battle_field):
        """【v43.1 重构】致盲状态下的随机移动 (启用物理挤压)"""
        old_pos = self.position
        move_dist = random.randint(1, 3)
        direction = random.choice([-1, 1])
        new_pos = old_pos + (move_dist * direction)
        
        # 简单的边界限制 (不能跑出战场)
        new_pos = max(0, min(len(battle_field)-1, new_pos))
        
        # 【v43.1 核心】使用 squeeze_move 实现真实的推挤移动
        success = squeeze_move(battle_field, self, new_pos)
        
        # 打印日志
        if success:
            # 判断方向文本
            dir_text = "左" if new_pos < old_pos else "右"
            print(f"   👁️❌ {self.name} 因为看不清路，惊慌失措地向 {dir_text} 方乱撞！(从 {old_pos} 移动到 {self.position})")
        else:
            print(f"   👁️❌ {self.name} 试图乱撞，但被周围的人群挤得动弹不得！")

    def _move_towards_target(self, party_members, battle_field, target_position=None):
        """
        【v43.1 重构】追击逻辑：向最近的敌人移动，或者直接移动到指定位置 (启用物理挤压)
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
        
        # 【v43.1 核心】直接使用 squeeze_move 移动到目标位置
        # 这会尝试把自己插到目标位置，并把原来在那的人往后推
        success = squeeze_move(battle_field, self, target_position)
        
        if success:
            print(f"   👹 {self.name} 发现无法攻击，决定向目标逼近！(从 {old_pos} 移动到 {self.position})")
        else:
            print(f"   👹 {self.name} 试图接近目标，但被挡住了！")
            
        return success

    def decide_action(self, party_members, battle_field):
        """
        怪物AI：决定本回合行动 (模块化版 + 智能索敌 + 物理挤压 v43.1 + 能量系统 v43)
        :param party_members: 玩家小队成员列表 (用于索敌)
        :param battle_field: 完整的战场列表 (包含所有单位，用于物理挤压移动)
        """
        # 【v43 新增】检查是否处于致盲状态
        if self.is_blinded:
            print(f"👁️❌ {self.name} 处于致盲状态，视野全黑！")
            self._move_randomly(battle_field) # 传入 battle_field
            return None # 无法发动技能

        # 检查是否处于晕眩状态
        if self.is_stunned:
            print(f"💫 {self.name} 处于眩晕状态，无法行动！")
            self.is_stunned = False 
            return None 

        # 【v43 新增】尝试释放 EX 技能 (如果能量满了且有 EX 技能定义)
        if self.energy >= self.max_energy and self.ex_skill_id:
            ex_skill = get_skill(self.ex_skill_id)
            if ex_skill:
                print(f"✨ {self.name} 能量蓄满，发动了绝招【{ex_skill.name}】！")
                targets = [p for p in party_members if p.is_alive()]
                logs = ex_skill.execute(self, targets, {})
                for log in logs:
                    print(log)
                self.energy = 0 # 消耗能量
                # 释放完大招后，本回合通常不再进行普通行动（视具体游戏设计而定，这里简化处理为大招即全部行动）
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
            
        elif isinstance(skill, DotEffect):
             needs_external_target = True
             targets = self._find_valid_targets(party_members, skill.range)

        elif isinstance(skill, BlindEffect):
             needs_external_target = True
             targets = self._find_valid_targets(party_members, skill.range)

        elif isinstance(skill, EnergyBlockEffect):
             needs_external_target = True
             targets = self._find_valid_targets(party_members, skill.range)

        # 【v44 紧急修复】增加对 SequenceEffect 的支持，使其能够正确寻找目标
        elif isinstance(skill, SequenceEffect):
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
                self._move_towards_target(party_members, battle_field) # 传入 battle_field
                
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
                elif isinstance(skill, DotEffect):
                    targets = self._find_valid_targets(party_members, skill.range)
                elif isinstance(skill, BlindEffect):
                    targets = self._find_valid_targets(party_members, skill.range)
                elif isinstance(skill, EnergyBlockEffect):
                    targets = self._find_valid_targets(party_members, skill.range)
                elif isinstance(skill, SequenceEffect):
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
                elif isinstance(skill, DotEffect):
                     # DoT 也只打一个
                    target = random.choice(targets)
                    logs = skill.execute(self, [target], {})
                elif isinstance(skill, BlindEffect):
                    # 致盲也只打一个
                    target = random.choice(targets)
                    logs = skill.execute(self, [target], {})
                elif isinstance(skill, EnergyBlockEffect):
                    # 能量封锁也只打一个
                    target = random.choice(targets)
                    logs = skill.execute(self, [target], {})
                else:
                    # AOE 或其他群体效果 (包括 SequenceEffect)
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
            
        # 【v43 新增】行动结束后尝试获得一点能量 (普通行动积攒 1 点)
        self.gain_energy(1)
            
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
        """打印状态信息：名字、血条、数值、状态图标、能量条"""
        bar_length = 20
        filled = int(self.hp / self.max_hp * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # 【v21 修复】增加状态图标显示逻辑，与 Player 保持一致
        status_str = ""
        if self.status_effects:
            icons = " ".join([s['icon'] for s in self.status_effects])
            status_str = f" {icons}"
        
        # 【v43 新增】能量条显示
        energy_bar = "⚡" * self.energy + "☆" * (self.max_energy - self.energy)
        
        print(f"   {self.name}: [{bar}] {self.hp}/{self.max_hp} [{energy_bar}]{status_str}")

# --- 数据常量 ---
MONSTERS_DATA = [
    {
        "name": "黏糊糊史莱姆", "level": 1, "hp": 100, "base_atk": 10, "base_defense": 5,
        "desc": "软绵绵的家伙，虽然弱但是数量多！", "quote": "喵呜喵呜~", "skill_type": "gel_form",
        "skills_list": ["slime_bounce", "acid_spit_dot"] # 【v43 更新】改为带中毒的技能
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
        "skills_list": ["vine_lash_dot", "bite"] # 【v43 更新】改为带中毒的技能
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
        "skills_list": ["shadow_kick_bleed", "cry"] # 【v43 更新】改为带出血的技能
    },
    {
        "name": "机械蜘蛛", "level": 7, "hp": 292, "base_atk": 42, "base_defense": 20,
        "desc": "精密的机械构造体，腿上有锋利的刀刃。", "quote": "滴滴滴... 锁定目标...", "skill_type": "web_trap",
        "skills_list": ["web_trap", "acid_bite_corrosion"] # 【v43 更新】改为带腐蚀的技能
    },
    {
        "name": "石头巨人", "level": 8, "hp": 512, "base_atk": 51, "base_defense": 50,
        "desc": "由岩石构成的巨大生命体，防御力极高。", "quote": "轰隆隆...", "skill_type": "stone_skin",
        "skills_list": ["heavy_stomp", "shield"]
    },
    {
        "name": "古代巨龙·炎", "level": 10, "hp": 500, "base_atk": 60, "base_defense": 40,
        "desc": "拥有极高火抗性的终极BOSS！", "quote": "吼——————！！！ ", "skill_type": "dragon_fury",
        "skills_list": ["dragon_wing_slap", "dragon_breath_burn", "shield"], # 【v43 更新】改为带灼烧的技能
        "ex_skill_id": "dragon_breath_burn" # 【v43 新增】龙的大招
    },
    {
        "name": "虚空吞噬者", "level": 11, "hp": 995, "base_atk": 80, "base_defense": 60,
        "desc": "来自深渊的终极Boss，所过之处一片虚无。", "quote": "吞噬... 一切...", "skill_type": "life_steal",
        "skills_list": ["void_collapse_drain", "abyssal_gaze", "life_steal"] # 【v43 更新】改为清空能量的技能
    },
    {
        "name": "虚空吞噬者·终焉", "level": 12, "hp": 2500, "base_atk": 95, "base_defense": 80,
        "desc": "吸收了团队能量的强化版虚空吞噬者，正在不断恢复！", "quote": "吞噬... 你们的力量...", "skill_type": "life_steal",
        "skills_list": ["void_collapse_drain", "abyssal_gaze", "life_steal", "shield"]
    },
    {
        "name": "优香大魔王", "level": 99, "hp": 9999, "base_atk": 100, "base_defense": 100,
        "desc": "体重100kg的重装法师，计算精确到小数点后三位！", "quote": "按照计算，消失吧！", "skill_type": "calculation",
        "skills_list": ["calculation", "high_speed_calculation", "critical_hit", "shield"]
    }
]