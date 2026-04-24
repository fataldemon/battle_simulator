# skill.py
# 战斗模拟器 v14 - 技能模块化管理中心 (修正版)
# 所有技能的定义和执行逻辑都在这里，方便扩展和管理

import random

# ==============================================================================
# 1. 技能效果类 (Skill Effect Classes)
# ==============================================================================

class BaseSkillEffect:
    """技能效果的基类"""
    def __init__(self, name, desc, cost=0):
        self.name = name
        self.desc = desc
        self.cost = cost

    def execute(self, caster, targets, params):
        raise NotImplementedError

class AttackEffect(BaseSkillEffect):
    """单体/群体攻击效果"""
    def __init__(self, name, desc, multiplier=1.0, variance=0, is_crit=False, crit_mult=1.5, is_aoe=False):
        super().__init__(name, desc)
        self.multiplier = multiplier
        self.variance = variance
        self.is_crit = is_crit
        self.crit_mult = crit_mult
        self.is_aoe = is_aoe  # 新增：是否为群体攻击

    def execute(self, caster, targets, params):
        logs = []
        for target in targets:
            if not target.is_alive():
                continue
            
            base_dmg = caster.atk * self.multiplier
            final_dmg = int(base_dmg + random.randint(-self.variance, self.variance))
            
            is_crit = False
            if self.is_crit or random.random() < 0.1:
                final_dmg = int(final_dmg * self.crit_mult)
                is_crit = True
            
            result = target.take_damage(final_dmg)
            
            log_msg = f"   💥 {caster.name} 对 {target.name} 造成了 {result['final_dmg']} 点伤害!"
            if is_crit:
                log_msg += " (暴击!)"
            logs.append(log_msg)
            
            if not target.is_alive():
                logs.append(f"   💀 {target.name} 倒下了...")
        return logs

class AoEAttackEffect(AttackEffect):
    """群体攻击效果 (AOE)"""
    def __init__(self, name, desc, multiplier=1.0, variance=0, is_crit=False, crit_mult=1.5, target_count=None):
        # 初始化时显式标记为 AOE
        # target_count: 如果为 None，则攻击所有目标；如果为整数，则随机攻击指定数量的目标
        super().__init__(name, desc, multiplier, variance, is_crit, crit_mult, is_aoe=True)
        self.target_count = target_count

    def execute(self, caster, targets, params):
        logs = []
        logs.append(f"   ✨ {caster.name} 使用了群体攻击【{self.name}】！")
        
        # 筛选出存活的敌人
        alive_targets = [t for t in targets if t.is_alive()]
        
        # 如果指定了 target_count，则从中随机选取
        if self.target_count is not None and len(alive_targets) > 0:
            count = min(self.target_count, len(alive_targets))
            selected_targets = random.sample(alive_targets, count)
        else:
            selected_targets = alive_targets

        for target in selected_targets:
            base_dmg = caster.atk * self.multiplier
            final_dmg = int(base_dmg + random.randint(-self.variance, self.variance))
            
            is_crit = False
            if self.is_crit or random.random() < 0.1:
                final_dmg = int(final_dmg * self.crit_mult)
                is_crit = True
            
            result = target.take_damage(final_dmg)
            
            log_msg = f"   💥 {caster.name} 对 {target.name} 造成了 {result['final_dmg']} 点伤害!"
            if is_crit:
                log_msg += " (暴击!)"
            logs.append(log_msg)
            
            if not target.is_alive():
                logs.append(f"   💀 {target.name} 倒下了...")
        return logs

class HealEffect(BaseSkillEffect):
    """治疗/恢复效果"""
    def __init__(self, name, desc, amount=0, percent=0.0):
        super().__init__(name, desc)
        self.amount = amount
        self.percent = percent

    def execute(self, caster, targets, params):
        logs = []
        for target in targets:
            if not target.is_alive():
                continue
            
            heal_val = self.amount
            if self.percent > 0:
                heal_val = int(target.max_hp * self.percent)
            
            old_hp = target.hp
            target.hp = min(target.max_hp, target.hp + heal_val)
            actual_heal = target.hp - old_hp
            
            logs.append(f"   💚 {target.name} 恢复了 {actual_heal} HP！")
        return logs

