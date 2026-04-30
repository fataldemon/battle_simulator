# equipment.py
# 战斗模拟器 v44.4 - 装备系统与核心调度器 (Asset Restoration Build)
# 
# 【v44.4 更新说明】：
# 1. **重大修复**：从历史记录中找回了 v3.2 版本的完整资产库（职业核心、白蓝紫掉落池、Boss专属掉落）。
# 2. **技术融合**：将旧有的数据模型与新写的 `scan_and_trigger` 事件驱动引擎进行了无缝对接。
# 3. **功能增强**：保留了之前设计的动态触发逻辑，现在所有的遗物都能享受这套先进的管理系统了！
# 4. **特殊处理**：光之剑·超新星被定义为技能绑定型特殊装备。
# 
# ============================================================
# 轨道零：事件定义 (Event Definitions)
# ============================================================
from enum import Enum
import random

class BattleEvents(Enum):
    PRE_TURN = "pre_turn"           # 回合开始阶段 (适合回血、充能类装备)
    ON_ATTACK_CAST = "on_cast"      # 发动攻击/施法时 (适合增益、穿透类装备)
    ON_DAMAGE_DEALT = "on_dealt"    # 造成伤害后 (适合吸血、追击类装备)
    ON_DAMAGE_TAKEN = "on_taken"    # 受到伤害时 (适合反伤、护盾类装备)
    POST_MOVEMENT = "post_move"     # 移动完成后 (适合减速、陷阱类装备)


# ============================================================
# 轨道一：数据结构 (Data Structure)
# ============================================================
class Rarity(Enum):
    """装备品质枚举"""
    COMMON = "White"       
    UNCOMMON = "Green"     
    RARE = "Blue"          
    EPIC = "Purple"        
    LEGENDARY = "Orange"   

    @property
    def icon(self):
        icons = {"White": "⚪", "Green": "🟢", "Blue": "🔵", "Purple": "🟣", "Orange": "🟠"}
        return icons.get(self.value, "")


class Equipment:
    """通用装备基类 v44.4 - 完美兼容版"""
    def __init__(self, equip_id, name, description, effect_type, effect_params=None, rarity=Rarity.COMMON, source="drop", is_unique=False, trigger_event=None):
        self.id = equip_id
        self.name = name
        self.description = description
        self.effect_type = effect_type
        self.effect_params = effect_params or {}
        
        # === TRIGGER SYSTEM ===
        self.trigger_event = trigger_event 
        
        self.rarity = rarity           
        self.source = source             
        self.is_unique = is_unique      

    def __str__(self):
        unique_tag = "★" if self.is_unique else ""
        timing = f" [{self.trigger_event}]" if self.trigger_event else " [StatBuff/Mechanic]"
        return f"{self.rarity.icon}{unique_tag}【{self.name}】{timing}"


