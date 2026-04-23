# skill.py
# 战斗模拟器 v12 - 技能定义模块
# 集中管理怪物和玩家的技能数据

# ================= 怪物技能库 =================
MONSTER_SKILLS = {
    # 通用基础技能
    "basic_attack": {"type": "damage", "multiplier": 1.0, "desc": "普通攻击"},
    "heavy_strike": {"type": "damage", "multiplier": 1.5, "desc": "蓄力重击"},
    "heal": {"type": "heal", "amount_ratio": 0.2, "desc": "自我治愈"},
    "shield": {"type": "buff", "stat": "defense", "value": 15, "duration": 2, "desc": "开启护盾"},
    "fireball": {"type": "damage", "multiplier": 1.8, "desc": "火焰球"},
    "cry": {"type": "debuff", "stat": "attack", "ratio": 0.8, "desc": "嚎叫 (降低敌方攻击)"},
    "berserk": {"type": "damage", "multiplier": 2.0, "desc": "狂暴一击"},
    
    # --- 独特机制技能 ---
    "life_steal": {"type": "lifesteal", "ratio": 0.5, "desc": "生命汲取 (吸取50%伤害的生命)"},
    "calculation": {"type": "crit_damage", "multiplier": 2.5, "chance": 0.3, "desc": "精确计算 (30%几率造成2.5倍暴击)"},
    
    # 新增独特技能
    "web_trap": {"type": "trap", "duration": 1, "desc": "蛛网束缚 (使一名玩家无法行动)"},
    "shell_defense": {"type": "buff", "stat": "defense_reflect", "value": 20, "duration": 2, "desc": "缩壳防御 (高防并反弹少量伤害)"},
    "phase_shift": {"type": "buff", "stat": "evade_next", "desc": "相位闪烁 (闪避下一次攻击)"},
    "earthquake": {"type": "aoe_damage", "multiplier": 0.8, "desc": "地震术 (对全员造成中等伤害)"},
    "emp_pulse": {"type": "debuff_all_stat", "stat": "defense", "ratio": 0.7, "desc": "电磁脉冲 (降低全队防御)"},
    "dragon_breath": {"type": "aoe_damage", "multiplier": 1.5, "desc": "龙息吐息 (对全员造成高额火焰伤害)"},
    "void_collapse": {"type": "cleanse_enemy", "desc": "视界崩坏 (清除我方增益效果)"},
    "acid_spit": {"type": "damage", "multiplier": 1.2, "desc": "酸液喷射"},
    "vine_lash": {"type": "aoe_damage", "multiplier": 0.6, "desc": "藤蔓横扫"},
    "static_discharge": {"type": "aoe_damage", "multiplier": 0.5, "desc": "静电释放"},
    "bone_shield": {"type": "buff", "stat": "defense", "value": 25, "duration": 3, "desc": "骨墙加固"},
    "throw_rock": {"type": "damage", "multiplier": 1.3, "desc": "投掷石块"},
    "charge": {"type": "damage", "multiplier": 2.0, "desc": "冲撞"},
    
    # --- 新增特色技能 ---
    "heavy_stomp": {"type": "damage", "multiplier": 1.2, "desc": "重踏"},
    "shadow_kick": {"type": "damage", "multiplier": 1.1, "desc": "影踢"},
    "acid_bite": {"type": "damage", "multiplier": 1.0, "desc": "酸液咬合"},
    "dragon_wing_slap": {"type": "damage", "multiplier": 1.5, "desc": "龙翼拍击"},
    "abyssal_gaze": {"type": "damage", "multiplier": 1.2, "desc": "深渊凝视"},
    "red_pen_mark": {"type": "damage", "multiplier": 1.2, "desc": "红笔批改"},
    "high_speed_calculation": {"type": "crit_damage", "multiplier": 2.5, "chance": 0.3, "desc": "高速计算"},
    "crush_claw": {"type": "damage", "multiplier": 1.3, "desc": "巨钳粉碎"},
    "scratch": {"type": "damage", "multiplier": 1.0, "desc": "猫爪乱抓"},
    "bite": {"type": "damage", "multiplier": 1.2, "desc": "撕咬"},
    "slime_bounce": {"type": "damage", "multiplier": 0.8, "desc": "弹跳撞击"},
    "horn_charge": {"type": "damage", "multiplier": 1.1, "desc": "角撞"},
    "emp_hammer": {"type": "damage", "multiplier": 1.3, "desc": "电磁重锤"},
    
    # --- 铁皮傀儡专属技能 ---
    "auto_repair": {"type": "special", "desc": "自我修复"},
}

# ================= 玩家技能元数据 =================
# 包含玩家技能的具体数值参数
PLAYER_SKILLS_META = {
    "alice": {
        "charge": {
            "desc": "光啊！", 
            "cost": 0, 
            "gain_energy": 1,
            "detail": "积攒光之能量，为释放终极必杀技做准备。"
        },
        "ex": {
            "desc": "世界的法则即将崩坏！光哟！！！" ,
            "base_multiplier": 5.91,
            "energy_bonus": 0.5,
            "crit_chance": 0.15,
            "crit_multiplier": 2.0,
            "detail": "消耗所有光之能量，释放出毁灭性的光之冲击！"
        },
        "physical": {
            "desc": "物理攻击",
            "variance": 5,
            "crit_chance": 0.1,
            "crit_multiplier": 1.5,
            "detail": "使用光之剑进行普通的物理斩击。"
        }
    },
    "yuzu": {
        "normal": {"desc": "普通攻击"},
        "super": {
            "desc": "通关指令·改",
            "stun_chance": 0.4,
            "once_per_battle": True
        }
    },
    "midori": {
        "heal": {"desc": "艺术润色", "min_heal": 20, "max_heal": 30}
    },
    "momoi": {
        "normal": {"desc": "普通攻击"},
        "debuff": {"desc": "剧情杀 (Debuff)", "chance": 0.3},
        "buff": {"desc": "剧情杀 (Buff)", "chance": 0.4}
    }
}