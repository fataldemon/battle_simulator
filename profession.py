# profession.py
# 战斗模拟器 v2.4 - 职业系统模块 (完整版)
# 核心设计：属性加成 + 被动效果 + 分级技能解锁（随等级逐步解锁）
# 
# 【v2.4 重大更新】：
# 1. 职业体系全面重构，从 8 职业扩展至 9 职业
# 2. 引入"遗物"概念（Lv.3 解锁的特殊被动/数值修正）
# 3. 支持特殊机制：元素组合(法师)、形态切换(德鲁伊)、层数叠加(吟游诗人)
# 4. 统一成长曲线：Lv.1(基础) -> Lv.3(遗物) -> Lv.5(大招) -> Lv.7(属性质变)

class Profession:
    """
    职业基类 v2.4
    包含：属性加成、被动效果、遗物、分级技能解锁表
    """
    def __init__(self, prof_id, display_name, stat_bonus, passive_tags, relic_tag=None, skill_unlock_table=None):
        self.id = prof_id  
        self.display_name = display_name
        
        # --- 1. 属性加成 (Stat Bonuses) ---
        self.stat_bonus = stat_bonus
        
        # --- 2. 被动效果 (Passive Effects) ---
        self.passive_tags = passive_tags 
        
        # --- 2.5 遗物 (Relic) - Lv.3 解锁 ---
        self.relic_tag = relic_tag  # 字符串标识，如 "element_box", "state_machine"
        
        # --- 3. 技能解锁表 (Skill Unlock Table) ---
        # 格式：{ level: [skill_id1, skill_id2], ... }
        self.skill_unlock_table = skill_unlock_table or {}
        
    def get_available_skills(self, level):
        """根据当前等级返回已解锁的技能ID列表"""
        available = []
        for unlock_lvl, skills in sorted(self.skill_unlock_table.items()):
            if level >= unlock_lvl:
                available.extend(skills)
        return list(set(available))


# ============================================================
# 职业数据定义 (v2.4 完整版)
# ============================================================