# ============================================================
# 轨道二：核心调度器 (The Manager Logic)
# ============================================================
def execute_effect_logic(owner_unit, enemy_unit_or_list, event_name, eq_instance):
    """
    【v44.4 核心】具体的效果执行逻辑路由器。
    """
    print(f"   🧪 装备管家介入：{owner_unit.name} 佩戴的 {eq_instance.name} 被激活！")
    
    etype = eq_instance.effect_type
    params = eq_instance.effect_params

    # --- 1. 受击反弹/反伤类 ---
    if etype == "thorns_damage" or etype == "high_block_aoe_reduce":
        reflect_dmg = int(params.get("value", 10))
        target_to_hurt = random.choice(enemy_unit_or_list) if isinstance(enemy_unit_or_list, list) else enemy_unit_or_list
        if hasattr(target_to_hurt, 'take_damage'):
            print(f"       -> ⚡ 反射伤害！敌方受到了 {reflect_dmg} 点伤害！")
            target_to_hurt.take_damage(reflect_dmg)

    # --- 2. 受伤治疗/吸血类 ---
    elif etype == "life_steal_on_hit" or etype == "switch_burst_buff":
        print(f"       -> ❤️ 生命汲取或形态切换回血！恢复了部分生命值！")
        owner_unit.hp = min(owner_unit.max_hp, owner_unit.hp + 15) 

    # --- 3. 概率致盲/眩晕 ---
    elif etype == "chance_blind_on_attack" or etype == "stun_attack_short_range":
        chance = params.get("chance", 0.3)
        targets = enemy_unit_or_list if isinstance(enemy_unit_or_list, list) else [enemy_unit_or_list]
        for target in targets:
            if random.random() < chance:
                if hasattr(target, 'is_blinded') or hasattr(target, 'is_stunned'):
                    target.is_blinded = True
                    print(f"       -> 👁️❌ 【装备特效】光效太强！敌人 {target.name} 被致盲了！")
            else:
                # 【v44.5 修复】增加未触发时的提示，提高透明度
                print(f"       -> 👁️✅ 【装备特效】敌人 {target.name} 躲过了强光！(未致盲)")

    # --- 4. 简单属性修正 (OnCast) ---
    elif etype == "attack_boost_next_turn" or etype == "super_magic_amp":
        boost_val = params.get("val", 10)
        owner_unit.atk += boost_val
        print(f"       -> ⚔️ 肾上腺素飙升/魔法增幅！攻击力提升 {boost_val}！")

    # --- 5. 特殊机制占位符 (对于复杂的如元素组合、CD刷新，这里先做日志记录) ---
    else:
        print(f"       -> 🔮 特殊机制触发：{etype} (等待主程序进一步处理)")


def scan_and_trigger(unit, current_event_enum, context_info=None):
    """总控台 (The Dispatcher)"""
    if not hasattr(unit, 'equipment_list'):
        return

    for item in unit.equipment_list:
        if item.trigger_event == current_event_enum:
            try:
                target = context_info.get("target") if context_info else None
                execute_effect_logic(unit, target, current_event_enum.value, item)
            except Exception as e:
                print(f"   ❌ 装备脚本运行错误：{item.name} ({str(e)})")


# ============================================================
# 轨道三：阶级传承 (Class Cores) - RESTORED from v3.2
# ============================================================
CLASS_CORE_REPLICAS = {
    "knight_core": Equipment("knight_core", "【钢铁之心】", "受到近身攻击时防御力大幅提升。", "defense_boost_on_melee_hit", {"def_pct": 0.3}, Rarity.LEGENDARY, "level_up"),
    "ranger_lens": Equipment("ranger_lens", "【远射手的透镜】", "所有技能射程强制 +3。", "range_bonus_global", {"val": 3}, Rarity.EPIC, "level_up"),
    "tower_shield": Equipment("tower_shield", "【巨塔之盾】", "获得高额固定格挡值，受到AOE伤害减半。", "high_block_aoe_reduce", {"fixed_block": 50, "aoe_mul": 0.5}, Rarity.EPIC, "level_up"),
    "blood_cloak": Equipment("blood_cloak", "【鲜血斗篷】", "生命值低于50%时额外获得20%减伤。", "low_hp_damage_reduction", {"thresh_hold": 0.5, "reduction_pct": 0.2}, Rarity.EPIC, "level_up"),
    "element_box": Equipment("element_box", "【元素之匣】", "能量槽位数+2，动态生成组合技能。", "magic_amp_slot_bonus", {"slot_add": 2, "enable_combo": True}, Rarity.EPIC, "level_up"),
    "assault_boots": Equipment("assault_boots", "【夜袭者之靴】", "移动后首攻增伤。", "first_attk_after_move_bonus", {"bonus_mul": 1.5}, Rarity.EPIC, "level_up"),
    "holy_sigil": Equipment("holy_sigil", "【神圣徽记】", "周围1格队友每秒自动恢复少量HP。", "aura_heal_adjacent", {"heal_amount": 5, "radius": 1}, Rarity.EPIC, "level_up"),
    "world_tree_essence": Equipment("world_tree_essence", "【世界树的精魄】", "切换形态冷却归零，切换时立即回复10%HP。", "switch_mechanic_enhanced", {"reset_cd": True, "heal_pct": 0.1}, Rarity.EPIC, "level_up"),
    "golden_harp": Equipment("golden_harp", "【金丝木竖琴】", "Buff类技能持续时间永久延长1回合。", "buff_duration_extender", {"add_turns": 1}, Rarity.EPIC, "level_up"),
    "yuzu_controller": Equipment("yuzu_controller", "【UZQueen的冠军手柄】", "能量槽位+3，组合技能伤害+10%。", "super_magic_amp", {"slot_add": 3, "damage_bonus": 0.1}, Rarity.LEGENDARY, "custom_level_up"),
    "midori_artset": Equipment("midori_artset", "【小绿的画具套装】", "切换形态时立即恢复15%HP，且下一技能效果+20%。", "switch_burst_buff", {"heal_pct": 0.15, "next_skill_mul": 1.2}, Rarity.LEGENDARY, "custom_level_up"),
    "momoi_script": Equipment("momoi_script", "【桃井的烂尾剧本】", "可以让一个已使用的技能冷却立即刷新。", "cooldown_manipulator", {"allow_refresh": True, "limit_per_game": 1}, Rarity.LEGENDARY, "custom_level_up"),
    # 【v44.4 修正】光之剑·超新星：技能绑定型特殊装备
    # 注：致盲效果由装备提供，而非技能本身
    "alice_sword_of_light": Equipment("alice_sword_of_light", "【光之剑·超新星】", "140kg电磁炮。【装备特效】普攻命中后30%几率致盲目标。赋予蓄力与EX大招权限。", "chance_blind_on_attack", {"chance": 0.3}, Rarity.LEGENDARY, "custom_level_up", trigger_event=BattleEvents.ON_DAMAGE_DEALT),
}


