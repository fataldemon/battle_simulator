# skill.py
# 战斗模拟器 v23 - 技能模块化管理中心 (全射程梯度优化版)
# 核心改进：大幅调整射程分布，从单一的 1 和 99 扩展为 1-10 的完整梯度

import random

# ==============================================================================
# 1. 技能效果类 (Skill Effect Classes)
# ==============================================================================

class BaseSkillEffect:
    """技能效果的基类"""
    def __init__(self, name, desc, cost=0, range=1):
        self.name = name
        self.desc = desc
        self.cost = cost
        self.range = range

    def execute(self, caster, targets, params):
        raise NotImplementedError

class AttackEffect(BaseSkillEffect):
    """单体/群体攻击效果"""
    def __init__(self, name, desc, multiplier=1.0, variance=0, is_crit=False, crit_mult=1.5, is_aoe=False, range=1):
        super().__init__(name, desc, range=range)
        self.multiplier = multiplier
        self.variance = variance
        self.is_crit = is_crit
        self.crit_mult = crit_mult
        self.is_aoe = is_aoe

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
                death_msg = getattr(target, 'death_msg', f"{target.name} 倒下了...")
                # 【修复】修正转义字符错误
                logs.append(f"   💀 {target.name} 倒下了... \"{death_msg}\"")
        return logs

class AoEAttackEffect(AttackEffect):
    """群体攻击效果 (AOE)"""
    def __init__(self, name, desc, multiplier=1.0, variance=0, is_crit=False, crit_mult=1.5, target_count=None, range=1):
        super().__init__(name, desc, multiplier, variance, is_crit, crit_mult, is_aoe=True, range=range)
        self.target_count = target_count

    def execute(self, caster, targets, params):
        logs = []
        logs.append(f"   ✨ {caster.name} 使用了群体攻击【{self.name}】！")
        
        alive_targets = [t for t in targets if t.is_alive()]
        
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
                death_msg = getattr(target, 'death_msg', f"{target.name} 倒下了...")
                # 【修复】修正转义字符错误
                logs.append(f"   💀 {target.name} 倒下了... \"{death_msg}\"")
        return logs

class HealEffect(BaseSkillEffect):
    """治疗/恢复效果"""
    def __init__(self, name, desc, amount=0, percent=0.0, range=1):
        super().__init__(name, desc, range=range)
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
    def __init__(self, name, desc, stat="atk", value=0, duration=2, icon="⬆️", range=1):
        super().__init__(name, desc, range=range)
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
    def __init__(self, name, desc, stat="atk", value=0, duration=2, icon="⬇️", range=1):
        super().__init__(name, desc, range=range)
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
    def __init__(self, name, desc, chance=1.0, range=1):
        super().__init__(name, desc, range=range)
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
    def __init__(self, name, desc, amount=0, percent=0.0, range=1):
        super().__init__(name, desc, range=range)
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
    def __init__(self, name, desc, multiplier=1.5, ratio=0.5, range=1):
        super().__init__(name, desc, range=range)
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
            death_msg = getattr(target, 'death_msg', f"{target.name} 倒下了...")
            # 【修复】修正转义字符错误
            logs.append(f"   💀 {target.name} 倒下了... \"{death_msg}\"")
        return logs

class TrapEffect(BaseSkillEffect):
    """陷阱/束缚效果"""
    def __init__(self, name, desc, range=1):
        super().__init__(name, desc, range=range)

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
    def __init__(self, name, desc, range=1):
        super().__init__(name, desc, range=range)

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
# 2. 技能注册表 (Skill Registry) - v23 全射程梯度版
# ==============================================================================

