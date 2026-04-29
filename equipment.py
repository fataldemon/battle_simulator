# equipment.py
# 战斗模拟器 v2.4 - 装备/遗物系统模块
# 核心设计：每个职业在 Lv.3 解锁专属“遗物”，提供特殊的被动加成或机制改变
# 
# 【v2.4 重大更新】：
# 1. 引入“遗物”概念，替代原有的通用装备系统
# 2. 每个遗物绑定一个特定的 relic_tag，与 profession.py 中的职业定义对应
# 3. 包含通用职业遗物及游戏开发部成员专属遗物

class Equipment:
    """
    装备/遗物基类 v2.4
    包含：ID、显示名称、描述、效果类型、具体数值/逻辑标识
    """
    def __init__(self, equip_id, display_name, description, effect_type, effect_params=None):
        self.id = equip_id
        self.display_name = display_name
        self.description = description
        self.effect_type = effect_type  # 如 "stat_bonus", "passive_trigger", "special_mechanic"
        self.effect_params = effect_params or {}  # 存储具体参数，如 {"atk_bonus": 10}

    def apply_effect(self, unit, context):
        """
        应用遗物效果
        :param unit: 单位实例 (Player/Monster)
        :param context: dict, 包含触发上下文信息
        :return: dict, 效果产生的结果
        """
        result = {"triggered": False, "bonus": {}, "message": ""}
        
        if self.effect_type == "stat_bonus":
            # 永久性属性加成，通常在初始化时应用，此处简化为返回加成值
            result["triggered"] = True
            result["bonus"] = self.effect_params
            result["message"] = f"装备了【{self.display_name}】，获得属性加成。"
            
        elif self.effect_type == "passive_trigger":
            # 被动触发型，需要检查 context 是否满足条件
            condition_met = self.check_condition(context)
            if condition_met:
                result["triggered"] = True
                result["bonus"] = self.calculate_bonus(unit, context)
                result["message"] = f"【{self.display_name}】发动！"
                
        elif self.effect_type == "special_mechanic":
            # 特殊机制型，如增加槽位、改变状态机等
            result["triggered"] = True
            result["mechanic_change"] = self.effect_params
            result["message"] = f"激活了【{self.display_name}】的特殊机制。"
            
        return result

    def check_condition(self, context):
        """检查触发条件，子类可重写"""
        return True

    def calculate_bonus(self, unit, context):
        """计算具体加成，子类可重写"""
        return self.effect_params


# ============================================================
# 遗物数据定义 (v2.4 完整版)
# ============================================================