# ============================================================
# 轨道四：通用战场掠夺 (Expanded Loot Table) - RESTORED from v3.2
# ============================================================
LOOT_TABLE = [
    # ============================== ⚪ 白色垃圾 (35 Items) ==============================
    Equipment("ammo_case_mk1", "【MK1标准弹箱】", "普通的子弹，勉强够用。", "reload_speed_small", {}, Rarity.COMMON),
    Equipment("dirty_rag", "【肮脏的抹布】", "擦擦汗吧。略微提升体力上限。", "max_stamina_small", {}, Rarity.COMMON),
    Equipment("crushed_canned_food", "【压扁的压缩饼干】", "口感像石头，但能补充热量。", "heal_hp_tiny", {"val": 5}, Rarity.COMMON),
    Equipment("expired_antiseptic", "【过期的消毒水】", "味道很难闻。清理伤口时的痛苦稍微减轻点。", "dot_clean_chance_low", {}, Rarity.COMMON),
    Equipment("plastic_water_bottle", "【塑料水瓶】", "装了一半的水。没什么特别效果。", "none", {}, Rarity.COMMON),
    Equipment("cheap_energy_drink", "【廉价能量饮料】", "喝完心跳加速。下回合速度略微提升。", "speed_boost_next_turn", {"val": 2}, Rarity.COMMON),
    Equipment("bent_bayonet", "【弯曲的刺刀】", "弯了就扔了，居然还有人留着。", "phys_atk_minus", {"val": -2}, Rarity.COMMON),
    Equipment("fractured_scope", "【碎裂的红点镜】", "视野里有道裂痕。命中率微降，但威慑力微升。", "accuracy_penalty", {}, Rarity.COMMON),
    Equipment("worn_knee_pads", "【磨破的护膝】", "膝盖凉飕飕的。移速微降，防摔伤微升。", "move_penalty_resist_fall", {}, Rarity.COMMON),
    Equipment("taped_goggles", "【胶带缠的死鱼眼】", "防止强光致盲。", "blind_resist_tiny", {}, Rarity.COMMON),
    Equipment("rusty_door_lock", "【生锈的门锁】", "沉重的金属块。纯粹的面板加点。", "weight_increase_def_tiny", {}, Rarity.COMMON),
    Equipment("broken_calculation_sheet", "【破碎的计算纸】", "上面写着乱七八糟的数字。智力微升。", "int_stat_tiny", {}, Rarity.COMMON),
    Equipment("lost_id_card", "【丢失的证件】", "照片上的人看起来很倒霉。", "luck_decrease", {}, Rarity.COMMON),
    Equipment("military_flashlight_dying", "【快没电的手电筒】", "只能照亮脚下。侦查范围微缩。", "vision_reduce", {}, Rarity.COMMON),
    Equipment("gaming_magazine_torn", "【撕烂的游戏杂志】", "全是广告页。", "none", {}, Rarity.COMMON),
    Equipment("scrap_metal_a", "【A级废料】", "回收站里的常客。", "craft_material", {"type": "metal"}, Rarity.COMMON),
    Equipment("synthetic_leather_patch", "【合成皮革补丁】", "缝在衣服上的。", "armor_bonus_flat", {"val": 1}, Rarity.COMMON),
    Equipment("ball_bearing_set", "【滚珠轴承组】", "撒在地上到处滚。", "mobility_tiny", {}, Rarity.COMMON),
    Equipment("copper_wire_spool", "【铜线圈】", "导电用。", "tech_bonus_tiny", {}, Rarity.COMMON),
    Equipment("duct_tape_roll", "【大力胶一卷】", "万能修复材料。", "repair_tool_basic", {}, Rarity.COMMON),
    Equipment("car_key_missing_remote", "【没有遥控器的车钥匙】", "打不着火。", "none", {}, Rarity.COMMON),
    Equipment("pencil_with_no_lead", "【没芯的铅笔】", "只能用来戳人。", "improvised_weapon_weak", {"dmg": 1}, Rarity.COMMON),
    Equipment("coin_jar_cracked", "【裂开的存钱罐】", "里面的硬币洒了一地。金币+10。", "currency_gain", {"val": 10}, Rarity.COMMON),
    Equipment("umbrella_broken_frame", "【骨架断裂的雨伞】", "防不住雨，但能当棍子使。", "weapon_replace_rod", {}, Rarity.COMMON),
    Equipment("shoe_laces_pair", "【鞋带一对】", "绊马索的材料。", "trap_material_basic", {}, Rarity.COMMON),
    Equipment("old_newspaper_bundle", "【报纸一捆】", "垫桌腿用。防御+0.1。", "armor_bonus_trivial", {}, Rarity.COMMON),
    Equipment("empty_parachute_pack", "【空的降落伞包】", "很轻。负重上限-5。", "carry_limit_decrease", {"val": -5}, Rarity.COMMON),
    Equipment("card_deck_dirty", "【脏扑克牌】", "发牌员专用。", "gambling_prop_useless", {}, Rarity.COMMON),
    Equipment("school_textbook_vol1", "【课本第一卷】", "看了就困。", "fatigue_increase", {}, Rarity.COMMON),
    Equipment("lunchbox_dented", "【凹痕饭盒】", "中午食堂抢来的。", "morale_restore_small", {}, Rarity.COMMON),
    Equipment("gym_whistle_cracked", "【裂纹哨子】", "吹不出声。", "command_fail", {}, Rarity.COMMON),
    Equipment("marker_pen_red", "【红色马克笔】", "涂鸦利器。", "stealth_decrease_marking", {}, Rarity.COMMON),
    Equipment("rubber_band_thick", "【加厚橡皮筋】", "弹弓专用。", "slingshot_part", {}, Rarity.COMMON),
    Equipment("mirror_fragment", "【镜面碎片】", "反光强烈。", "distraction_reflect", {}, Rarity.COMMON),
    Equipment("brick_painted_blue", "【涂蓝油漆的砖头】", "伪装成补给箱。", "decoy_item", {}, Rarity.COMMON),
    Equipment("plastic_bag_white", "【白色塑料袋】", "飘得很快。", "none", {}, Rarity.COMMON),
    Equipment("safety_pin_bent", "【变曲的安全别针】", "开锁失败。", "lockpick_bad", {}, Rarity.COMMON),
    
    # ============================== 🔵 蓝色极品 (25 Items) ==============================
    Equipment("tactical_stock_hogue", "【霍格战术枪托】", "抵肩稳固。", "aim_stability_medium", {}, Rarity.RARE),
    Equipment("suppressor_standard", "【标准消音器】", "隐蔽性好。", "noise_reduce_high", {}, Rarity.RARE),
    Equipment("red_dot_scope_t1", "【T1红点瞄准镜】", "准星清晰。", "aim_time_reduce_med", {}, Rarity.RARE),
    Equipment("foregrip_vertical", "【垂直握把】", "压住后坐力。", "recoil_control_good", {}, Rarity.RARE),
    Equipment("flash_hSuppressor", "【灭焰装置】", "夜间作战必备。", "visibility_night_reduce", {}, Rarity.RARE),
    Equipment("extended_mag_30rnd", "【30发扩容弹匣】", "火力持久。", "clip_size_plus", {"val": 10}, Rarity.RARE),
    Equipment("taser_gadget_handheld", "【手持电击器】", "近战眩晕小玩具。", "stun_attack_short_range", {}, Rarity.RARE),
    Equipment("smoke_grenade_pin", "【烟雾弹引信】", "随时可以引爆。", "smoke_ability_unlock", {}, Rarity.RARE),
    Equipment("breaching_ram_light", "【轻型撞门槌】", "破门速度快。", "deploy_speed_fast", {}, Rarity.RARE),
    Equipment("digital_watch_gps", "【GPS数字表】", "定位精准。", "nav_accuracy_high", {}, Rarity.RARE),
    Equipment("kevlar_weave_patch", "【凯夫拉编织补片】", "防弹插板升级。", "bullet_resist_mod", {}, Rarity.RARE),
    Equipment("ceramic_plate_shard", "【陶瓷防弹片】", "硬度很高。", "blunt_damage_absorb", {}, Rarity.RARE),
    Equipment("carbon_fiber_hinge", "【碳纤维铰链】", "轻量化关节。", "weight_reduction_armor", {}, Rarity.RARE),
    Equipment("shock_absorber_mount", "【减震支架】", "减少震动。", "concussion_prevention", {}, Rarity.RARE),
    Equipment("thermal_insulation_layer", "【隔热层】", "防火阻燃。", "fire_resist_med", {}, Rarity.RARE),
    Equipment("signal_scrambler_chip", "【信号干扰芯片】", "雷达隐身。", "radar_signature_hide", {}, Rarity.RARE),
    Equipment("battery_pack_li_ion", "【锂电池包】", "续航增强。", "energy_regeneraton_up", {}, Rarity.RARE),
    Equipment("usb_drive_encrypted", "【加密U盘】", "内含机密？", "intel_gathering_buff", {}, Rarity.RARE),
    Equipment("drone_motor_mini", "【微型无人机马达】", "嗡嗡作响。", "mobility_flight_assist", {}, Rarity.RARE),
    Equipment("headlamp_rechargable", "【充电头灯】", "解放双手。", "hands_free_work_bonus", {}, Rarity.RARE),
    Equipment("multi_tool_levenger", "【瑞士军刀】", "什么都能修。", "utility_action_fast", {}, Rarity.RARE),
    Equipment("paracord_rope_strong", "【高强度伞绳】", "捆绑救援用。", "tie_down_extra_strong", {}, Rarity.RARE),
    Equipment("water_filter_bottle", "【净水滤水壶】", "野外生存神器。", "drink_from_source_safe", {}, Rarity.RARE),
    Equipment("first_aid_kit_prof", "【专业急救包】", "止血效果好。", "bleed_stop_fast", {}, Rarity.RARE),
    Equipment("camo_netting_square", "【迷彩网】", "融入环境。", "concealment_bonus_forest", {}, Rarity.RARE),

    # ============================== 🟣 紫色强力 (12 Items) ==============================
    Equipment("exo_leg_actuator_v2", "【外骨骼腿部液压杆v2】", "飞跃障碍。", "dash_distance_double", {}, Rarity.EPIC),
    Equipment("smart_targeting_ai", "【AI智能靶心系统】", "自动锁定弱点。", "weak_spot_auto_detect", {}, Rarity.EPIC),
    Equipment("quantum_comm_link", "【量子通讯链接】", "延迟为0。", "info_sync_instant", {}, Rarity.EPIC),
    Equipment("nano_fiber_mesh_full", "【全覆盖纳米纤维】", "轻便如衣，坚如钢铁。", "agi_high_def_medium", {}, Rarity.EPIC),
    Equipment("reactor_micro_core", "【微型反应堆核心】", "永不枯竭的动力。", "stamina_infinite_gen", {}, Rarity.EPIC),
    Equipment("active_camouflage_skin", "【主动变色龙蒙皮】", "光学隐身。", "stealth_optical_active", {}, Rarity.EPIC),
    Equipment("holographic_decoy_proj", "【全息诱饵投影器】", "吸引仇恨。", "taunt_technology_based", {}, Rarity.EPIC),
    Equipment("gravity_manip_cell", "【重力操控单元】", "让物体失重。", "physics_anomaly_zone", {}, Rarity.EPIC),
    Equipment("neural_accel_patch", "【神经加速贴片】", "思维变快。", "reaction_time_halved", {}, Rarity.EPIC),
    Equipment("plasma_cutting_edge", "【等离子切割刃】", "削铁如泥。", "armour_ignoring_cut", {}, Rarity.EPIC),
    Equipment("bio_feedback_monitor", "【生物反馈监测仪】", "身体数据可视化。", "status_visibility_full_self", {}, Rarity.EPIC),
    Equipment("sonic_pulse_emitter", "【声波脉冲发射器】", "震碎内脏。", "internal_damage_ignore_def", {}, Rarity.EPIC),
]