PROFESSIONS_DATA = {
    
    # ========================================================================
    # A. 通用职业 (General Classes)
    # ========================================================================
    
    # --- 骑士 (Knight) ---
    "knight": Profession(
        prof_id="knight",
        display_name="骑士",
        stat_bonus={
            "hp": 30,
            "max_energy": 0,
            "atk_multiplier": 1.2,
            "def_multiplier": 1.3
        },
        passive_tags=["charge"],  # 【冲锋】移动距离转化为攻击力加成
        relic_tag="milan_armor",   # 【米兰板甲】冲锋时移动距离转化为减伤/格挡值
        skill_unlock_table={
            1: ["lance_impact"],       # 【骑枪冲击】普攻+穿透身后一人
            3: ["divine_protection"],  # 遗物关联技能
            5: ["war_summon"],         # 【战争召唤】自晕1t，全队双倍行动+奶+盾
            7: ["power_up"]            # 力量/体质大幅强化
        }
    ),
    
    # --- 游侠 (Ranger) ---
    "ranger": Profession(
        prof_id="ranger",
        display_name="游侠",
        stat_bonus={
            "hp": 0,
            "max_energy": 0,
            "atk_multiplier": 1.1,
            "def_multiplier": 1.0
        },
        passive_tags=["eagle_eye"],  # 【鹰眼视野】攻击距离越远伤害越高
        relic_tag="ranger_lens",     # 【远射手的透镜】所有技能射程强制+3
        skill_unlock_table={
            1: ["long_range_shot"],   # 【远程射击】射程7，单体+猎人标记
            3: ["sniper_focus"],      # 遗物关联技能
            5: ["ultimate_snipe"],    # 【超远距离瞬狙】(待细化)
            7: ["agility_up"]         # 敏捷/感知大幅强化
        }
    ),
    
    # --- 重装卫士 (Heavy Guard) ---
    "heavy_guard": Profession(
        prof_id="heavy_guard",
        display_name="重装卫士",
        stat_bonus={
            "hp": 50,
            "max_energy": 0,
            "atk_multiplier": 0.9,
            "def_multiplier": 1.8
        },
        passive_tags=["steel_barrier"],  # 【钢铁壁垒】面向前方时格挡背后队友伤害
        relic_tag="tower_shield",        # 【巨塔之盾】高额固定格挡值，AOE减半
        skill_unlock_table={
            1: ["shield_bash"],          # 【盾击】单体攻击+小幅击退+重置冲锋冷却
            3: ["fortify"],              # 遗物关联技能
            5: ["immovable_as_mountain"],# 【不动如山】嘲讽全场+自身无敌1t+反射50%伤害
            7: ["constitution_up"]       # 体质/防御大幅强化
        }
    ),
    
    # --- 异教徒 (Heretic) ---
    "heretic": Profession(
        prof_id="heretic",
        display_name="异教徒",
        stat_bonus={
            "hp": -20,
            "max_energy": 0,
            "atk_multiplier": 1.6,
            "def_multiplier": 0.7
        },
        passive_tags=["bloodlust"],  # 【嗜血本能】每-5%HP → ATK+3%(上限+30%)
        relic_tag="blood_cloak",     # 【鲜血斗篷】HP<50%时额外获得20%减伤
        skill_unlock_table={
            1: ["blood_blade"],       # 【鲜血之刃】2.0x伤害+30%吸血
            3: ["hemomancy"],         # 遗物关联技能
            5: ["friendly_curse"],    # 【友伤禁咒】全屏毁灭打击+扣除自身20%HP
            7: ["intelligence_up"]    # 智力/幸运大幅强化
        }
    ),
    
    # --- 法师 (Mage) ---
    "mage": Profession(
        prof_id="mage",
        display_name="法师",
        stat_bonus={
            "hp": -30,
            "max_energy": 3,  # 基础能量槽位较多
            "atk_multiplier": 1.5,
            "def_multiplier": 0.7
        },
        passive_tags=["element_resonance"],  # 【元素共鸣】攻击敌人时吸取四大元素能量
        relic_tag="element_box",             # 【元素之匣】能量槽位+2，动态生成组合技能
        skill_unlock_table={
            1: ["arcane_missile"],    # 【奥术飞弹】消耗1点任意能量造成2.0x法伤+吸取1点属性
            3: ["dynamic_cast"],      # 遗物关联技能：动态组合施法
            5: ["perfect_copy"],      # 【完美复刻】复制本局出现过的强力技能(整局限1次)
            7: ["mana_cap_up"]        # 魔力上限大幅强化
        }
    ),
    
    # --- 盗贼 (Thief) ---
    "thief": Profession(
        prof_id="thief",
        display_name="盗贼",
        stat_bonus={
            "hp": -10,
            "max_energy": 0,
            "atk_multiplier": 1.3,
            "def_multiplier": 0.9
        },
        passive_tags=["shadow_walker"],  # 【暗影行者】背刺伤害 +60%
        relic_tag="night_assault_boots", # 【夜袭者之靴】移动后首攻增伤
        skill_unlock_table={
            1: ["armor_gap_attack"],     # 【甲缝袭击】1.2倍伤害 + 降低目标防御力
            3: ["night_strike_boost"],   # 遗物关联技能
            5: ["shadow_array"],         # 【无影杀阵】隐身3回合，期间普攻伤害翻倍
            7: ["luck_up"]               # 敏捷/幸运大幅强化
        }
    ),
    
    # --- 牧师 (Priest) ---
    "priest": Profession(
        prof_id="priest",
        display_name="牧师",
        stat_bonus={
            "hp": 30,
            "max_energy": 1,
            "atk_multiplier": 0.8,
            "def_multiplier": 1.1
        },
        passive_tags=["faith_power"],  # 【信仰之力】目标缺失HP比例越高治疗量越高
        relic_tag="holy_sigil",        # 【神圣徽记】周围1格队友每秒自动恢复少量HP
        skill_unlock_table={
            1: ["holy_heal"],          # 【治愈之光】单体治疗+清除1个Debuff
            3: ["regeneration"],       # 遗物关联技能
            5: ["divine_grace"],       # 【神之恩典】复活倒地队友并使其短暂无敌
            7: ["spirit_up"]           # 精神/体质大幅强化
        }
    ),
    
    # --- 德鲁伊 (Druid) ---
    "druid": Profession(
        prof_id="druid",
        display_name="德鲁伊",
        stat_bonus={
            "hp": 20,
            "max_energy": 2,
            "atk_multiplier": 1.1,
            "def_multiplier": 1.1
        },
        passive_tags=["wild_adaptation"],  # 【野性适应】每回合可切换一次战斗/支援形态
        relic_tag="world_tree_essence",    # 【世界树的精魄】切换形态冷却归零，切换时立即回复10%HP
        skill_unlock_table={
            1: ["form_skill"],         # 【形态技能】支援:治疗/护盾；战斗:高伤/控制
            3: ["form_switch_boost"],  # 遗物关联技能
            5: ["world_tree_descend"], # 【世界树降临】变身守护形态，根植地面，全员回血+嘲讽
            7: ["vitality_up"]         # 体质/魔力大幅强化
        }
    ),
    
    # --- 吟游诗人 (Bard) ---
    "bard": Profession(
        prof_id="bard",
        display_name="吟游诗人",
        stat_bonus={
            "hp": 0,
            "max_energy": 1,
            "atk_multiplier": 0.9,
            "def_multiplier": 1.0
        },
        passive_tags=["harmonic_rhythm"],  # 【和谐韵律】普攻为范围内队友叠加【节拍/灵感】层数
        relic_tag="golden_string_harp",    # 【金丝木竖琴】Buff类技能持续时间永久延长1回合
        skill_unlock_table={
            1: ["battle_anthem"],       # 【激昂战歌】消耗3层【节拍】使单体ATK提升50%
            3: ["buff_extend"],         # 遗物关联技能
            5: ["final_requiem"],       # 【终焉安魂曲】清空所有【节拍】对敌造成巨额法术伤害
            7: ["charisma_up"]          # 魅力/智力大幅强化
        }
    ),
    
    # ========================================================================
    # B. 游戏开发部成员定制配置 (Custom Characters)
    # ========================================================================
    
    # --- 柚子 (Yuzu) - 法师定制版 ---
    "yuzu_custom": Profession(
        prof_id="yuzu_custom",
        display_name="柚子·通关王者",
        stat_bonus={
            "hp": -30,
            "max_energy": 6,  # 基础3 + 遗物3 = 8格(实际显示时处理)
            "atk_multiplier": 1.65,  # 1.5 * 1.1(遗物加成)
            "def_multiplier": 0.7
        },
        passive_tags=["element_resonance"],
        relic_tag="uzqueen_championship_controller",  # 【UZQueen的冠军手柄】能量槽位+3，组合技能伤害倍率+10%
        skill_unlock_table={
            1: ["uzqueen_analysis"],  # 【UZQueen的解析眼】必中吸取能量，效率更高
            3: ["dynamic_cast_yuzu"], # 强化版动态组合
            5: ["hit_stop_freeze"],   # 【Hit Stop!·元素静止】复制技能+冻结目标1回合
            7: ["mana_cap_up"]
        }
    ),
    
    # --- 小绿 (Midori) - 德鲁伊定制版 ---
    "midori_custom": Profession(
        prof_id="midori_custom",
        display_name="小绿·原画师",
        stat_bonus={
            "hp": 20,
            "max_energy": 2,
            "atk_multiplier": 1.1,
            "def_multiplier": 1.1
        },
        passive_tags=["artistic_adaptation"],  # 【野性适应】表现为更换绘图笔刷/图层属性
        relic_tag="midori_drawing_set",        # 【小绿的画具套装】切换形态时立即恢复15%HP，下个技能效果+20%
        skill_unlock_table={
            1: ["cel_shading_mode"],   # 【赛璐璐清透】支援模式：艺术润色(治疗/护盾)
            2: ["pencil_sketch_mode"], # 【铅笔速写】战斗模式：线条切割(高伤/致盲)
            3: ["mode_switch_heal"],   # 遗物关联技能
            5: ["masterpiece_complete"], # 【杰作完成】变身画廊守护者形态，根植地面回血+保护
            7: ["vitality_up"]
        }
    ),
    
    # --- 桃井 (Momoi) - 吟游诗人定制版 ---
    "momoi_custom": Profession(
        prof_id="momoi_custom",
        display_name="桃井·编剧",
        stat_bonus={
            "hp": 0,
            "max_energy": 1,
            "atk_multiplier": 0.9,
            "def_multiplier": 1.0
        },
        passive_tags=["improvisation"],  # 【即兴创作】普攻为队友叠层，层数用于触发特效
        relic_tag="momoi_unfinished_script",  # 【桃井的烂尾剧本】可以让一个已使用的技能冷却立即刷新
        skill_unlock_table={
            1: ["tempo_buildup"],        # 【节拍积累】被动叠层
            3: ["cd_refresh"],           # 遗物关联技能：刷新CD
            5: ["final_act_performance"], # 【最终话演出】清空所有层数换取一次性爆发
            7: ["charisma_up"]
        }
    )
}


