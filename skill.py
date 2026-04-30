# skill.py
# 战斗模拟器 v44.2 - 技能模块化管理中心 (背刺版)
# 核心改进：
# 1. 【v44.2 新增】背刺系统：在 AttackEffect, AoEAttackEffect, LifestealEffect 中集成背刺判定。
# 2. 当施法者位于目标背面时，造成 125% 的伤害。
# 3. 保持其他原有逻辑不变。

import random

# ==============================================================================
# 1. 技能效果类 (Skill Effect Classes)
# ==============================================================================

class BaseSkillEffect:
    """技能效果的基类"""
    def __init__(self, name, desc, quote="", cost=0, range=1):
        self.name = name
        self.desc = desc
        self.quote = quote  
        self.cost = cost
        self.range = range

    def execute(self, caster, targets, params):
        raise NotImplementedError

def _check_backstab(caster, target):
    """
    检查是否触发背刺
    规则：
    1. 施法者在目标左侧 (pos < target.pos) 且目标面向右 (facing == 1) -> 背刺
    2. 施法者在目标右侧 (pos > target.pos) 且目标面向左 (facing == -1) -> 背刺
    """
    if not hasattr(target, 'facing'):
        return False
    
    # 确保 target 有 position 属性
    if not hasattr(target, 'position') or not hasattr(caster, 'position'):
        return False
        
    pos_diff = caster.position - target.position
    
    if pos_diff < 0 and target.facing == 1:
        return True
    if pos_diff > 0 and target.facing == -1:
        return True
        
    return False