SKILL_REGISTRY = {
    # --- 基础攻击 (近战基准) ---
    "basic_attack": AttackEffect("普通攻击", "进行了一次普通的攻击", multiplier=1.0, variance=5, range=1),
    
    # --- 玩家技能 (Team Skills) ---
    # 爱丽丝：普攻稍微远一点，毕竟是电磁炮
    "alice_charge": BaseSkillEffect("光啊！赐予我力量！", "正在积蓄光之剑的能量", cost=0, range=1),
    "alice_ex": AoEAttackEffect("世界的法则即将崩坏！光哟！！！","释放出覆盖全场的巨大电磁炮", multiplier=5.91, variance=0, is_crit=True, crit_mult=2.0, range=99),
    "alice_physical": AttackEffect("光之剑，出鞘吧", "光之剑出鞘，斩向敌人！", multiplier=1.0, variance=5, range=2), 
    
    # 柚子：突击手，短距高爆发
    "yuzu_super": StunEffect("Hit Stop!", "时间停止！强制打断！", chance=0.4, range=3),
    "yuzu_normal": AttackEffect("普通攻击", "请别靠近我……", multiplier=1.0, variance=0, range=2),
    
    # 桃井 & 小绿：后方支援，射程较远
    "momoi_normal": AttackEffect("内测独占技能", "嘿嘿，这可是只有内测玩家才能看到的秘密招式！", multiplier=1.0, variance=5, range=5),
    "midori_normal": AttackEffect("草稿涂色", "草稿涂色！请多指教！", multiplier=1.0, variance=5, range=4),
    
    "midori_heal": HealEffect("艺术润色", "画出了治愈的颜料", amount=25, range=7),
    
    "momoi_debuff_atk": DebuffEffect("剧情杀 (降低攻击)", "为了让主角赢得漂亮，BOSS 的智商下线了！", stat="atk", value=0.3, duration=2, icon="📉", range=6),
    "momoi_debuff_def": DebuffEffect("剧情杀 (降低防御)", "为了让主角赢得漂亮，BOSS 的智商下线了！", stat="defense", value=0.3, duration=2, icon="📉", range=6),
    "momoi_debuff": DebuffEffect("剧情杀 (Debuff)", "为了让主角赢得漂亮，BOSS 的智商下线了！", stat="atk", value=0.3, duration=2, icon="📉", range=6),
    "momoi_buff": BuffEffect("剧情杀 (Buff)", "为了收视率，主角团必须加强！", stat="atk", value=0.2, duration=2, icon="⚔️", range=5),
    "momoi_heal": HealEffect("剧本里写着大家充满了活力！", "插入一段感人至深的回忆杀！", amount=18, range=7),
    
    # --- 怪物特有技能 (Monster Skills) ---
    
    # 【近战梯队 Range 1-3】
    "heavy_strike": AttackEffect("蓄力重击", "发动了强力的一击", multiplier=1.5, variance=10, range=2),
    "berserk": AttackEffect("狂暴一击", "进入了狂暴状态", multiplier=2.0, variance=10, range=2),
    "slime_bounce": AttackEffect("弹跳撞击", "弹跳着发起攻击", multiplier=0.8, variance=3, range=2),
    "horn_charge": AttackEffect("角撞", "用犄角发起冲锋", multiplier=1.1, variance=0, range=2),
    "charge": AttackEffect("冲撞", "向前猛冲撞击", multiplier=2.0, variance=5, range=3),
    "bite": AttackEffect("撕咬", "张开大口咬住敌人", multiplier=1.2, variance=3, range=2),
    "scratch": AttackEffect("猫爪乱抓", "用利爪快速抓挠", multiplier=1.0, variance=5, range=2),
    "crush_claw": AttackEffect("巨钳粉碎", "用巨钳狠狠夹碎敌人", multiplier=1.3, variance=0, range=2),
    "emp_hammer": AttackEffect("电磁重锤", "用电磁脉冲锤猛烈砸击", multiplier=1.3, variance=5, range=2),
    "shadow_kick": AttackEffect("影踢", "从阴影中突袭踢击", multiplier=1.1, variance=0, range=2),
    "acid_bite": AttackEffect("酸液咬合", "用酸液腐蚀的牙齿咬合", multiplier=1.0, variance=5, range=2),
    "heavy_stomp": AttackEffect("重踏", "沉重地踩踏地面", multiplier=1.2, variance=10, range=3),
    "life_steal": LifestealEffect("生命汲取", "吸取敌人的生命力", multiplier=1.5, ratio=0.5, range=3),
    
    # 【中程梯队 Range 4-6】
    "fireball": AttackEffect("火焰球", "发射了灼热的火焰球", multiplier=1.8, variance=5, range=5),
    "vine_lash": AttackEffect("藤蔓横扫", "甩动藤蔓进行攻击", multiplier=0.6, variance=5, range=4),
    "throw_rock": AttackEffect("投掷石块", "投掷了尖锐的石块", multiplier=1.3, variance=8, range=6),
    "dragon_wing_slap": AttackEffect("龙翼拍击", "用巨大的龙翼横扫", multiplier=1.5, variance=5, range=5),
    "web_trap": TrapEffect("蛛网束缚", "布置了致命的蛛网陷阱", range=5),
    "cry": DebuffEffect("嚎叫 (降低敌方攻击)", "发出了令人胆寒的嚎叫", stat="atk", value=0.2, duration=2, icon="😱", range=6),
    
    # 【远程梯队 Range 7-10】
    "acid_spit": AttackEffect("酸液喷射", "喷出了腐蚀性酸液", multiplier=1.2, variance=5, range=8),
    "dragon_breath": AttackEffect("龙息吐息", "喷出毁灭性的龙息", multiplier=1.5, variance=10, range=9),
    "abyssal_gaze": AttackEffect("深渊凝视", "用空洞的眼神注视敌人", multiplier=1.2, variance=5, range=7),
    
    # 【优香大人的精准打击 (假设她是某种精英怪) Range 8-10】
    "red_pen_mark": AttackEffect("红笔批改", "用红笔精准批注弱点", multiplier=1.2, variance=0, range=8),
    "calculation": AttackEffect("精确计算", "经过精密计算后的攻击", multiplier=2.5, variance=0, is_crit=True, crit_mult=2.0, range=8),
    "high_speed_calculation": AttackEffect("高速计算", "高速运算后的连续打击", multiplier=2.5, variance=0, is_crit=True, crit_mult=2.0, range=9),
    "critical_hit": AttackEffect("暴击", "发动了必定暴击的攻击", multiplier=2.0, variance=0, is_crit=True, crit_mult=2.0, range=10),
    
    # 【自身增益/特殊机制 (Self-Buffs)】
    "shield": BuffEffect("开启护盾", "展开了防御护盾", stat="defense", value=15, duration=2, icon="🛡️", range=1),
    "auto_repair": SelfHealEffect("自我修复", "启动了紧急维修程序", amount=20, range=1),
    "phase_shift": BuffEffect("相位闪烁", "融入阴影中闪避下次攻击", stat="evade", value=1, duration=1, icon="👻", range=1),
    "shell_defense": BuffEffect("缩壳防御", "缩进壳里大幅提升防御", stat="defense", value=20, duration=2, icon="🐚", range=1),
    
    # 【超远程/全屏 (Full Screen)】
    "earthquake": AttackEffect("地震术", "引发了剧烈的地震", multiplier=0.8, variance=10, range=99),
    "void_collapse": CleanseEffect("视界崩坏", "清除我方增益效果", range=99),
}

# ==============================================================================
# 3. 辅助函数
# ==============================================================================

def get_skill(skill_id):
    """从注册表中获取技能实例"""
    if skill_id in SKILL_REGISTRY:
        return SKILL_REGISTRY[skill_id]
    return None