def get_profession(prof_id):
    """根据ID获取职业实例"""
    return PROFESSIONS_DATA.get(prof_id, None)


def list_all_professions():
    """列出所有可用职业"""
    return list(PROFESSIONS_DATA.values())


# ============================================================
# 辅助工具函数 (Helper Functions)
# ============================================================

def apply_stat_bonus(base_stats, profession):
    """
    应用职业的属性加成到基础属性上
    :param base_stats: dict, 例如 {"hp": 100, "atk": 50, "defense": 10, "max_energy": 5}
    :param profession: Profession 实例
    :return: dict, 修正后的属性
    """
    bonus = profession.stat_bonus
    
    result = base_stats.copy()
    
    # HP 修正 (加减法)
    if "hp" in bonus:
        result["hp"] += bonus["hp"]
    
    # 能量槽位修正 (加减法)
    if "max_energy" in bonus:
        result["max_energy"] += bonus["max_energy"]
    
    # 攻击力修正 (乘法)
    if "atk_multiplier" in bonus:
        result["atk"] = int(result["atk"] * bonus["atk_multiplier"])
    
    # 防御力修正 (乘法)
    if "def_multiplier" in bonus:
        result["defense"] = int(result["defense"] * bonus["def_multiplier"])
    
    return result


def check_passive_effect(unit, passive_tag, context):
    """
    检查并执行被动效果
    :param unit: 单位实例 (Player/Monster)
    :param passive_tag: 字符串，如 "charge", "eagle_eye", "element_resonance"
    :param context: dict, 包含触发上下文信息 (如移动距离、目标位置等)
    :return: dict, 被动效果产生的结果
    """
    result = {"triggered": False, "bonus": {}}
    
    if passive_tag == "charge":
        # 【冲锋】移动距离转化为攻击力加成 (%)
        move_distance = context.get("move_distance", 0)
        atk_bonus_pct = move_distance * 5  # 每移动1格，ATK+5%
        result["triggered"] = True
        result["bonus"]["atk_percent"] = atk_bonus_pct
        
    elif passive_tag == "eagle_eye":
        # 【鹰眼视野】攻击距离越远伤害越高 (%)
        distance = context.get("distance", 0)
        dmg_bonus_pct = distance * 3  # 每1距离，伤害+3%
        result["triggered"] = True
        result["bonus"]["damage_percent"] = dmg_bonus_pct
        
    elif passive_tag == "bloodlust":
        # 【嗜血本能】每-5%HP → ATK+3%(上限+30%)
        hp_ratio = unit.hp / unit.max_hp if unit.max_hp > 0 else 1
        lost_hp_pct = (1 - hp_ratio) * 100
        stacks = min(int(lost_hp_pct // 5), 6)  # 最多6层
        atk_bonus_pct = stacks * 3
        result["triggered"] = True
        result["bonus"]["atk_percent"] = atk_bonus_pct
        
    elif passive_tag == "shadow_walker":
        # 【暗影行者】背刺伤害 +60%
        # 注：此被动在背刺判定时生效，增加 60% 伤害加成
        result["triggered"] = True
        result["bonus"]["backstab_damage_percent"] = 60
            
    elif passive_tag == "faith_power":
        # 【信仰之力】目标缺失HP比例越高治疗量越高
        target_missing_hp_ratio = context.get("target_missing_hp_ratio", 0)
        heal_multiplier = 1.0 + target_missing_hp_ratio * 1.5  # 满血1.0x, 濒死2.5x
        result["triggered"] = True
        result["bonus"]["heal_multiplier"] = heal_multiplier
        
    return result


# ============================================================
# 特殊机制类 (Special Mechanics)
# ============================================================

class ElementPool:
    """
    法师专属：元素能量池管理类
    用于管理火(🔥)、水(💧)、气(💨)、土(🌍)四色能量球
    """
    ELEMENTS = {
        "FIRE": {"symbol": "🔥", "color": "red", "code": "F"},
        "WATER": {"symbol": "💧", "color": "blue", "code": "W"},
        "AIR": {"symbol": "💨", "color": "yellow", "code": "A"},
        "EARTH": {"symbol": "🌍", "color": "brown", "code": "E"}
    }
    
    def __init__(self, capacity=5):
        self.capacity = capacity
        self.elements = []  # 存储元素代号，如 ["F", "W", "F"]
    
    def add_element(self, element_code):
        """添加一个元素"""
        if len(self.elements) < self.capacity:
            self.elements.append(element_code)
            return True
        return False
    
    def remove_element(self, element_code):
        """移除一个元素"""
        if element_code in self.elements:
            self.elements.remove(element_code)
            return True
        return False
    
    def clear(self):
        """清空所有元素"""
        self.elements.clear()
    
    def get_combination(self):
        """获取当前持有的元素组合(排序后去重统计)"""
        from collections import Counter
        counts = Counter(self.elements)
        return dict(counts)
    
    def has_elements(self, required_codes):
        """检查是否拥有指定的元素集合"""
        from collections import Counter
        current_counts = Counter(self.elements)
        required_counts = Counter(required_codes)
        for code, count in required_counts.items():
            if current_counts.get(code, 0) < count:
                return False
        return True


class DruidModeStateMachine:
    """
    德鲁伊专属：形态状态机
    管理【赛璐璐清透】(支援)与【铅笔速写】(战斗)两种形态
    """
    MODE_SUPPORT = "cel_shading"   # 赛璐璐清透
    MODE_COMBAT = "pencil_sketch"  # 铅笔速写
    
    def __init__(self):
        self.current_mode = self.MODE_SUPPORT
        self.switch_cooldown = 0
    
    def switch_mode(self):
        """切换形态"""
        if self.switch_cooldown > 0:
            return False  # 冷却中，无法切换
        
        if self.current_mode == self.MODE_SUPPORT:
            self.current_mode = self.MODE_COMBAT
        else:
            self.current_mode = self.MODE_SUPPORT
        
        self.switch_cooldown = 1  # 设置1回合冷却
        return True
    
    def update_cooldown(self):
        """每回合结束时减少冷却"""
        if self.switch_cooldown > 0:
            self.switch_cooldown -= 1
    
    def is_support_mode(self):
        return self.current_mode == self.MODE_SUPPORT
    
    def is_combat_mode(self):
        return self.current_mode == self.MODE_COMBAT


class BardInspirationCounter:
    """
    吟游诗人专属：灵感/节拍层数计数器
    """
    def __init__(self, max_layers=10):
        self.max_layers = max_layers
        self.layers = 0
    
    def add_layer(self, amount=1):
        """增加层数"""
        old_layers = self.layers
        self.layers = min(self.layers + amount, self.max_layers)
        return self.layers - old_layers  # 返回实际增加的层数
    
    def consume_layers(self, amount):
        """消耗层数"""
        consumed = min(amount, self.layers)
        self.layers -= consumed
        return consumed
    
    def clear(self):
        """清空所有层数"""
        layers = self.layers
        self.layers = 0
        return layers