class BuffEffect(BaseSkillEffect):
    """增益效果 (对自己或队友)"""
    def __init__(self, name, desc, stat="atk", value=0, duration=2, icon="⬆️"):
        super().__init__(name, desc)
        self.stat = stat
        self.value = value
        self.duration = duration
        self.icon = icon

    def execute(self, caster, targets, params):
        logs = []
        for target in targets:
            if not target.is_alive():
                continue
            
            target.add_status_effect(self.icon, self.name, self.duration, f"{self.stat}_up", self.value)
            logs.append(f"   ✨ {target.name} 获得了【{self.name}】！({self.stat}提升 {self.value}, 持续 {self.duration} 回合)")
        return logs

class DebuffEffect(BaseSkillEffect):
    """减益效果 (对敌人)"""
    def __init__(self, name, desc, stat="atk", value=0, duration=2, icon="⬇️"):
        super().__init__(name, desc)
        self.stat = stat
        self.value = value
        self.duration = duration
        self.icon = icon

    def execute(self, caster, targets, params):
        logs = []
        for target in targets:
            if not target.is_alive():
                continue
            
            target.add_status_effect(self.icon, self.name, self.duration, f"{self.stat}_down", self.value)
            logs.append(f"   ⚠️ {target.name} 受到了【{self.name}】！({self.stat}降低 {self.value}, 持续 {self.duration} 回合)")
        return logs

class StunEffect(BaseSkillEffect):
    """眩晕效果"""
    def __init__(self, name, desc, chance=1.0):
        super().__init__(name, desc)
        self.chance = chance

    def execute(self, caster, targets, params):
        logs = []
        for target in targets:
            if not target.is_alive():
                continue
            
            if random.random() < self.chance:
                target.is_stunned = True
                logs.append(f"   💫 {target.name} 被眩晕了！无法行动！")
            else:
                logs.append(f"   ❌ {target.name} 抵抗了眩晕！")
        return logs

class SelfHealEffect(BaseSkillEffect):
    """自我恢复效果 (针对怪物)"""
    def __init__(self, name, desc, amount=0, percent=0.0):
        super().__init__(name, desc)
        self.amount = amount
        self.percent = percent

    def execute(self, caster, targets, params):
        logs = []
        heal_val = self.amount
        if self.percent > 0:
            heal_val = int(caster.max_hp * self.percent)
        
        old_hp = caster.hp
        caster.hp = min(caster.max_hp, caster.hp + heal_val)
        actual_heal = caster.hp - old_hp
        logs.append(f"   🧛‍♂️ {caster.name} 自我恢复了 {heal_val} HP！")
        return logs

class LifestealEffect(BaseSkillEffect):
    """吸血效果"""
    def __init__(self, name, desc, multiplier=1.5, ratio=0.5):
        super().__init__(name, desc)
        self.multiplier = multiplier
        self.ratio = ratio

    def execute(self, caster, targets, params):
        logs = []
        target = targets[0] if targets else None
        if not target or not target.is_alive():
            return logs

        base_dmg = caster.atk * self.multiplier
        final_dmg = int(base_dmg + random.randint(-5, 5))
        result = target.take_damage(final_dmg)
        
        heal_val = int(result['final_dmg'] * self.ratio)
        caster.hp = min(caster.max_hp, caster.hp + heal_val)
        
        logs.append(f"   🩸 {caster.name} 吸取了 {result['final_dmg']} 点生命，恢复了 {heal_val} HP！")
        if not target.is_alive():
            logs.append(f"   💀 {target.name} 倒下了...")
        return logs