# --- 轨道五：Boss专属掉落 (Boss Specific Drops) ---
BOSS_DROP_TABLE = {
    "ancient_dragon": [
        Equipment("flame_emperor_crown", "【炎帝冠冕】", "免疫火焰伤害，且火系技能伤害翻倍。", "immune_fire_double_dmg", {}, Rarity.LEGENDARY, "boss_kill", is_unique=True),
        Equipment("dragon_tail_whip", "【苍龙之尾】", "一条活着的尾巴武器。每回合自动挥动一次。", "auto_attack_minion", {"dmg": 20, "range": 2}, Rarity.LEGENDARY, "boss_kill", is_unique=True)
    ],
    "void_devourer": [
        Equipment("void_eye", "【虚空之眼】", "看穿虚空的魔眼。攻击无视目标20%防御。", "armor_penetration", {"pct": 0.2}, Rarity.LEGENDARY, "boss_kill", is_unique=True),
        Equipment("entropy_staff", "【熵增权杖】", "使周围的物质加速腐朽。攻击附加高额度腐蚀DoT。", "heavy_corrosion_dot", {"dmg": 25}, Rarity.LEGENDARY, "boss_kill", is_unique=True)
    ],
    "mecha_spider_queen": [
        Equipment("spider_acid_gland", "【剧毒腺体】", "让所有物理攻击附带中毒效果。", "poison_on_phys_atk", {}, Rarity.EPIC, "boss_kill", is_unique=True)
    ],
    "yuuka_final": [
        Equipment("red_calculator", "【红色的正义计算器】", "持有者不仅会不断计算敌人的弱点，还会不断扣钱。攻击力+100%，每回合金币-100。", "atk_boost_gold_drain", {"atk_mul": 1.0, "gold_cost": 100}, Rarity.LEGENDARY, "boss_kill", is_unique=True)
    ]
}

# ============================================================
# 辅助工具函数 (Helper Functions) - RESTORED
# ============================================================
def get_class_core(profession_id):
    core_map = {
        "knight": "knight_core", "ranger": "ranger_lens", "heavy_guard": "tower_shield",
        "heretic": "blood_cloak", "mage": "element_box", "thief": "assault_boots",
        "priest": "holy_sigil", "druid": "world_tree_essence", "bard": "golden_harp",
        "alice": "alice_sword_of_light", "yuzu": "yuzu_controller", "midori": "midori_artset", "momoi": "momoi_script"
    }
    cid = core_map.get(profession_id)
    if cid:
        return CLASS_CORE_REPLICAS.get(cid)
    return None

def check_drop_conflict(inventory_ids, potential_drop_item):
    if potential_drop_item.is_unique:
        if potential_drop_item.id in inventory_ids:
            return False  
    return True