class AttackEffect(BaseSkillEffect):
    """单体/群体攻击效果"""
    def __init__(self, name, desc, quote="", multiplier=1.0, variance=0, is_crit=False, crit_mult=1.5, is_aoe=False, range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.multiplier = multiplier
        self.variance = variance
        self.is_crit = is_crit
        self.crit_mult = crit_mult
        self.is_aoe = is_aoe

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        crit_rate = params.get('crit_rate', getattr(caster, 'crit_rate', 0.1))
        effective_multiplier = params.get('multiplier', self.multiplier)
        effective_variance = params.get('variance', self.variance)
        
        for target in targets:
            if not target.is_alive():
                continue
            
            base_dmg = caster.atk * effective_multiplier
            final_dmg = int(base_dmg + random.randint(-effective_variance, effective_variance))
            
            is_crit = False
            if self.is_crit or random.random() < crit_rate:
                final_dmg = int(final_dmg * self.crit_mult)
                is_crit = True
            
            # 【v44.2 新增】背刺判定
            is_backstab = _check_backstab(caster, target)
            if is_backstab:
                final_dmg = int(final_dmg * 1.25)
            
            result = target.take_damage(final_dmg)
            
            log_msg = f"   💥 {caster.name} 对 {target.name} 造成了 {result['final_dmg']} 点伤害!"
            suffixes = []
            if is_crit:
                suffixes.append("暴击!")
            if is_backstab:
                suffixes.append("背刺!")
                
            if suffixes:
                log_msg += " (" + ", ".join(suffixes) + ")"
                
            logs.append(log_msg)
            
            if not target.is_alive():
                death_msg = getattr(target, 'death_msg', f"{target.name} 倒下了...")
                logs.append(f"   💀 {target.name} 倒下了... \"{death_msg}\"")
        return logs

class AoEAttackEffect(AttackEffect):
    """群体攻击效果 (AOE)"""
    def __init__(self, name, desc, quote="", multiplier=1.0, variance=0, is_crit=False, crit_mult=1.5, target_count=None, range=1):
        super().__init__(name, desc, quote=quote, multiplier=multiplier, variance=variance, is_crit=is_crit, crit_mult=crit_mult, is_aoe=True, range=range)
        self.target_count = target_count

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
        
        alive_targets = [t for t in targets if t.is_alive()]
        
        if self.target_count is not None and len(alive_targets) > 0:
            count = min(self.target_count, len(alive_targets))
            selected_targets = random.sample(alive_targets, count)
        else:
            selected_targets = alive_targets

        crit_rate = params.get('crit_rate', getattr(caster, 'crit_rate', 0.1))
        effective_multiplier = params.get('multiplier', self.multiplier)
        effective_variance = params.get('variance', self.variance)

        for target in selected_targets:
            base_dmg = caster.atk * effective_multiplier
            final_dmg = int(base_dmg + random.randint(-effective_variance, effective_variance))
            
            is_crit = False
            if self.is_crit or random.random() < crit_rate:
                final_dmg = int(final_dmg * self.crit_mult)
                is_crit = True
                
            # 【v44.2 新增】背刺判定
            is_backstab = _check_backstab(caster, target)
            if is_backstab:
                final_dmg = int(final_dmg * 1.25)
            
            result = target.take_damage(final_dmg)
            
            log_msg = f"   💥 {caster.name} 对 {target.name} 造成了 {result['final_dmg']} 点伤害!"
            suffixes = []
            if is_crit:
                suffixes.append("暴击!")
            if is_backstab:
                suffixes.append("背刺!")
                
            if suffixes:
                log_msg += " (" + ", ".join(suffixes) + ")"
            
            logs.append(log_msg)
            
            if not target.is_alive():
                death_msg = getattr(target, 'death_msg', f"{target.name} 倒下了...")
                logs.append(f"   💀 {target.name} 倒下了... \"{death_msg}\"")
        return logs

class HealEffect(BaseSkillEffect):
    """治疗/恢复效果"""
    def __init__(self, name, desc, quote="", amount=0, percent=0.0, range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.amount = amount
        self.percent = percent

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
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
    def __init__(self, name, desc, quote="", stat="atk", value=0, duration=2, icon="⬆️", range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.stat = stat
        self.value = value
        self.duration = duration
        self.icon = icon

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        for target in targets:
            if not target.is_alive():
                continue
            
            target.add_status_effect(self.icon, self.name, self.duration, f"{self.stat}_up", self.value)
            logs.append(f"   ✨ {target.name} 获得了【{self.name}】！({self.stat}提升 {self.value}, 持续 {self.duration} 回合)")
        return logs

class DebuffEffect(BaseSkillEffect):
    """减益效果 (对敌人)"""
    def __init__(self, name, desc, quote="", stat="atk", value=0, duration=2, icon="⬇️", range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.stat = stat
        self.value = value
        self.duration = duration
        self.icon = icon

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        for target in targets:
            if not target.is_alive():
                continue
            
            target.add_status_effect(self.icon, self.name, self.duration, f"{self.stat}_down", self.value)
            logs.append(f"   ⚠️ {target.name} 受到了【{self.name}】！({self.stat}降低 {self.value}, 持续 {self.duration} 回合)")
        return logs

class StunEffect(BaseSkillEffect):
    """眩晕效果（无法行动一回合）"""
    def __init__(self, name, desc, quote="", chance=1.0, range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.chance = chance

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        for target in targets:
            if not target.is_alive():
                continue
            
            if random.random() < self.chance:
                target.is_stunned = True
                logs.append(f"   💫 {target.name} 被眩晕了！无法行动！")
            else:
                logs.append(f"   ❌ {target.name} 抵抗了眩晕！")
        return logs

class ImmobilizeEffect(BaseSkillEffect):
    """束缚/定身效果（无法移动，但可以行动，持续多回合）"""
    def __init__(self, name, desc, quote="", duration=5, range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.duration = duration

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        alive_targets = [t for t in targets if t.is_alive()]
        if alive_targets:
            target = random.choice(alive_targets)
            target.is_immobilized = True
            target.add_status_effect("🕸️", self.name, self.duration, "immobilized", 0)
            logs.append(f"   🕸️ {target.name} 被 {caster.name} 的【{self.name}】束缚住了！（无法移动，持续 {self.duration} 回合）")
        return logs

class SelfHealEffect(BaseSkillEffect):
    """自我恢复效果 (针对怪物)"""
    def __init__(self, name, desc, quote="", amount=0, percent=0.0, range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.amount = amount
        self.percent = percent

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
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
    def __init__(self, name, desc, quote="", multiplier=1.5, ratio=0.5, range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.multiplier = multiplier
        self.ratio = ratio

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        target = targets[0] if targets else None
        if not target or not target.is_alive():
            return logs

        base_dmg = caster.atk * self.multiplier
        final_dmg = int(base_dmg + random.randint(-5, 5))
        
        # 【v44.2 新增】背刺判定
        is_backstab = _check_backstab(caster, target)
        if is_backstab:
            final_dmg = int(final_dmg * 1.25)
            
        result = target.take_damage(final_dmg)
        
        heal_val = int(result['final_dmg'] * self.ratio)
        caster.hp = min(caster.max_hp, caster.hp + heal_val)
        
        log_msg = f"   🩸 {caster.name} 吸取了 {result['final_dmg']} 点生命，恢复了 {heal_val} HP！"
        if is_backstab:
            log_msg += " (背刺!)"
            
        logs.append(log_msg)
        if not target.is_alive():
            death_msg = getattr(target, 'death_msg', f"{target.name} 倒下了...")
            logs.append(f"   💀 {target.name} 倒下了... \"{death_msg}\"")
        return logs

class TrapEffect(ImmobilizeEffect):
    """陷阱/束缚效果（兼容旧代码，继承自 ImmobilizeEffect）"""
    def __init__(self, name, desc, quote="", duration=5, range=1):
        super().__init__(name, desc, quote=quote, duration=duration, range=range)

class CleanseEffect(BaseSkillEffect):
    """清除增益效果"""
    def __init__(self, name, desc, quote="", range=1, clear_energy=False):
        super().__init__(name, desc, quote=quote, range=range)
        # 【v43 新增】可选参数：是否同时清除目标的能量条
        self.clear_energy = clear_energy

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        for target in targets:
            if not target.is_alive():
                continue
            
            has_effects = hasattr(target, 'status_effects') and target.status_effects
            has_energy = hasattr(target, 'energy') and target.energy > 0
            
            # 清除增益/Buff
            if has_effects:
                target.status_effects = []
                logs.append(f"   ✨ {target.name} 的所有增益效果被【{self.name}】清除了！")
            else:
                logs.append(f"   ✨ {target.name} 没有增益效果可以被清除。")
                
            # 【v43 新增】清除能量
            if self.clear_energy and has_energy:
                old_energy = target.energy
                target.energy = 0
                logs.append(f"   🔋 {target.name} 的能量被抽空了！(减少了 {old_energy} 层)")
        return logs

# ==============================================================================\
# 【v43 新增】 高级/特殊效果类
# ==============================================================================\

class DotEffect(BaseSkillEffect):
    """持续伤害效果 (Damage over Time)"""
    def __init__(self, name, desc, quote="", damage_per_tick=10, duration=3, icon="☠️", range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.damage_per_tick = damage_per_tick
        self.duration = duration
        # 【v44.1 修复】添加缺失的属性赋值
        self.icon = icon

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        for target in targets:
            if not target.is_alive():
                continue
            
            # 使用特殊的 effect type: dot
            target.add_status_effect(self.icon, self.name, self.duration, "dot", self.damage_per_tick)
            logs.append(f"   ☠️ {target.name} 中了【{self.name}】！将持续受到伤害！")
        return logs

class BlindEffect(BaseSkillEffect):
    """致盲效果（视线遮蔽，导致随机移动并跳过行动阶段）"""
    def __init__(self, name, desc, quote="", duration=1, chance=1.0, range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.duration = duration
        self.chance = chance

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        # 优先从 params 获取自定义的持续时间或概率
        # 这允许我们在调用时动态调整效果强度
        effective_duration = params.get('blind_duration', self.duration)
        effective_chance = params.get('blind_chance', self.chance)

        for target in targets:
            if not target.is_alive():
                continue
            
            if random.random() < effective_chance:
                target.is_blinded = True
                target.add_status_effect("👁️❌", self.name, effective_duration, "blind", 0)
                logs.append(f"   👁️❌ {target.name} 陷入了致盲状态！视野全黑！")
            else:
                logs.append(f"   🛡️ {target.name} 保持了冷静，未被致盲！")
        return logs

class EnergyBlockEffect(BaseSkillEffect):
    """能量清空效果（直接抽干目标当前的能量）"""
    def __init__(self, name, desc, quote="", range=1):
        super().__init__(name, desc, quote=quote, range=range)

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
            
        for target in targets:
            if not target.is_alive():
                continue
            
            if hasattr(target, 'energy') and target.energy > 0:
                old_energy = target.energy
                target.energy = 0
                logs.append(f"   🔋💨 {target.name} 的能量被 {caster.name} 瞬间抽空了！(减少了 {old_energy} 层)")
            else:
                logs.append(f"   ❌ {target.name} 目前没有能量可以被抽取。")
        return logs

class SequenceEffect(BaseSkillEffect):
    """连携/序列技能效果（百宝箱）"""
    def __init__(self, name, desc, quote="", effects=None, range=1):
        super().__init__(name, desc, quote=quote, range=range)
        self.effects = effects or []

    def execute(self, caster, targets, params):
        logs = []
        if self.quote:
            logs.append(f"   🗣️ {caster.name}: 「{self.quote}」")
        # 【v44 优化】移除“发动了复合技能”的系统提示，保持界面清爽
        
        for effect in self.effects:
            # 递归执行子技能
            sub_logs = effect.execute(caster, targets, params)
            logs.extend(sub_logs)
            
        return logs


# ==============================================================================
# 2. 技能注册表 (Skill Registry) - v44.2 最终修正版
# ==============================================================================

SKILL_REGISTRY = {
    # --- 基础攻击 (近战基准) ---
    "basic_attack": AttackEffect("普通攻击", "进行了一次普通的攻击", quote="", multiplier=1.0, variance=5, range=1),
    
    # --- 玩家技能 (Team Skills) ---
    # 爱丽丝
    "alice_charge": BaseSkillEffect("光啊！赐予我力量！", "正在积蓄光之剑的能量", quote="友情的力量！", cost=0, range=1),
    # 【v44 改动】爱丽丝的EX技能维持最初的经典名称不变
    "alice_ex": AoEAttackEffect("世界的法则即将崩坏！光哟！！！","释放出覆盖全场的巨大电磁炮", quote="世界的法则即将崩坏！光哟！！！ ", multiplier=5.91, variance=0, is_crit=True, crit_mult=2.0, range=99),
    
    # 【v44.4 重构】爱丽丝的普攻改为纯物理斩击，致盲效果由装备【光之剑·超新星】提供
    "alice_physical": AttackEffect(
        "光之剑，出鞘吧",
        "挥舞光之剑进行物理斩击",
        quote="接招吧！光之剑！",
        multiplier=1.0, 
        variance=5, 
        range=2
    ), 
    
    # 柚子 (部门部长)
    "yuzu_super": StunEffect("Hit Stop!", "发动 Hit Stop 强制打断敌人行动", quote="Hit Stop!", chance=0.8, range=3),
    "yuzu_normal": AttackEffect("普通攻击", "保持距离进行防御反击", quote="请别靠近我……", multiplier=1.0, variance=0, range=2),
    
    # 桃井 & 小绿
    "momoi_normal": AttackEffect("内测独占技能", "施展内测独占的特殊招式", quote="嘿嘿，这可是只有内测玩家才能看到的秘密招式！", multiplier=1.0, variance=5, range=5),
    "midori_normal": AttackEffect("草稿涂色", "通过涂抹颜色发起攻击", quote="草稿涂色！请多指教！", multiplier=1.0, variance=5, range=4),
    
    "midori_heal": HealEffect("艺术润色", "绘制出治愈系颜料进行治疗", quote="画出了治愈的颜料！", amount=25, range=7),
    
    "momoi_debuff_atk": DebuffEffect("剧情杀 (降低攻击)", "利用剧情杀降低敌方攻击力", quote="为了让主角赢，反派智商下线了！", stat="atk", value=0.3, duration=2, icon="📉", range=6),
    "momoi_debuff_def": DebuffEffect("剧情杀 (降低防御)", "利用剧情杀降低敌方防御力", quote="为了让主角赢，反派防御下线了！", stat="defense", value=0.3, duration=2, icon="📉", range=6),
    "momoi_debuff": DebuffEffect("剧情杀 (Debuff)", "利用剧情杀削弱敌方战力", quote="剧本就是这么写的！", stat="atk", value=0.3, duration=2, icon="📉", range=6),
    "momoi_buff": BuffEffect("剧情杀 (Buff)", "为了收视率提升己方攻击力", quote="为了收视率，主角团必须加强！", stat="atk", value=0.2, duration=2, icon="⚔️", range=5),
    "momoi_heal": HealEffect("剧本里写着大家充满了活力！", "播放感人回忆杀恢复生命值", quote="插入一段感人至深的回忆杀！", amount=18, range=7),
    
    # --- 优香大人的精准打击 (Shinonome Yuuka) - 财务审计模式 ---
    # 普通攻击：充满压迫感的怒吼
    "yuuka_normal": AttackEffect("红笔批改", "用红笔精准批注弱点", quote="桃井——！！！ ", multiplier=1.2, variance=0, range=8),
    
    # 精确计算：关于费用的唠叨
    "calculation": AttackEffect("精确计算", "经过精密计算后的攻击", quote="这笔违规支出，直接从你的报销款里扣除！", multiplier=2.5, variance=0, is_crit=True, crit_mult=2.0, range=8),
    
    # 高速计算：连续的账单
    "high_speed_calculation": AttackEffect("高速计算", "高速运算后的连续打击", quote="三秒钟内让你破产！", multiplier=2.5, variance=0, is_crit=True, crit_mult=2.0, range=9),
    
    # 暴击：绝对的财政制裁
    "critical_hit": AttackEffect("暴击", "发动了必定暴击的攻击", quote="违规！立即冻结所有预算！", multiplier=2.0, variance=0, is_crit=True, crit_mult=2.0, range=10),
    
    # --- 怪物特有技能 (Monster Skills) ---
    
    # 【近战梯队 Range 1】 (已修正)
    "heavy_strike": AttackEffect("蓄力重击", "发动了强力的一击", quote="吃我一拳！", multiplier=1.5, variance=10, range=1),
    "berserk": AttackEffect("狂暴一击", "进入了狂暴状态", quote="吼啊啊啊！好痛！", multiplier=2.0, variance=10, range=1),
    "slime_bounce": AttackEffect("弹跳撞击", "弹跳着发起攻击", quote="噗尼~！", multiplier=0.8, variance=3, range=1),
    "horn_charge": AttackEffect("角撞", "用犄角发起冲锋", quote="呜噢噢噢！", multiplier=1.1, variance=0, range=1),
    "charge": AttackEffect("冲撞", "向前猛冲撞击", quote="我要撞飞你！", multiplier=2.0, variance=5, range=1),
    "bite": AttackEffect("撕咬", "张开大口咬住敌人", quote="嗷呜！", multiplier=1.2, variance=3, range=1),
    "scratch": AttackEffect("猫爪乱抓", "用利爪快速抓挠", quote="嘶哈——！", multiplier=1.0, variance=5, range=1),
    "crush_claw": AttackEffect("巨钳粉碎", "用巨钳狠狠夹碎敌人", quote="咔嚓！碎掉吧！", multiplier=1.3, variance=0, range=1),
    "emp_hammer": AttackEffect("电磁重锤", "用电磁脉冲锤猛烈砸击", quote="滋啦啦——！", multiplier=1.3, variance=5, range=1),
    "shadow_kick": AttackEffect("影踢", "从阴影中突袭踢击", quote="嘿！", multiplier=1.1, variance=0, range=1),
    "acid_bite": AttackEffect("酸液咬合", "用酸液腐蚀的牙齿咬合", quote="滋滋……", multiplier=1.0, variance=5, range=1),
    "heavy_stomp": AttackEffect("重踏", "沉重地踩踏地面", quote="咚！！", multiplier=1.2, variance=10, range=1),
    "life_steal": LifestealEffect("生命汲取", "吸取敌人的生命力", quote="把你的力量交出来！", multiplier=1.5, ratio=0.5, range=1),
    
    # 【中程梯队 Range 4-6】
    "fireball": AttackEffect("火焰球", "发射了灼热的火焰球", quote="燃烧吧！", multiplier=1.8, variance=5, range=5),
    "vine_lash": AttackEffect("藤蔓横扫", "甩动藤蔓进行攻击", quote="缠绕上来！", multiplier=0.6, variance=5, range=4),
    "throw_rock": AttackEffect("投掷石块", "投掷了尖锐的石块", quote="接招！石头！", multiplier=1.3, variance=8, range=6),
    "dragon_wing_slap": AttackEffect("龙翼拍击", "用巨大的龙翼横扫", quote="风压！", multiplier=1.5, variance=5, range=5),
    "web_trap": TrapEffect("蛛网束缚", "布置了致命的蛛网陷阱", quote="别想逃！", duration=5, range=5),
    "cry": DebuffEffect("嚎叫 (降低敌方攻击)", "发出了令人胆寒的嚎叫", quote="嗷呜————！", stat="atk", value=0.2, duration=2, icon="😱", range=6),
    
    # 【远程梯队 Range 7-10】
    "acid_spit": AttackEffect("酸液喷射", "喷出了腐蚀性酸液", quote="呸！", multiplier=1.2, variance=5, range=8),
    "dragon_breath": AttackEffect("龙息吐息", "喷出毁灭性的龙息", quote="呼——！！！ ", multiplier=1.5, variance=10, range=9),
    "abyssal_gaze": AttackEffect("深渊凝视", "用空洞的眼神注视敌人", quote="(低沉的嗡鸣)", multiplier=1.2, variance=5, range=7),
    
    # 【自身增益/特殊机制 (Self-Buffs)】
    "shield": BuffEffect("开启护盾", "展开了防御护盾", quote="防御模式启动。", stat="defense", value=15, duration=2, icon="🛡️", range=1),
    "auto_repair": SelfHealEffect("自我修复", "启动了紧急维修程序", quote="滴滴滴...修复中。", amount=20, range=1),
    "phase_shift": BuffEffect("相位闪烁", "融入阴影中闪避下次攻击", quote="隐身！", stat="evade", value=1, duration=1, icon="👻", range=1),
    "shell_defense": BuffEffect("缩壳防御", "缩进壳里大幅提升防御", quote="躲进去！", stat="defense", value=20, duration=2, icon="🐚", range=1),
    
    # 【超远程/全屏 (Full Screen)】
    "earthquake": AttackEffect("地震术", "引发了剧烈的地震", quote="大地的愤怒！", multiplier=0.8, variance=10, range=99),
    # 【v43 更新】视界崩坏增加了清空能量的选项
    "void_collapse": CleanseEffect("视界崩坏", "清除我方增益效果并抽干能量", quote="世界崩坏了！", range=99, clear_energy=True),
    
    # ==============================================================================\
    # 【v43 新增】 带有 DoT / 灼烧 / 出血 / 腐蚀 的复合技能
    # ==============================================================================\
    
    # 史莱姆的中毒酸液
    "acid_spit_dot": SequenceEffect(
        "酸性毒雾",
        "喷射带有剧毒的酸液",
        quote="呸！有毒的哦！",
        effects=[
            AttackEffect("酸液溅射", "酸液附着在皮肤上造成初期伤害", multiplier=1.0, variance=3, range=8),
            DotEffect("重度中毒", "毒素侵入体内持续破坏", damage_per_tick=8, duration=3, icon="☠️", range=8)
        ],
        range=8
    ),
    
    # 食人花的中毒藤蔓
    "vine_lash_dot": SequenceEffect(
        "剧毒藤鞭",
        "甩动带毒的藤蔓抽打敌人",
        quote="尝尝我的汁液！",
        effects=[
            AttackEffect("藤蔓抽打", "坚韧的藤蔓造成伤害", multiplier=0.8, variance=5, range=4),
            DotEffect("植物毒素", "伤口开始溃烂", damage_per_tick=10, duration=3, icon="☠️", range=4)
        ],
        range=4
    ),
    
    # 暗影忍者的出血攻击
    "shadow_kick_bleed": SequenceEffect(
        "裂影断水脚",
        "撕裂伤口的致命踢击",
        quote="破！",
        effects=[
            AttackEffect("凌厉踢击", "集中一点突破防御", multiplier=1.5, variance=5, range=1),
            DotEffect("大量出血", "伤口止不住地在流血", damage_per_tick=12, duration=4, icon="🩸", range=1)
        ],
        range=1
    ),
    
    # 机械蜘蛛的腐蚀酸液
    "acid_bite_corrosion": SequenceEffect(
        "高浓缩酸液咬合",
        "用能溶解钢铁的酸液进行攻击",
        quote="解析中... 溶解中...",
        effects=[
            AttackEffect("酸性侵蚀", "酸液破坏表面装甲", multiplier=1.2, variance=5, range=1),
            DotEffect("结构腐蚀", "身体结构受到持续破坏", damage_per_tick=15, duration=3, icon="🧪", range=1)
        ],
        range=1
    ),
    
    # 古代巨龙的灼烧龙息
    "dragon_breath_burn": SequenceEffect(
        "狱炎吐息",
        "喷吐出附带高温的火柱",
        quote="化为灰烬吧！",
        effects=[
            AttackEffect("烈焰冲击", "火柱造成巨额伤害", multiplier=2.0, variance=10, range=9),
            DotEffect("深度灼伤", "皮肉被点燃持续燃烧", damage_per_tick=20, duration=4, icon="🔥", range=9)
        ],
        range=9
    ),
    
    # 虚空吞噬者的能量榨取版
    "void_collapse_drain": SequenceEffect(
        "虚无吞噬",
        "吞没一切光芒与能量",
        quote="归于虚无...",
        effects=[
            AttackEffect("虚空震荡", "暗物质波纹造成伤害", multiplier=1.5, variance=10, range=99),
            CleanseEffect("能量剥夺", "强行吸干目标的能量", range=99, clear_energy=True)
        ],
        range=99
    )
}

# ==============================================================================\
# 3. 辅助函数
# ==============================================================================\

def get_skill(skill_id):
    """从注册表中获取技能实例"""
    if skill_id in SKILL_REGISTRY:
        return SKILL_REGISTRY[skill_id]
    return None