class TrapEffect(BaseSkillEffect):
    """陷阱/束缚效果"""
    def __init__(self, name, desc):
        super().__init__(name, desc)

    def execute(self, caster, targets, params):
        logs = []
        alive_targets = [t for t in targets if t.is_alive()]
        if alive_targets:
            target = random.choice(alive_targets)
            target.is_stunned = True
            logs.append(f"   🕸️ {target.name} 被 {caster.name} 的【{self.name}】束缚住了！")
        return logs

class CleanseEffect(BaseSkillEffect):
    """清除增益效果"""
    def __init__(self, name, desc):
        super().__init__(name, desc)

    def execute(self, caster, targets, params):
        logs = []
        for target in targets:
            if not target.is_alive():
                continue
            
            if hasattr(target, 'status_effects') and target.status_effects:
                target.status_effects = []
                logs.append(f"   ✨ {target.name} 的所有增益效果被【{self.name}】清除了！")
            else:
                logs.append(f"   ✨ {target.name} 没有增益效果可以被清除。")
        return logs

# ==============================================================================
# 2. 技能注册表 (Skill Registry)
# ==============================================================================

SKILL_REGISTRY = {
    # --- 基础攻击 ---
    "basic_attack": AttackEffect("普通攻击", "进行了一次普通的攻击", multiplier=1.0, variance=5),
    "heavy_strike": AttackEffect("蓄力重击", "发动了强力的一击", multiplier=1.5, variance=10),
    
    # --- 怪物特有技能 ---
    "fireball": AttackEffect("火焰球", "发射了灼热的火焰球", multiplier=1.8, variance=5),
    "shield": BuffEffect("开启护盾", "展开了防御护盾", stat="defense", value=15, duration=2, icon="🛡️"),
    "cry": DebuffEffect("嚎叫 (降低敌方攻击)", "发出了令人胆寒的嚎叫", stat="atk", value=0.2, duration=2, icon="😱"),
    "berserk": AttackEffect("狂暴一击", "进入了狂暴状态", multiplier=2.0, variance=10),
    "auto_repair": SelfHealEffect("自我修复", "启动了紧急维修程序", amount=20),
    "emp_pulse": DebuffEffect("电磁脉冲 (降低全队防御)", "释放了EMP干扰波", stat="defense", value=0.3, duration=2, icon="⚡"),
    "web_trap": TrapEffect("蛛网束缚", "布置了致命的蛛网陷阱"),
    "earthquake": AttackEffect("地震术", "引发了剧烈的地震", multiplier=0.8, variance=10),
    
    # --- 补充遗漏的特色技能 ---
    "slime_bounce": AttackEffect("弹跳撞击", "弹跳着发起攻击", multiplier=0.8, variance=3),
    "acid_spit": AttackEffect("酸液喷射", "喷出了腐蚀性酸液", multiplier=1.2, variance=5),
    "throw_rock": AttackEffect("投掷石块", "投掷了尖锐的石块", multiplier=1.3, variance=8),
    "horn_charge": AttackEffect("角撞", "用犄角发起冲锋", multiplier=1.1, variance=0),
    "charge": AttackEffect("冲撞", "向前猛冲撞击", multiplier=2.0, variance=5),
    "vine_lash": AttackEffect("藤蔓横扫", "甩动藤蔓进行攻击", multiplier=0.6, variance=5),
    "bite": AttackEffect("撕咬", "张开大口咬住敌人", multiplier=1.2, variance=3),
    "scratch": AttackEffect("猫爪乱抓", "用利爪快速抓挠", multiplier=1.0, variance=5),
    "phase_shift": BuffEffect("相位闪烁", "融入阴影中闪避下次攻击", stat="evade", value=1, duration=1, icon="👻"),
    "crush_claw": AttackEffect("巨钳粉碎", "用巨钳狠狠夹碎敌人", multiplier=1.3, variance=0),
    "shell_defense": BuffEffect("缩壳防御", "缩进壳里大幅提升防御", stat="defense", value=20, duration=2, icon="🐚"),
    "emp_hammer": AttackEffect("电磁重锤", "用电磁脉冲锤猛烈砸击", multiplier=1.3, variance=5),
    "shadow_kick": AttackEffect("影踢", "从阴影中突袭踢击", multiplier=1.1, variance=0),
    "acid_bite": AttackEffect("酸液咬合", "用酸液腐蚀的牙齿咬合", multiplier=1.0, variance=5),
    "heavy_stomp": AttackEffect("重踏", "沉重地踩踏地面", multiplier=1.2, variance=10),
    "dragon_wing_slap": AttackEffect("龙翼拍击", "用巨大的龙翼横扫", multiplier=1.5, variance=5),
    "dragon_breath": AttackEffect("龙息吐息", "喷出毁灭性的龙息", multiplier=1.5, variance=10),
    "abyssal_gaze": AttackEffect("深渊凝视", "用空洞的眼神注视敌人", multiplier=1.2, variance=5),
    "void_collapse": CleanseEffect("视界崩坏", "清除我方增益效果"),
    "red_pen_mark": AttackEffect("红笔批改", "用红笔精准批注弱点", multiplier=1.2, variance=0),
    "calculation": AttackEffect("精确计算", "经过精密计算后的攻击", multiplier=2.5, variance=0, is_crit=True, crit_mult=2.0), # Simplified to crit attack
    "high_speed_calculation": AttackEffect("高速计算", "高速运算后的连续打击", multiplier=2.5, variance=0, is_crit=True, crit_mult=2.0),
    "critical_hit": AttackEffect("暴击", "发动了必定暴击的攻击", multiplier=2.0, variance=0, is_crit=True, crit_mult=2.0),
    "life_steal": LifestealEffect("生命汲取", "吸取敌人的生命力", multiplier=1.5, ratio=0.5),
    
    # --- 玩家技能 ---
    "alice_charge": BaseSkillEffect("光啊！", "正在积蓄光之剑的能量", cost=0),
    # 修改：爱丽丝的大招现在使用 AoEAttackEffect 类型
    "alice_ex": AoEAttackEffect("世界的法则即将崩坏！光哟！！！", "释放出覆盖全场的巨大电磁炮", multiplier=5.91, variance=0, is_crit=True, crit_mult=2.0),
    "alice_physical": AttackEffect("物理攻击", "挥舞光之剑进行物理打击", multiplier=1.0, variance=5),
    
    "yuzu_super": StunEffect("通关指令·改", "发动了必杀技，造成了眩晕", chance=0.4),
    "yuzu_normal": AttackEffect("普通攻击", "进行了普通攻击", multiplier=1.0, variance=0),
    
    "midori_heal": HealEffect("艺术润色", "画出了治愈的颜料", amount=25),
    
    # --- 修正桃井的技能 ---
    "momoi_debuff_atk": DebuffEffect("剧情杀 (降低攻击)", "剧本里写着BOSS的攻击下降了", stat="atk", value=0.3, duration=2, icon="📉"),
    "momoi_debuff_def": DebuffEffect("剧情杀 (降低防御)", "剧本里写着BOSS的防御下降了", stat="defense", value=0.3, duration=2, icon="📉"),
    "momoi_debuff": DebuffEffect("剧情杀 (Debuff)", "剧本里写着BOSS的状态变差了", stat="atk", value=0.3, duration=2, icon="📉"),
    "momoi_buff": BuffEffect("剧情杀 (Buff)", "剧本里写着大家获得了力量", stat="atk", value=0.2, duration=2, icon="⚔️"),
    "momoi_heal": HealEffect("剧本里写着大家充满了活力！", "全队恢复了 18 HP！", amount=18), # 新增桃井回复技能
}

# ==============================================================================
# 3. 辅助函数
# ==============================================================================

def get_skill(skill_id):
    """从注册表中获取技能实例"""
    if skill_id in SKILL_REGISTRY:
        return SKILL_REGISTRY[skill_id]
    return None