EQUIPMENT_DATA = {
    
    # ========================================================================
    # A. 通用职业遗物 (General Class Relics)
    # ========================================================================
    
    # --- 骑士 (Knight) ---
    "milan_armor": Equipment(
        equip_id="milan_armor",
        display_name="【米兰板甲】",
        description="冲锋时移动距离转化为减伤/格挡值",
        effect_type="passive_trigger",
        effect_params={"damage_reduction_per_move": 5} # 每移动1格，减伤+5%
    ),
    
    # --- 游侠 (Ranger) ---
    "ranger_lens": Equipment(
        equip_id="ranger_lens",
        display_name="【远射手的透镜】",
        description="所有技能射程强制 +3",
        effect_type="stat_bonus",
        effect_params={"range_bonus": 3}
    ),
    
    # --- 重装卫士 (Heavy Guard) ---
    "tower_shield": Equipment(
        equip_id="tower_shield",
        display_name="【巨塔之盾】",
        description="获得高额固定格挡值，受到AOE伤害减半",
        effect_type="stat_bonus",
        effect_params={"fixed_block_value": 50, "aoe_damage_multiplier": 0.5}
    ),
    
    # --- 异教徒 (Heretic) ---
    "blood_cloak": Equipment(
        equip_id="blood_cloak",
        display_name="【鲜血斗篷】",
        description="生命值低于50%时额外获得20%减伤",
        effect_type="passive_trigger",
        effect_params={"damage_reduction_pct": 20, "hp_threshold": 0.5}
    ),
    
    # --- 法师 (Mage) ---
    "element_box": Equipment(
        equip_id="element_box",
        display_name="【元素之匣】",
        description="能量槽位数 +2，动态生成组合技能",
        effect_type="special_mechanic",
        effect_params={"energy_capacity_bonus": 2, "enable_dynamic_cast": True}
    ),
    
    # --- 盗贼 (Thief) ---
    "night_assault_boots": Equipment(
        equip_id="night_assault_boots",
        display_name="【夜袭者之靴】",
        description="移动后首攻增伤",
        effect_type="passive_trigger",
        effect_params={"first_attack_after_move_bonus": 1.5} # 移动后第一次攻击伤害 x1.5
    ),
    
    # --- 牧师 (Priest) ---
    "holy_sigil": Equipment(
        equip_id="holy_sigil",
        display_name="【神圣徽记】",
        description="周围1格队友每秒自动恢复少量HP",
        effect_type="passive_trigger",
        effect_params={"heal_amount_per_turn": 5, "aoe_radius": 1}
    ),
    
    # --- 德鲁伊 (Druid) ---
    "world_tree_essence": Equipment(
        equip_id="world_tree_essence",
        display_name="【世界树的精魄】",
        description="切换形态冷却归零，切换时立即回复10%HP",
        effect_type="special_mechanic",
        effect_params={"reset_switch_cooldown": True, "heal_on_switch_pct": 0.1}
    ),
    
    # --- 吟游诗人 (Bard) ---
    "golden_string_harp": Equipment(
        equip_id="golden_string_harp",
        display_name="【金丝木竖琴】",
        description="Buff类技能持续时间永久延长1回合",
        effect_type="stat_bonus",
        effect_params={"buff_duration_bonus": 1}
    ),
    
    # ========================================================================
    # B. 游戏开发部成员专属遗物 (Custom Character Relics)
    # ========================================================================
    
    # --- 柚子 (Yuzu) ---
    "uzqueen_championship_controller": Equipment(
        equip_id="uzqueen_championship_controller",
        display_name="【UZQueen的冠军手柄】",
        description="能量槽位 +3（总计8格），且所有组合技能伤害倍率 +10%",
        effect_type="special_mechanic",
        effect_params={"energy_capacity_bonus": 3, "combo_skill_atk_multiplier": 1.1}
    ),
    
    # --- 小绿 (Midori) ---
    "midori_drawing_set": Equipment(
        equip_id="midori_drawing_set",
        display_name="【小绿的画具套装】",
        description="切换形态时立即恢复 15% HP，且下一个技能效果 +20%",
        effect_type="special_mechanic",
        effect_params={"heal_on_switch_pct": 0.15, "next_skill_power_bonus": 1.2}
    ),
    
    # --- 桃井 (Momoi) ---
    "momoi_unfinished_script": Equipment(
        equip_id="momoi_unfinished_script",
        display_name="【桃井的烂尾剧本】",
        description="可以让一个已使用的技能冷却立即刷新",
        effect_type="special_mechanic",
        effect_params={"allow_cd_refresh": True, "refresh_limit_per_game": 1}
    )
}


def get_equipment(equip_id):
    """根据ID获取装备实例"""
    return EQUIPMENT_DATA.get(equip_id, None)


def list_all_equipments():
    """列出所有可用装备"""
    return list(EQUIPMENT_DATA.values())


# ============================================================
# 辅助工具函数 (Helper Functions)
# ============================================================

def apply_relic_to_unit(unit, relic_tag):
    """
    将遗物绑定到单位上
    :param unit: 单位实例
    :param relic_tag: 遗物ID字符串
    :return: bool, 是否成功绑定
    """
    equipment = get_equipment(relic_tag)
    if equipment:
        unit.equipment = equipment
        # 如果是 stat_bonus 或 special_mechanic，可能需要在此处直接修改单位属性
        if equipment.effect_type == "stat_bonus":
            for key, value in equipment.effect_params.items():
                if hasattr(unit, key):
                    setattr(unit, key, getattr(unit, key) + value)
        return True
    return False