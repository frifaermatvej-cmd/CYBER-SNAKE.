import math
import json
import os
import re
import pygame
import random
import sys
import time
from array import array

# Инициализация Pygame и миксера
pygame.init()
# Перезапускаем микшер в нужном формате: это убирает несоответствие аудиобуфера.
try:
    pygame.mixer.quit()
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
except pygame.error:
    pass

# Константы (карта 800x800)
WIDTH, HEIGHT = 800, 800
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

# Цвета объектов
SNAKE_HEAD_COLOR = (0, 255, 140)
GOLD_COLOR = (255, 215, 0)
FOOD_COLOR = (255, 50, 90)
ARMOR_BONUS_COLOR = (180, 50, 240)
MEDKIT_COLOR = (50, 240, 120)
SLOWMO_COLOR = (0, 200, 255)
MAGNET_COLOR = (255, 140, 0)
FREEZE_COLOR = (100, 220, 255)
SHIELD_COLOR = (255, 255, 255)
NUKES_COLOR = (255, 100, 0)
SPIDER_COLOR = (170, 60, 220)
MINI_SPIDER_COLOR = (200, 100, 255)
MINE_COLOR = (255, 60, 60)
LASER_COLOR = (255, 0, 100)
TEXT_COLOR = (240, 240, 255)
HP_BAR_COLOR = (50, 220, 80)
ARMOR_BAR_COLOR = (160, 160, 180)
HP_BG_COLOR = (60, 20, 30)
ULT_BAR_COLOR = (0, 180, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CYBER SNAKE | Developed by MONZAY")
clock = pygame.time.Clock()

# Чёткий системный шрифт с хорошей поддержкой кириллицы.
try:
    font_small = pygame.font.SysFont("Segoe UI", 18, bold=True)
    font_tiny = pygame.font.SysFont("Segoe UI", 14)
    font_large = pygame.font.SysFont("Segoe UI", 32, bold=True)
    font_title = pygame.font.SysFont("Segoe UI", 36, bold=True)
except Exception:
    font_small = pygame.font.Font(None, 18)
    font_tiny = pygame.font.Font(None, 14)
    font_large = pygame.font.Font(None, 32)
    font_title = pygame.font.Font(None, 36)

SAVE_FILE = "save_data.json"


def draw_dev_watermarks(surface, show_side_author=True):
    # Надпись снизу поднята выше, чтобы её было отлично видно
    dev_text = font_tiny.render("[ ИГРА В СТАДИИ РАЗРАБОТКИ ]", True, (255, 220, 0))
    surface.blit(dev_text, (WIDTH // 2 - dev_text.get_width() // 2, HEIGHT - 35))

    # Автор — обычная надпись без рамки и фона.
    if show_side_author:
        author_surf = font_tiny.render("by. Monzay", True, (0, 255, 200))
        surface.blit(author_surf, (WIDTH - author_surf.get_width() - 18, 14))


def draw_coin_icon(surface, x, y, size=16):
    pygame.draw.circle(surface, (200, 160, 0), (x + size // 2, y + size // 2 + 1), size // 2)
    pygame.draw.circle(surface, GOLD_COLOR, (x + size // 2, y + size // 2), size // 2 - 1)
    pygame.draw.circle(surface, (255, 240, 150), (x + size // 2 - 2, y + size // 2 - 2), 2)


def draw_heart_icon(surface, x, y, size=16):
    hx, hy = x + size // 2, y + size // 2
    pygame.draw.circle(surface, (220, 20, 60), (hx - 4, hy - 2), 4)
    pygame.draw.circle(surface, (220, 20, 60), (hx + 4, hy - 2), 4)
    points = [(hx - size // 2, hy), (hx + size // 2, hy), (hx, y + size // 2 + 4)]
    pygame.draw.polygon(surface, (220, 20, 60), points)
    pygame.draw.circle(surface, (255, 120, 140), (hx - 4, hy - 3), 1)


def load_game_data():
    default_data = {
        "player_name": "",
        "language": "ru",
        "coins": 0,
        "high_score": 0,
        "max_time_survived": 0,
        "max_bosses_killed": 0,
        "max_coins_earned": 0,
        "max_combo": 1,
        "current_skin": "classic",
        "unlocked_skins": ["classic"],
        "current_theme": "cosmos",
        "unlocked_themes": ["cosmos"],
        "current_accessory": "none",
        "unlocked_accessories": ["none"],
        "lives_count": 0,
        "last_daily_reset": time.time(),
        "achievements": {
            "first_spider": False,
            "survivor_60": False,
            "rich_500": False,
            "combo_5": False,
            "apocalypse_survive": False
        },
        "daily_quests": {
            "eat_apples": {"progress": 0, "target": 15, "reward": 60, "done": False},
            "survive_45": {"progress": 0, "target": 45, "reward": 80, "done": False},
            "kill_boss_daily": {"progress": 0, "target": 1, "reward": 100, "done": False},
            "collect_bonuses": {"progress": 0, "target": 5, "reward": 70, "done": False},
            "earn_coins": {"progress": 0, "target": 50, "reward": 90, "done": False},
            "reach_combo_3": {"progress": 0, "target": 3, "reward": 75, "done": False}
        },
        "global_quests": {
            "global_bosses": {"progress": 0, "target": 15, "reward_coins": 500, "reward_skin": "phoenix",
                              "done": False},
            "global_score": {"progress": 0, "target": 2000, "reward_coins": 750, "reward_skin": "crystal_king",
                             "done": False},
            "global_survival": {"progress": 0, "target": 300, "reward_coins": 400, "reward_skin": "ghost",
                                "done": False},
            "global_apples": {"progress": 0, "target": 250, "reward_coins": 600, "reward_skin": "pumpkin",
                              "done": False}
        },
        "stats": {
            "total_bosses_killed": 0,
            "total_apples_eaten": 0,
            "total_time_survived": 0,
            "total_bonuses_collected": 0
        }
    }

    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                for key in default_data:
                    if key not in data:
                        data[key] = default_data[key]
                # Сохраняем прогресс ежедневных заданий из файла.
                # Новые задания из будущих версий добавляем без сброса старых.
                saved_daily = data.get("daily_quests", {})
                merged_daily = {}
                for qkey, qdefault in default_data["daily_quests"].items():
                    merged_daily[qkey] = saved_daily.get(qkey, qdefault.copy())
                    for field, value in qdefault.items():
                        merged_daily[qkey].setdefault(field, value)
                data["daily_quests"] = merged_daily
                return data
        except Exception:
            pass
    return default_data


def save_game_data(data):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


game_data = load_game_data()


def check_daily_reset():
    now = time.time()
    if now - game_data.get("last_daily_reset", now) >= 21600:
        game_data["last_daily_reset"] = now
        for qkey in game_data["daily_quests"]:
            game_data["daily_quests"][qkey]["progress"] = 0
            game_data["daily_quests"][qkey]["done"] = False
        save_game_data(game_data)


check_daily_reset()

ACHIEVEMENTS_LIST = [
    {"id": "first_spider", "name": "Первый охотник", "desc": "Победить первого босса-паука", "reward": 50},
    {"id": "survivor_60", "name": "Марафонец", "desc": "Прожить в забеге более 60 секунд", "reward": 100},
    {"id": "rich_500", "name": "Магнат", "desc": "Накопить суммарно 500 монет", "reward": 150},
    {"id": "combo_5", "name": "Комбо-мастер", "desc": "Достигнуть максимального комбо x5", "reward": 120},
    {"id": "apocalypse_survive", "name": "Герой Апокалипсиса", "desc": "Сыграть и выжить в режиме Апокалипсис",
     "reward": 200}
]

GLOBAL_QUESTS_INFO = {
    "global_bosses": {"name": "Истребитель боссов", "desc": "Победить 15 пауков-боссов за всё время",
                      "reward_skin": "phoenix", "skin_name": "Неоновый Феникс"},
    "global_score": {"name": "Легендарный счет", "desc": "Набрать 2000 очков в одном забеге",
                     "reward_skin": "crystal_king", "skin_name": "Королевский Кристалл"},
    "global_survival": {"name": "Бессмертный", "desc": "Суммарно прожить 300 секунд в забегах", "reward_skin": "ghost",
                        "skin_name": "Ледяной Призрак"},
    "global_apples": {"name": "Яблочный маньяк", "desc": "Съесть 250 яблок за всё время", "reward_skin": "pumpkin",
                      "skin_name": "Тыквоголовый"}
}

CASE_REWARDS = [
    {"id": "poop", "name": "💩 Какашка", "type": "joke", "weight": 35, "chance": "35%", "congrats": "Упс! Не повезло!",
     "desc": "Обычная виртуальная какашка."},
    {"id": "coins_30", "name": "💰 Пакет монет (+30)", "type": "coins", "amount": 30, "weight": 25, "chance": "25%",
     "congrats": "Неплохо!", "desc": "+30 монет в кошелек."},
    {"id": "extra_life", "name": "💊 Вторая жизнь (+1)", "type": "life", "weight": 15, "chance": "15%",
     "congrats": "Удача!", "desc": "Лишняя жизнь для забегов."},
    {"id": "coins_100", "name": "💰 Мешок монет (+100)", "type": "coins", "amount": 100, "weight": 10, "chance": "10%",
     "congrats": "Отличный улов!", "desc": "+100 монет в копилку."},
    {"id": "grass", "name": "🌿 Поле: Кибер-Трава", "type": "theme", "weight": 6, "chance": "6%",
     "congrats": "Редкая находка!", "desc": "Кибер-растительность разблокирована."},
    {"id": "sunset", "name": "🌆 Поле: Неоновый закат", "type": "theme", "weight": 4, "chance": "4%",
     "congrats": "Эпический дроп!", "desc": "Неоновый закат разблокирован."},
    {"id": "cyber", "name": "🤖 Скин: Киберпанк", "type": "skin", "weight": 3, "chance": "3%", "congrats": "Потрясающе!",
     "desc": "Стильный скин разблокирован."},
    {"id": "zeus", "name": "⚡ Скин: Кибер-Зевс", "type": "skin", "weight": 1.5, "chance": "1.5%",
     "congrats": "Легендарный выигрыш!", "desc": "Сила молний в твоих руках."},
    {"id": "void_lord", "name": "🕳️ Скин: Повелитель Бездны", "type": "skin", "weight": 0.5, "chance": "0.5%",
     "congrats": "БОЖЕСТВЕННЫЙ ДРОП!", "desc": "Редчайший скин Бездны."}
]




def draw_case_reward_icon(surface, reward, x, y, size=24):
    """Небольшая понятная иконка награды, нарисованная средствами Pygame."""
    rid = reward.get("id", "")
    kind = reward.get("type", "")
    rarity_colors = {
        "poop": (150, 105, 75), "coins_30": (245, 190, 45),
        "extra_life": (255, 90, 125), "coins_100": (255, 165, 35),
        "grass": (65, 220, 125), "sunset": (255, 105, 180),
        "cyber": (55, 205, 255), "zeus": (255, 220, 65),
        "void_lord": (185, 90, 255),
    }
    color = rarity_colors.get(rid, (100, 190, 255))
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(surface, (23, 28, 52), rect, border_radius=6)
    pygame.draw.rect(surface, color, rect, 2, border_radius=6)
    cx, cy = rect.center

    if rid in ("coins_30", "coins_100"):
        pygame.draw.circle(surface, color, (cx, cy), size // 3)
        pygame.draw.circle(surface, (255, 240, 150), (cx, cy), size // 4, 2)
        # Небольшой знак монеты
        txt = font_tiny.render("$", True, (255, 255, 230))
        surface.blit(txt, txt.get_rect(center=(cx, cy)))
    elif rid == "extra_life":
        # Сердце из двух кругов и треугольника
        pygame.draw.circle(surface, color, (cx - 4, cy - 2), 5)
        pygame.draw.circle(surface, color, (cx + 4, cy - 2), 5)
        pygame.draw.polygon(surface, color, [(cx - 9, cy), (cx + 9, cy), (cx, cy + 10)])
    elif rid == "grass":
        pygame.draw.line(surface, color, (cx, y + size - 5), (cx - 5, y + 6), 3)
        pygame.draw.ellipse(surface, color, (cx - 10, cy - 6, 9, 5))
        pygame.draw.ellipse(surface, color, (cx + 1, cy - 2, 9, 5))
    elif rid == "sunset":
        pygame.draw.circle(surface, color, (cx, cy - 2), 6)
        for k in range(3):
            pygame.draw.line(surface, color, (x + 5, y + 7 + k * 5), (x + size - 5, y + 7 + k * 5), 1)
    elif rid == "cyber":
        pygame.draw.rect(surface, color, (cx - 7, cy - 7, 14, 14), border_radius=3)
        pygame.draw.circle(surface, (15, 20, 40), (cx - 3, cy - 1), 2)
        pygame.draw.circle(surface, (15, 20, 40), (cx + 3, cy - 1), 2)
        pygame.draw.line(surface, (15, 20, 40), (cx - 3, cy + 4), (cx + 3, cy + 4), 2)
    elif rid == "zeus":
        pygame.draw.polygon(surface, color, [(cx + 2, y + 3), (cx - 6, cy), (cx, cy), (cx - 3, y + size - 3), (cx + 7, cy - 1), (cx + 1, cy - 1)])
    elif rid == "void_lord":
        pygame.draw.circle(surface, color, (cx, cy), 8, 2)
        pygame.draw.circle(surface, (15, 12, 35), (cx, cy), 4)
        pygame.draw.circle(surface, (240, 220, 255), (cx, cy), 1)
    else:
        # Иконка шутливой награды
        pygame.draw.circle(surface, color, (cx, cy), 7)
        pygame.draw.circle(surface, (255, 235, 210), (cx - 3, cy - 2), 1)
        pygame.draw.circle(surface, (255, 235, 210), (cx + 3, cy - 2), 1)
        pygame.draw.arc(surface, (255, 235, 210), (cx - 4, cy, 8, 6), 3.2, 6.1, 1)

def roll_case():
    total_weight = sum(r["weight"] for r in CASE_REWARDS)
    pick = random.uniform(0, total_weight)
    current = 0
    for r in CASE_REWARDS:
        current += r["weight"]
        if pick <= current:
            return r
    return CASE_REWARDS[0]


def update_quest_progress(quest_type, amount=1, score_val=0, match_time=0):
    dq = game_data["daily_quests"]
    if quest_type == "apple" and not dq["eat_apples"]["done"]:
        dq["eat_apples"]["progress"] = min(dq["eat_apples"]["target"], dq["eat_apples"]["progress"] + amount)
        if dq["eat_apples"]["progress"] >= dq["eat_apples"]["target"]:
            dq["eat_apples"]["done"] = True
            game_data["coins"] += dq["eat_apples"]["reward"]
    elif quest_type == "survive" and not dq["survive_45"]["done"]:
        dq["survive_45"]["progress"] = min(dq["survive_45"]["target"], match_time)
        if dq["survive_45"]["progress"] >= dq["survive_45"]["target"]:
            dq["survive_45"]["done"] = True
            game_data["coins"] += dq["survive_45"]["reward"]
    elif quest_type == "boss" and not dq["kill_boss_daily"]["done"]:
        dq["kill_boss_daily"]["progress"] = min(dq["kill_boss_daily"]["target"],
                                                dq["kill_boss_daily"]["progress"] + amount)
        if dq["kill_boss_daily"]["progress"] >= dq["kill_boss_daily"]["target"]:
            dq["kill_boss_daily"]["done"] = True
            game_data["coins"] += dq["kill_boss_daily"]["reward"]
    elif quest_type == "bonus" and not dq["collect_bonuses"]["done"]:
        dq["collect_bonuses"]["progress"] = min(dq["collect_bonuses"]["target"],
                                                dq["collect_bonuses"]["progress"] + amount)
        if dq["collect_bonuses"]["progress"] >= dq["collect_bonuses"]["target"]:
            dq["collect_bonuses"]["done"] = True
            game_data["coins"] += dq["collect_bonuses"]["reward"]
    elif quest_type == "coins" and not dq["earn_coins"]["done"]:
        dq["earn_coins"]["progress"] = min(dq["earn_coins"]["target"], dq["earn_coins"]["progress"] + amount)
        if dq["earn_coins"]["progress"] >= dq["earn_coins"]["target"]:
            dq["earn_coins"]["done"] = True
            game_data["coins"] += dq["earn_coins"]["reward"]
    elif quest_type == "combo" and not dq["reach_combo_3"]["done"]:
        dq["reach_combo_3"]["progress"] = min(dq["reach_combo_3"]["target"],
                                              max(dq["reach_combo_3"]["progress"], amount))
        if dq["reach_combo_3"]["progress"] >= dq["reach_combo_3"]["target"]:
            dq["reach_combo_3"]["done"] = True
            game_data["coins"] += dq["reach_combo_3"]["reward"]

    gq = game_data["global_quests"]
    st = game_data["stats"]
    if quest_type == "boss":
        st["total_bosses_killed"] += amount
        if not gq["global_bosses"]["done"]:
            gq["global_bosses"]["progress"] = min(gq["global_bosses"]["target"], st["total_bosses_killed"])
            if gq["global_bosses"]["progress"] >= gq["global_bosses"]["target"]:
                gq["global_bosses"]["done"] = True
                game_data["coins"] += gq["global_bosses"]["reward_coins"]
                if "phoenix" not in game_data["unlocked_skins"]:
                    game_data["unlocked_skins"].append("phoenix")
    elif quest_type == "apple":
        st["total_apples_eaten"] += amount
        if not gq["global_apples"]["done"]:
            gq["global_apples"]["progress"] = min(gq["global_apples"]["target"], st["total_apples_eaten"])
            if gq["global_apples"]["progress"] >= gq["global_apples"]["target"]:
                gq["global_apples"]["done"] = True
                game_data["coins"] += gq["global_apples"]["reward_coins"]
                if "pumpkin" not in game_data["unlocked_skins"]:
                    game_data["unlocked_skins"].append("pumpkin")
    elif quest_type == "score_check":
        if not gq["global_score"]["done"]:
            gq["global_score"]["progress"] = max(gq["global_score"]["progress"], score_val)
            if gq["global_score"]["progress"] >= gq["global_score"]["target"]:
                gq["global_score"]["done"] = True
                game_data["coins"] += gq["global_score"]["reward_coins"]
                if "crystal_king" not in game_data["unlocked_skins"]:
                    game_data["unlocked_skins"].append("crystal_king")
    elif quest_type == "survival_check":
        st["total_time_survived"] += amount
        if not gq["global_survival"]["done"]:
            gq["global_survival"]["progress"] = min(gq["global_survival"]["target"], st["total_time_survived"])
            if gq["global_survival"]["progress"] >= gq["global_survival"]["target"]:
                gq["global_survival"]["done"] = True
                game_data["coins"] += gq["global_survival"]["reward_coins"]
                if "ghost" not in game_data["unlocked_skins"]:
                    game_data["unlocked_skins"].append("ghost")

    save_game_data(game_data)


def check_achievements(match_time, bosses_killed, combo_val, is_apocalypse=False):
    unlocked_any = False
    ach = game_data["achievements"]

    if bosses_killed >= 1 and not ach.get("first_spider"):
        ach["first_spider"] = True
        game_data["coins"] += 50
        unlocked_any = True
    if match_time >= 60 and not ach.get("survivor_60"):
        ach["survivor_60"] = True
        game_data["coins"] += 100
        unlocked_any = True
    if game_data["coins"] >= 500 and not ach.get("rich_500"):
        ach["rich_500"] = True
        game_data["coins"] += 150
        unlocked_any = True
    if combo_val >= 5 and not ach.get("combo_5"):
        ach["combo_5"] = True
        game_data["coins"] += 120
        unlocked_any = True
    if is_apocalypse and not ach.get("apocalypse_survive"):
        ach["apocalypse_survive"] = True
        game_data["coins"] += 200
        unlocked_any = True

    if unlocked_any:
        save_game_data(game_data)
        play_sound("cashier")


THEMES = {
    "cosmos": {"name": "🌌 Неоновый космос", "price": 0, "bg": (12, 12, 22), "grid": (22, 22, 38)},
    "grass": {"name": "🌿 Кибер-Трава", "price": 150, "bg": (10, 22, 15), "grid": (20, 45, 30)},
    "matrix": {"name": "⚡ Цифровой матрикс", "price": 300, "bg": (15, 15, 15), "grid": (30, 30, 30)},
    "sunset": {"name": "🌆 Неоновый закат", "price": 450, "bg": (25, 12, 30), "grid": (45, 22, 55)},
    "lava": {"name": "🔥 Лавовая бездна", "price": 600, "bg": (30, 10, 10), "grid": (55, 20, 20)}
}

SHOP_ITEMS = {
    "skins": sorted([
        {"id": "classic", "name": "Скин: Неоновый", "price": 0, "type": "skin", "head": (0, 255, 140),
         "body": (0, 190, 100), "ability": "Стандартный баланс"},
        {"id": "cyber", "name": "Скин: Киберпанк", "price": 75, "type": "skin", "head": (200, 50, 255),
         "body": (140, 30, 200), "ability": "Урон от лазеров -50% | Заряд ульты +20%"},
        {"id": "soccer", "name": "Скин: Футбольный", "price": 200, "type": "skin", "head": (255, 255, 255),
         "body": (50, 50, 50), "ability": "Скорость +15% | Монеты x1.5 за всё!"},
        {"id": "pumpkin", "name": "🎃 Скин: Тыквоголовый", "price": 350, "type": "skin", "head": (255, 140, 0),
         "body": (200, 80, 0), "ability": "Антивирусный иммунитет (минус урон от вирусов)"},
        {"id": "ghost", "name": "❄️ Скин: Ледяной Призрак", "price": 400, "type": "skin", "head": (150, 220, 255),
         "body": (80, 150, 220), "ability": "Долгая заморозка времени от бонусов"},
        {"id": "dragon", "name": "Скин: Дракон", "price": 450, "type": "skin", "head": (255, 60, 20),
         "body": (220, 120, 0), "ability": "Клавиша [ F ]: Огненный шар (урон по врагам!)"},
        {"id": "phoenix", "name": "🔥 Скин: Неоновый Феникс", "price": 500, "type": "skin", "head": (255, 60, 60),
         "body": (220, 100, 0), "ability": "Увеличенный радиус магнита и притяжения"},
        {"id": "zeus", "name": "Скин: Кибер-Зевс", "price": 800, "type": "skin", "head": (255, 230, 50),
         "body": (200, 180, 0), "ability": "Клавиша [ E ]: Молния уничтожает всех врагов!"},
        {"id": "crystal_king", "name": "👑 Скин: Королевский Кристалл", "price": 1200, "type": "skin",
         "head": (0, 220, 255), "body": (100, 50, 255), "ability": "Двойной бонус монет и максимальный кулдаун"},
        {"id": "void_lord", "name": "Скин: Повелитель Бездны", "price": 1500, "type": "skin", "head": (140, 0, 255),
         "body": (70, 0, 150), "ability": "Клавиша [ E ]: Чёрная дыра + Иммунитет к минам!"}
    ], key=lambda x: x["price"]),

    "lives": sorted([
        {"id": "extra_life", "name": "Вторая жизнь", "price": 100, "type": "life"}
    ], key=lambda x: x["price"]),

    "themes": sorted([
        {"id": "cosmos", "name": "Поле: Неоновый космос", "price": 0, "type": "theme"},
        {"id": "grass", "name": "Поле: Кибер-Трава", "price": 150, "type": "theme"},
        {"id": "matrix", "name": "Поле: Матрикс", "price": 300, "type": "theme"},
        {"id": "sunset", "name": "Поле: Неоновый закат", "price": 450, "type": "theme"},
        {"id": "lava", "name": "Поле: Лавовая бездна", "price": 600, "type": "theme"}
    ], key=lambda x: x["price"]),

    "accessories": sorted([
        {"id": "none", "name": "Аксессуар: Нет", "price": 0, "type": "accessory"},
        {"id": "hat", "name": "🎩 Цилиндр джентльмена", "price": 150, "type": "accessory"},
        {"id": "glasses", "name": "🕶️ Очки хакера", "price": 180, "type": "accessory"},
        {"id": "crown", "name": "👑 Корона монарха", "price": 250, "type": "accessory"},
        {"id": "headphones", "name": "🎧 Неоновые наушники", "price": 300, "type": "accessory"},
        {"id": "helmet", "name": "🪖 Шлем спецназа", "price": 400, "type": "accessory"}
    ], key=lambda x: x["price"])
}


def play_sound(sound_type):
    """Негромкие мягкие синтезированные звуки интерфейса."""
    try:
        sample_rate = 22050
        durations = {"click": 0.065, "hover": 0.045, "purchase": 0.28,
                     "error": 0.14, "eat": 0.085, "gameover": 0.24}
        duration = durations.get(sound_type, 0.065)
        samples = array('h')
        count = int(sample_rate * duration)
        for i in range(count):
            t = i / sample_rate
            progress = t / duration
            if sound_type == "purchase":
                freq = 440 + 180 * progress
                volume = 0.11
            elif sound_type == "error":
                freq = 260 - 45 * progress
                volume = 0.055
            elif sound_type == "gameover":
                freq = 390 - 120 * progress
                volume = 0.065
            elif sound_type == "eat":
                freq = 590 + 90 * progress
                volume = 0.07
            elif sound_type == "hover":
                freq, volume = 520, 0.035
            elif sound_type == "click":
                freq, volume = 390, 0.045
            else:
                freq, volume = 420, 0.04
            # Плавное нарастание и затухание, чтобы убрать резкие щелчки.
            attack = min(1.0, t / 0.012)
            release = min(1.0, max(0.0, (duration - t) / 0.035))
            envelope = attack * release
            wave = math.sin(2 * math.pi * freq * t)
            # Чуть более мягкая вторая гармоника вместо резкого писка.
            wave = 0.82 * wave + 0.18 * math.sin(2 * math.pi * freq * 0.5 * t)
            samples.append(int(32767 * volume * envelope * wave))
        sound = pygame.mixer.Sound(buffer=samples.tobytes())
        sound.set_volume(0.55)
        sound.play()
    except Exception:
        pass


class ConfettiParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-6, -2)
        self.color = random.choice([
            (255, 50, 100), (50, 255, 150), (255, 220, 0),
            (0, 200, 255), (200, 100, 255), (255, 140, 0)
        ])
        self.size = random.randint(4, 8)
        self.life = 60

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), self.size, self.size))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add(self, x, y, color, count=8):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append({'x': x, 'y': y, 'vx': vx, 'vy': vy, 'color': color, 'life': 20})

    def update(self):
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        for p in self.particles:
            pygame.draw.circle(surface, p['color'], (int(p['x']), int(p['y'])), 3)


class Fireball:
    def __init__(self, pos, direction):
        self.pos = [pos[0], pos[1]]
        self.direction = direction
        self.active = True

    def update(self):
        self.pos[0] += self.direction[0]
        self.pos[1] += self.direction[1]
        if self.pos[0] < 0 or self.pos[0] >= GRID_WIDTH or self.pos[1] < 0 or self.pos[1] >= GRID_HEIGHT:
            self.active = False

    def draw(self, surface):
        px = self.pos[0] * GRID_SIZE + GRID_SIZE // 2
        py = self.pos[1] * GRID_SIZE + GRID_SIZE // 2
        pygame.draw.circle(surface, (255, 100, 0), (px, py), GRID_SIZE // 2)
        pygame.draw.circle(surface, (255, 255, 0), (px, py), GRID_SIZE // 4)


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.body = [
            (GRID_WIDTH // 2, GRID_HEIGHT // 2),
            (GRID_WIDTH // 2, GRID_HEIGHT // 2 + 1),
            (GRID_WIDTH // 2, GRID_HEIGHT // 2 + 2)
        ]
        self.direction = (0, -1)
        self.next_direction = (0, -1)
        self.grow_pending = False
        self.hp = 100
        self.max_hp = 100
        self.armor = 0
        self.max_armor = 50
        self.ult_charge = 0.0
        self.fireball_cooldown = 0
        self.ability_cooldown = 0
        self.trail = []

    def revive(self):
        self.hp = self.max_hp
        self.armor = self.max_armor
        self.direction = (0, -1)
        self.next_direction = (0, -1)

        length = len(self.body)
        cx, cy = GRID_WIDTH // 2, GRID_HEIGHT // 2
        self.body = [(cx, (cy + i) % GRID_HEIGHT) for i in range(length)]

    def take_damage(self, damage, viruses_ref=None, is_shielded=False):
        if is_shielded:
            return

        skin_key = game_data.get("current_skin", "classic")
        if skin_key == "cyber":
            damage = int(damage * 0.7)
        elif skin_key == "pumpkin":
            damage = int(damage * 0.5)

        armor_broken = False
        if self.armor > 0:
            if self.armor >= damage:
                self.armor -= damage
            else:
                rem = damage - self.armor
                self.armor = 0
                self.hp -= rem
                armor_broken = True
        else:
            self.hp -= damage

        play_sound("hit")

        if armor_broken and viruses_ref is not None:
            head = self.body[0]
            for v in viruses_ref[:]:
                dist = abs(head[0] - v.pos[0]) + abs(head[1] - v.pos[1])
                if dist <= 3:
                    viruses_ref.remove(v)

    def update(self):
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % GRID_WIDTH, (head_y + dy) % GRID_HEIGHT)

        if new_head in self.body:
            return False

        self.trail.append((head_x * GRID_SIZE + GRID_SIZE // 2, head_y * GRID_SIZE + GRID_SIZE // 2))
        if len(self.trail) > 8:
            self.trail.pop(0)

        if self.fireball_cooldown > 0: self.fireball_cooldown -= 1
        if self.ability_cooldown > 0: self.ability_cooldown -= 1

        self.body.insert(0, new_head)
        if not self.grow_pending:
            self.body.pop()
        else:
            self.grow_pending = False
        return True

    def draw(self, surface, foods, is_shielded=False):
        for idx, (tx, ty) in enumerate(self.trail):
            alpha_col = (0, 255, 200)
            pygame.draw.circle(surface, alpha_col, (tx, ty), (idx + 1) // 2)

        dx, dy = self.direction
        skin_key = game_data.get("current_skin", "classic")
        skin_info = next((s for s in SHOP_ITEMS["skins"] if s["id"] == skin_key), SHOP_ITEMS["skins"][0])

        for i, segment in enumerate(self.body):
            px = segment[0] * GRID_SIZE
            py = segment[1] * GRID_SIZE
            rect = pygame.Rect(px, py, GRID_SIZE - 2, GRID_SIZE - 2)

            if i == 0:
                color = SHIELD_COLOR if is_shielded else skin_info["head"]
                pygame.draw.rect(surface, color, rect, border_radius=6)
                if skin_key == "dragon":
                    pygame.draw.circle(surface, GOLD_COLOR, (px + GRID_SIZE // 2, py + 3), 3)

                eye_color = (10, 10, 20)
                if dx == 1 or dx == -1:
                    e1 = (px + (12 if dx == 1 else 4), py + 4)
                    e2 = (px + (12 if dx == 1 else 4), py + 12)
                else:
                    e1 = (px + 4, py + (12 if dy == 1 else 4))
                    e2 = (px + 12, py + (12 if dy == 1 else 4))

                pygame.draw.circle(surface, eye_color, e1, 3)
                pygame.draw.circle(surface, eye_color, e2, 3)

                acc_key = game_data.get("current_accessory", "none")
                if acc_key != "none" and not is_shielded:
                    if acc_key == "crown":
                        pygame.draw.polygon(surface, (255, 215, 0), [
                            (px + 3, py + 4), (px + 6, py - 2), (px + 10, py + 4),
                            (px + 14, py - 2), (px + 17, py + 4)
                        ])
                    elif acc_key == "glasses":
                        pygame.draw.rect(surface, (20, 20, 20), (px + 3, py + 5, 6, 5), border_radius=2)
                        pygame.draw.rect(surface, (20, 20, 20), (px + 11, py + 5, 6, 5), border_radius=2)
                        pygame.draw.line(surface, (200, 200, 200), (px + 9, py + 7), (px + 11, py + 7), 1)
                    elif acc_key == "hat":
                        pygame.draw.rect(surface, (40, 40, 40), (px + 4, py - 6, 12, 8))
                        pygame.draw.rect(surface, (20, 20, 20), (px + 2, py + 1, 16, 2))
                    elif acc_key == "headphones":
                        pygame.draw.arc(surface, (0, 220, 255), (px + 2, py - 2, 16, 12), 0, math.pi, 2)
                        pygame.draw.circle(surface, (255, 50, 100), (px + 2, py + 8), 3)
                        pygame.draw.circle(surface, (255, 50, 100), (px + 18, py + 8), 3)
                    elif acc_key == "helmet":
                        pygame.draw.arc(surface, (100, 120, 100), (px + 2, py - 3, 16, 16), 0, math.pi, 4)
                        pygame.draw.rect(surface, (255, 220, 0), (px + 5, py + 4, 10, 3), border_radius=1)
            else:
                color = SHIELD_COLOR if is_shielded else (
                    (255, 255, 255) if (skin_key == "soccer" and i % 2 == 0) else (
                        (30, 30, 30) if skin_key == "soccer" else skin_info["body"]))
                pygame.draw.rect(surface, color, rect, border_radius=4)


class VirusEnemy:
    def __init__(self, snake_body):
        self.spawn(snake_body)

    def spawn(self, snake_body):
        while True:
            self.pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if self.pos not in snake_body:
                break

    def move_towards(self, target_pos):
        hx, hy = self.pos
        tx, ty = target_pos
        dx = 1 if hx < tx else (-1 if hx > tx else 0)
        dy = 1 if hy < ty else (-1 if hy > ty else 0)
        if dx != 0 and dy != 0:
            self.pos = (hx + dx, hy) if random.random() < 0.5 else (hx, hy + dy)
        else:
            self.pos = (hx + dx, hy + dy)

    def draw(self, surface):
        px = self.pos[0] * GRID_SIZE + GRID_SIZE // 2
        py = self.pos[1] * GRID_SIZE + GRID_SIZE // 2
        radius = GRID_SIZE // 2 - 2
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sx = px + int((radius + 3) * math.cos(rad))
            sy = py + int((radius + 3) * math.sin(rad))
            pygame.draw.line(surface, (255, 30, 80), (px, py), (sx, sy), 2)
        pygame.draw.circle(surface, (180, 20, 50), (px, py), radius)
        pygame.draw.circle(surface, (255, 220, 0), (px, py), radius // 2)


class MiniSpider:
    def __init__(self, pos):
        self.pos = pos

    def move_randomly(self):
        dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0), (0, 0)])
        self.pos = ((self.pos[0] + dx) % GRID_WIDTH, (self.pos[1] + dy) % GRID_HEIGHT)

    def draw(self, surface):
        px = self.pos[0] * GRID_SIZE + GRID_SIZE // 2
        py = self.pos[1] * GRID_SIZE + GRID_SIZE // 2
        pygame.draw.circle(surface, MINI_SPIDER_COLOR, (px, py), GRID_SIZE // 3)


class SpiderBoss:
    def __init__(self, snake_body):
        self.spawn(snake_body)
        self.web_row = -1
        self.web_timer = 0
        self.shoot_cooldown = 30
        self.health = 3
        self.minis = []

    def spawn(self, snake_body):
        while True:
            self.pos = (random.randint(2, GRID_WIDTH - 3), random.randint(2, GRID_HEIGHT - 3))
            if self.pos not in snake_body:
                break

    def hit_and_bounce(self, snake_body):
        self.health -= 1
        play_sound("hit")
        dx, dy = random.choice([(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)])
        self.pos = ((self.pos[0] + dx) % GRID_WIDTH, (self.pos[1] + dy) % GRID_HEIGHT)

        if self.health <= 0:
            for _ in range(3):
                self.minis.append(MiniSpider(self.pos))

    def update(self):
        if self.health <= 0:
            return True
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 35
            self.web_row = random.randint(0, GRID_HEIGHT - 1)
            self.web_timer = 35
            play_sound("powerup")
        if self.web_timer > 0:
            self.web_timer -= 1
            if self.web_timer == 0:
                self.web_row = -1
        return False

    def draw(self, surface):
        px = self.pos[0] * GRID_SIZE + GRID_SIZE // 2
        py = self.pos[1] * GRID_SIZE + GRID_SIZE // 2
        body_col = SPIDER_COLOR if self.health > 1 else (255, 80, 80)

        for angle in range(30, 160, 40):
            rad = math.radians(angle)
            pygame.draw.line(surface, (120, 30, 160), (px, py),
                             (px + int(16 * math.cos(rad)), py + int(16 * math.sin(rad))), 2)
            pygame.draw.line(surface, (120, 30, 160), (px, py),
                             (px - int(16 * math.cos(rad)), py + int(16 * math.sin(rad))), 2)

        pygame.draw.circle(surface, body_col, (px, py), GRID_SIZE - 2)
        pygame.draw.circle(surface, (255, 0, 50), (px - 5, py - 3), 3)
        pygame.draw.circle(surface, (255, 0, 50), (px + 5, py - 3), 3)

        pygame.draw.polygon(surface, (255, 255, 255), [(px - 4, py + 3), (px - 2, py + 8), (px, py + 3)])
        pygame.draw.polygon(surface, (255, 255, 255), [(px + 4, py + 3), (px + 2, py + 8), (px, py + 3)])

        if self.web_row != -1:
            wy = self.web_row * GRID_SIZE
            pygame.draw.line(surface, (220, 220, 255), (0, wy + GRID_SIZE // 2), (WIDTH, wy + GRID_SIZE // 2), 4)


def draw_accessory_preview(surface, accessory_id, center_x, center_y):
    """Рисует увеличенную миниатюру головы змейки с выбранным аксессуаром."""
    head = pygame.Rect(center_x - 30, center_y - 25, 60, 54)
    pygame.draw.circle(surface, (0, 255, 160), (center_x, center_y), 36)
    pygame.draw.circle(surface, (0, 90, 75), (center_x, center_y), 32, 2)
    pygame.draw.rect(surface, (0, 230, 130), head, border_radius=15)
    pygame.draw.rect(surface, (140, 255, 210), head, 2, border_radius=15)
    pygame.draw.circle(surface, (10, 20, 35), (center_x - 13, center_y - 3), 5)
    pygame.draw.circle(surface, (10, 20, 35), (center_x + 13, center_y - 3), 5)
    pygame.draw.circle(surface, (255, 255, 255), (center_x - 14, center_y - 5), 2)
    pygame.draw.circle(surface, (255, 255, 255), (center_x + 12, center_y - 5), 2)

    if accessory_id == "crown":
        pygame.draw.polygon(surface, (255, 205, 35), [
            (center_x - 25, center_y - 20), (center_x - 20, center_y - 42),
            (center_x - 7, center_y - 27), (center_x, center_y - 45),
            (center_x + 8, center_y - 27), (center_x + 21, center_y - 42),
            (center_x + 25, center_y - 20)])
        pygame.draw.rect(surface, (255, 170, 0), (center_x - 25, center_y - 23, 50, 9), border_radius=3)
        for gem_x in (center_x - 14, center_x, center_x + 14):
            pygame.draw.circle(surface, (255, 70, 120), (gem_x, center_y - 19), 3)
    elif accessory_id == "glasses":
        pygame.draw.rect(surface, (15, 20, 35), (center_x - 25, center_y - 8, 22, 16), border_radius=5)
        pygame.draw.rect(surface, (0, 220, 255), (center_x - 25, center_y - 8, 22, 16), 2, border_radius=5)
        pygame.draw.rect(surface, (15, 20, 35), (center_x + 3, center_y - 8, 22, 16), border_radius=5)
        pygame.draw.rect(surface, (0, 220, 255), (center_x + 3, center_y - 8, 22, 16), 2, border_radius=5)
        pygame.draw.line(surface, (0, 220, 255), (center_x - 3, center_y), (center_x + 3, center_y), 3)
        pygame.draw.line(surface, (100, 245, 255), (center_x - 21, center_y - 3), (center_x - 10, center_y - 3), 2)
    elif accessory_id == "hat":
        pygame.draw.ellipse(surface, (15, 15, 25), (center_x - 34, center_y - 39, 68, 17))
        pygame.draw.rect(surface, (35, 35, 50), (center_x - 23, center_y - 64, 46, 29), border_radius=5)
        pygame.draw.rect(surface, (220, 35, 75), (center_x - 23, center_y - 44, 46, 7))
        pygame.draw.line(surface, (100, 100, 125), (center_x - 15, center_y - 58), (center_x + 15, center_y - 58), 2)
    elif accessory_id == "headphones":
        pygame.draw.arc(surface, (0, 220, 255), (center_x - 32, center_y - 42, 64, 64), 0, math.pi, 6)
        pygame.draw.rect(surface, (0, 220, 255), (center_x - 34, center_y - 12, 13, 28), border_radius=5)
        pygame.draw.rect(surface, (255, 50, 130), (center_x + 21, center_y - 12, 13, 28), border_radius=5)
        pygame.draw.rect(surface, (180, 255, 255), (center_x - 31, center_y - 8, 7, 18), border_radius=3)
        pygame.draw.rect(surface, (255, 180, 220), (center_x + 24, center_y - 8, 7, 18), border_radius=3)
    elif accessory_id == "helmet":
        pygame.draw.arc(surface, (115, 140, 155), (center_x - 31, center_y - 42, 62, 62), 0, math.pi, 8)
        pygame.draw.rect(surface, (100, 125, 145), (center_x - 30, center_y - 19, 60, 12), border_radius=4)
        pygame.draw.rect(surface, (255, 210, 45), (center_x - 18, center_y - 17, 36, 6), border_radius=2)
        pygame.draw.circle(surface, (0, 220, 255), (center_x + 22, center_y - 23), 4)


def draw_buff_icon(surface, buff_type, x, y, size=22):
    """Небольшие рисованные иконки баффов, не зависящие от emoji-шрифтов."""
    colors = {
        "freeze": (80, 205, 255), "shield": (230, 240, 255),
        "magnet": (255, 145, 45), "slowmo": (80, 225, 255), "combo": (255, 105, 35)
    }
    color = colors.get(buff_type, (220, 220, 240))
    cx, cy = x + size // 2, y + size // 2
    pygame.draw.circle(surface, (20, 25, 45), (cx, cy), size // 2)
    pygame.draw.circle(surface, color, (cx, cy), size // 2 - 1, 2)
    if buff_type == "freeze":
        pygame.draw.line(surface, color, (cx, y + 4), (cx, y + size - 4), 2)
        pygame.draw.line(surface, color, (x + 4, cy), (x + size - 4, cy), 2)
        pygame.draw.line(surface, color, (x + 6, y + 6), (x + size - 6, y + size - 6), 1)
        pygame.draw.line(surface, color, (x + size - 6, y + 6), (x + 6, y + size - 6), 1)
    elif buff_type == "shield":
        pygame.draw.polygon(surface, color, [(cx, y + 4), (x + size - 5, y + 7),
                                             (x + size - 7, y + 14), (cx, y + size - 4),
                                             (x + 7, y + 14), (x + 5, y + 7)], 2)
    elif buff_type == "magnet":
        pygame.draw.arc(surface, color, (x + 5, y + 4, size - 10, size - 8), math.pi, 2 * math.pi, 3)
        pygame.draw.line(surface, color, (x + 5, cy), (x + 5, y + 7), 3)
        pygame.draw.line(surface, color, (x + size - 5, cy), (x + size - 5, y + 7), 3)
    elif buff_type == "slowmo":
        pygame.draw.line(surface, color, (cx - 3, y + 5), (cx + 1, cy - 1), 3)
        pygame.draw.line(surface, color, (cx + 1, cy - 1), (cx - 2, cy - 1), 2)
        pygame.draw.line(surface, color, (cx - 2, cy - 1), (cx + 3, y + size - 5), 3)
    else:
        pygame.draw.polygon(surface, color, [(cx, y + 4), (cx + 3, cy - 2),
                                              (x + size - 5, cy), (cx + 2, cy + 2),
                                              (cx + 4, y + size - 4), (cx - 2, cy + 2),
                                              (x + 5, cy)], 0)


def draw_hud(surface, score, high_score, hp, max_hp, armor, max_armor, coins, lives, active_buffs, ult_charge, combo,
             mode_name, current_event):
    bar_width = 110
    bar_height = 12

    pygame.draw.rect(surface, HP_BG_COLOR, (12, 8, bar_width, bar_height), border_radius=4)
    fill = (hp / max_hp) * bar_width
    if fill > 0:
        pygame.draw.rect(surface, HP_BAR_COLOR, (12, 8, fill, bar_height), border_radius=4)
    if armor > 0:
        armor_fill = (armor / max_armor) * bar_width
        pygame.draw.rect(surface, ARMOR_BAR_COLOR, (12, 8, armor_fill, bar_height // 2), border_radius=2)

    pygame.draw.rect(surface, (30, 30, 50), (12, 24, bar_width, 6), border_radius=2)
    ult_fill = (ult_charge / 100.0) * bar_width
    if ult_fill > 0:
        pygame.draw.rect(surface, ULT_BAR_COLOR, (12, 24, ult_fill, 6), border_radius=2)

    p_name = game_data.get('player_name', 'Игрок')
    m_label = "АПОКАЛИПСИС" if mode_name == "APOCALYPSE" else "КЛАССИКА"

    txt_info = f"Игрок: {p_name}  |  [{m_label}]  |  Очки: {score}  |  Рекорд: {high_score}"
    surf_info = font_small.render(txt_info, True, GOLD_COLOR)
    surface.blit(surf_info, (135, 8))

    cur_x = 135 + surf_info.get_width() + 15
    draw_coin_icon(surface, cur_x, 8, 14)
    surf_coins = font_small.render(f"{coins}", True, GOLD_COLOR)
    surface.blit(surf_coins, (cur_x + 18, 8))

    cur_x += 18 + surf_coins.get_width() + 15
    draw_heart_icon(surface, cur_x, 8, 14)
    surf_lives = font_small.render(f"x{lives}", True, (255, 100, 120))
    surface.blit(surf_lives, (cur_x + 18, 8))

    bx = 12
    by = 38
    buff_list = []
    if active_buffs.get("freeze", 0) > 0:
        buff_list.append(("🧊 ЗАМОРОЗКА", FREEZE_COLOR, active_buffs['freeze']))
    if active_buffs.get("shield", 0) > 0:
        buff_list.append(("🛡️ ЩИТ", (255, 255, 255), active_buffs['shield']))
    if active_buffs.get("magnet", 0) > 0:
        buff_list.append(("🧲 МАГНИТ", MAGNET_COLOR, active_buffs['magnet']))
    if active_buffs.get("slowmo", 0) > 0:
        buff_list.append(("⚡ СКОРОСТЬ", SLOWMO_COLOR, active_buffs['slowmo']))
    if combo > 1:
        buff_list.append((f"🔥 x{combo} КОМБО", (255, 100, 0), -1))

    for b_title, b_color, b_timer in buff_list:
        sec_str = f" {math.ceil(b_timer / 20)}s" if b_timer > 0 else ""
        text_str = f"{b_title}{sec_str}"
        b_surf = font_tiny.render(text_str, True, (245, 248, 255))
        kind = ("freeze" if "ЗАМОРОЗКА" in b_title else
                "shield" if "ЩИТ" in b_title else
                "magnet" if "МАГНИТ" in b_title else
                "slowmo" if "СКОРОСТЬ" in b_title else "combo")
        bg_w = b_surf.get_width() + 34
        bg_r = pygame.Rect(bx, by, bg_w, 25)
        pygame.draw.rect(surface, (18, 24, 45), bg_r, border_radius=7)
        pygame.draw.rect(surface, b_color, bg_r, 1, border_radius=7)
        draw_buff_icon(surface, kind, bx + 3, by + 1, 22)
        surface.blit(b_surf, (bx + 28, by + 5))
        bx += bg_w + 6

    if current_event:
        ev_surf = font_tiny.render(f"⚠️ {current_event}", True, (255, 60, 60))
        surface.blit(ev_surf, (bx + 10, by + 2))


def draw_background(surface, game_mode, current_event):
    theme_key = game_data.get("current_theme", "cosmos")
    theme = THEMES.get(theme_key, THEMES["cosmos"])

    bg_col = (40, 10, 15) if game_mode == "APOCALYPSE" else theme["bg"]
    grid_col = (70, 20, 25) if game_mode == "APOCALYPSE" else theme["grid"]

    surface.fill(bg_col)
    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(surface, grid_col, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(surface, grid_col, (0, y), (WIDTH, y))


def spawn_food(snake_body, foods, viruses, spiders, mines, type_name="apple", timer_seconds=12):
    while True:
        pos = (random.randint(0, GRID_WIDTH - 1), random.randint(2, GRID_HEIGHT - 1))
        if (pos not in snake_body and
                not any(f['pos'] == pos for f in foods) and
                not any(v.pos == pos for v in viruses) and
                not any(s.pos == pos for s in spiders) and
                pos not in mines):
            item = {'pos': pos, 'type': type_name}
            if type_name != "apple":
                item['timer'] = timer_seconds * 20
                item['max_timer'] = timer_seconds * 20
            foods.append(item)
            break



LANGUAGES = ["Русский", "English", "Deutsch", "中文", "Français", "Українська"]
LANG_CODES = ["ru", "en", "de", "zh", "fr", "uk"]
UI_TEXT = {
    "ru": {"start":"ПЕРЕЙТИ В ИГРУ", "settings":"НАСТРОЙКИ", "info":"СВЕДЕНИЯ ОБ ИГРЕ", "back":"НАЗАД", "choose_lang":"ЯЗЫК ИГРЫ", "hint":"Выбери пункт мышью", "about":"О CYBER SNAKE", "about1":"Управляй неоновой змейкой, собирай яблоки и бонусы.", "about2":"Избегай врагов, усиливайся и ставь новые рекорды!", "buffs":"БАФФЫ", "freeze":"Заморозка — временно останавливает врагов.", "shield":"Щит — защищает от части опасностей.", "magnet":"Магнит — притягивает полезные предметы.", "slowmo":"Замедление — замедляет темп игры.", "enemies":"ВРАГИ И ОПАСНОСТИ", "spider":"Паук-босс и мини-пауки преследуют игрока.", "virus":"Вирусы, мины и лазеры опасны при столкновении.", "footer":"CYBER SNAKE • Developed by MONZAY"},
    "en": {"start":"PLAY GAME", "settings":"SETTINGS", "info":"ABOUT THE GAME", "back":"BACK", "choose_lang":"GAME LANGUAGE", "hint":"Choose an option with the mouse", "about":"ABOUT CYBER SNAKE", "about1":"Control a neon snake, collect apples and bonuses.", "about2":"Avoid enemies, power up and set new records!", "buffs":"BUFFS", "freeze":"Freeze — temporarily stops enemies.", "shield":"Shield — protects you from some dangers.", "magnet":"Magnet — attracts useful items.", "slowmo":"Slow motion — slows the game down.", "enemies":"ENEMIES & HAZARDS", "spider":"The boss spider and mini-spiders chase the player.", "virus":"Viruses, mines and lasers are dangerous on contact.", "footer":"CYBER SNAKE • Developed by MONZAY"},
    "de": {"start":"SPIEL STARTEN", "settings":"EINSTELLUNGEN", "info":"SPIELINFO", "back":"ZURÜCK", "choose_lang":"SPIELSPRACHE", "hint":"Wähle einen Punkt mit der Maus", "about":"ÜBER CYBER SNAKE", "about1":"Steuere eine Neon-Schlange und sammle Äpfel und Boni.", "about2":"Meide Gegner, werde stärker und stelle Rekorde auf!", "buffs":"BOOSTS", "freeze":"Einfrieren — stoppt Gegner kurzzeitig.", "shield":"Schild — schützt vor einigen Gefahren.", "magnet":"Magnet — zieht nützliche Gegenstände an.", "slowmo":"Zeitlupe — verlangsamt das Spiel.", "enemies":"GEGNER & GEFAHREN", "spider":"Boss-Spinne und kleine Spinnen verfolgen dich.", "virus":"Viren, Minen und Laser sind bei Kontakt gefährlich.", "footer":"CYBER SNAKE • Developed by MONZAY"},
    "zh": {"start":"开始游戏", "settings":"设置", "info":"游戏说明", "back":"返回", "choose_lang":"游戏语言", "hint":"用鼠标选择菜单", "about":"关于 CYBER SNAKE", "about1":"控制霓虹贪吃蛇，收集苹果和奖励。", "about2":"躲避敌人，获得强化并创造新纪录！", "buffs":"增益效果", "freeze":"冻结：暂时停止敌人。", "shield":"护盾：抵挡部分危险。", "magnet":"磁铁：吸引有用物品。", "slowmo":"减速：降低游戏速度。", "enemies":"敌人与危险", "spider":"蜘蛛首领和小蜘蛛会追击玩家。", "virus":"病毒、地雷和激光接触时很危险。", "footer":"CYBER SNAKE • Developed by MONZAY"},
    "fr": {"start":"JOUER", "settings":"PARAMÈTRES", "info":"À PROPOS DU JEU", "back":"RETOUR", "choose_lang":"LANGUE DU JEU", "hint":"Choisis une option avec la souris", "about":"À PROPOS DE CYBER SNAKE", "about1":"Contrôle un serpent néon et collecte pommes et bonus.", "about2":"Évite les ennemis, améliore-toi et bats des records !", "buffs":"BONUS", "freeze":"Gel — immobilise temporairement les ennemis.", "shield":"Bouclier — protège de certains dangers.", "magnet":"Aimant — attire les objets utiles.", "slowmo":"Ralenti — ralentit le jeu.", "enemies":"ENNEMIS ET DANGERS", "spider":"L'araignée boss et les petites araignées te poursuivent.", "virus":"Virus, mines et lasers sont dangereux au contact.", "footer":"CYBER SNAKE • Developed by MONZAY"},
    "uk": {"start":"ГРАТИ", "settings":"НАЛАШТУВАННЯ", "info":"ПРО ГРУ", "back":"НАЗАД", "choose_lang":"МОВА ГРИ", "hint":"Обери пункт мишкою", "about":"ПРО CYBER SNAKE", "about1":"Керуй неоновою змійкою, збирай яблука та бонуси.", "about2":"Уникай ворогів, посилюйся та встановлюй рекорди!", "buffs":"ПІДСИЛЕННЯ", "freeze":"Замороження — тимчасово зупиняє ворогів.", "shield":"Щит — захищає від частини небезпек.", "magnet":"Магніт — притягує корисні предмети.", "slowmo":"Уповільнення — сповільнює гру.", "enemies":"ВОРОГИ Й НЕБЕЗПЕКИ", "spider":"Павук-бос і малі павуки переслідують гравця.", "virus":"Віруси, міни та лазери небезпечні при зіткненні.", "footer":"CYBER SNAKE • Developed by MONZAY"}
}

def ui(key):
    lang = game_data.get("language", "ru")
    return UI_TEXT.get(lang, UI_TEXT["ru"]).get(key, UI_TEXT["ru"].get(key, key))

def ui_font(size):
    # На Windows выбираем шрифт с поддержкой китайских символов при необходимости.
    preferred = "Microsoft YaHei" if game_data.get("language") == "zh" else "Segoe UI"
    try:
        return pygame.font.SysFont(preferred, size, bold=(size >= 28))
    except Exception:
        return pygame.font.Font(None, size)

def draw_menu_button(surface, rect, label, accent=(0, 255, 180), hovered=False):
    fill = (24, 32, 58) if not hovered else (34, 48, 78)
    pygame.draw.rect(surface, fill, rect, border_radius=14)
    pygame.draw.rect(surface, accent, rect, 2, border_radius=14)
    label_surface = ui_font(17).render(label, True, (245, 250, 255))
    surface.blit(label_surface, (rect.centerx-label_surface.get_width()//2, rect.centery-label_surface.get_height()//2))


def draw_neon_panel(surface, rect, accent=(0, 220, 190), fill=(12, 20, 39), radius=20, glow=True):
    """Единая карточка интерфейса в стиле неонового главного меню."""
    if glow:
        glow_rect = rect.inflate(8, 8)
        pygame.draw.rect(surface, (0, 55, 65), glow_rect, border_radius=radius + 4)
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, accent, rect, 2, border_radius=radius)
    # Маленькие угловые акценты создают вид игровой панели.
    corner = 18
    for x, y, sx, sy in ((rect.left, rect.top, 1, 1), (rect.right, rect.top, -1, 1),
                         (rect.left, rect.bottom, 1, -1), (rect.right, rect.bottom, -1, -1)):
        pygame.draw.line(surface, (90, 255, 220), (x, y + sy * corner), (x, y), 3)
        pygame.draw.line(surface, (90, 255, 220), (x, y), (x + sx * corner, y), 3)


def draw_section_heading(surface, title, subtitle=None, accent=(0, 255, 180)):
    title_surf = font_title.render(title, True, accent)
    surface.blit(title_surf, (WIDTH // 2  title_surf.get_width() // 2, 30))
    pygame.draw.line(surface, accent, (WIDTH // 2 - 120, 88), (WIDTH // 2 + 120, 88), 2)
    if subtitle:
        sub = font_tiny.render(subtitle, True, (155, 180, 205))
        surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 96))


def main():
    snake = Snake()
    particles = ParticleSystem()
    foods = []
    viruses = []
    spiders = []
    mines = []
    lasers = []
    fireballs = []

    spawn_food(snake.body, foods, viruses, spiders, mines, "apple")

    score = 0
    earned_coins_match = 0
    bosses_killed_match = 0
    match_time_seconds = 0
    frame_counter = 0

    eaten_count = 0
    combo = 1
    combo_timer = 0

    game_state = "REGISTRATION" if not game_data.get("player_name") else "SPLASH"
    splash_started = time.time()
    reg_text = game_data.get("player_name", "")

    game_mode = "CLASSIC"
    screen_shake_timer = 0

    pickup_text = ""
    pickup_text_timer = 0

    insufficient_coins_timer = 0

    current_event = None
    event_timer = 0
    meteor_shadows = []

    active_buffs = {"slowmo": 0, "magnet": 0, "freeze": 0, "shield": 0}

    shop_category_idx = 0
    category_names = ["skins", "lives", "themes", "accessories"]
    selected_item_indices = [0, 0, 0, 0]
    confirm_purchase = False

    purchase_anim_timer = 0
    purchased_item_name = ""
    confetti_list = []

    last_won_reward = None
    case_rolling = False
    roll_timer = 0
    rolling_items = []
    show_chances_modal = False
    quests_tab = "daily"

    while True:
        # Проверяем таймер постоянно, поэтому задания обновятся даже без перезапуска игры.
        check_daily_reset()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if game_state == "RUNNING" and pygame.Rect(WIDTH - 58, 12, 42, 42).collidepoint(mx, my):
                    game_state = "PAUSED"
                    play_sound("click")
                elif game_state == "PAUSED":
                    resume_rect = pygame.Rect(WIDTH // 2 - 145, HEIGHT // 2 + 55, 290, 48)
                    exit_rect = pygame.Rect(WIDTH // 2 - 145, HEIGHT // 2 + 115, 290, 48)
                    if resume_rect.collidepoint(mx, my):
                        game_state = "RUNNING"
                        play_sound("click")
                    elif exit_rect.collidepoint(mx, my):
                        game_state = "MENU"
                        play_sound("click")
                elif game_state == "SPLASH":
                    # Интро закрывается только по явному действию игрока.
                    game_state = "HOME"
                    play_sound("click")
                elif game_state == "HOME":
                    if pygame.Rect(WIDTH//2-170, 360, 340, 54).collidepoint(mx, my):
                        game_state = "MENU"
                    elif pygame.Rect(WIDTH//2-170, 430, 340, 54).collidepoint(mx, my):
                        game_state = "SETTINGS"
                    elif pygame.Rect(WIDTH//2-170, 500, 340, 54).collidepoint(mx, my):
                        game_state = "INFO"
                elif game_state == "SETTINGS":
                    if pygame.Rect(WIDTH//2-190, 360, 55, 48).collidepoint(mx, my):
                        idx = LANG_CODES.index(game_data.get("language", "ru")) if game_data.get("language", "ru") in LANG_CODES else 0
                        game_data["language"] = LANG_CODES[(idx-1) % len(LANG_CODES)]
                        save_game_data(game_data)
                    elif pygame.Rect(WIDTH//2+135, 360, 55, 48).collidepoint(mx, my):
                        idx = LANG_CODES.index(game_data.get("language", "ru")) if game_data.get("language", "ru") in LANG_CODES else 0
                        game_data["language"] = LANG_CODES[(idx+1) % len(LANG_CODES)]
                        save_game_data(game_data)
                    elif pygame.Rect(WIDTH//2-120, 520, 240, 52).collidepoint(mx, my):
                        game_state = "HOME"
                elif game_state == "INFO":
                    if pygame.Rect(WIDTH//2-120, 690, 240, 52).collidepoint(mx, my):
                        play_sound("click")
                        game_state = "HOME"
                elif game_state == "MENU":
                    # Большая карточка режима одновременно служит кнопкой старта.
                    if pygame.Rect(48, 232, WIDTH-96, 66).collidepoint(mx, my):
                        if mx < 112 or mx > WIDTH - 112:
                            game_mode = "APOCALYPSE" if game_mode == "CLASSIC" else "CLASSIC"
                            play_sound("click")
                        else:
                            snake.reset(); foods.clear(); viruses.clear(); spiders.clear(); mines.clear(); lasers.clear(); fireballs.clear()
                            spawn_food(snake.body, foods, viruses, spiders, mines, "apple")
                            score = 0; earned_coins_match = 0; bosses_killed_match = 0; match_time_seconds = 0
                            frame_counter = 0; eaten_count = 0; combo = 1
                            active_buffs = {"slowmo": 0, "magnet": 0, "freeze": 0, "shield": 0}
                            current_event = None; event_timer = 0
                            game_state = "RUNNING"
                            play_sound("click")
                    else:
                        quick_rects = [pygame.Rect(48 + (idx % 2) * 368, 315 + (idx // 2) * 78, 336, 66) for idx in range(6)]
                        for idx, rect in enumerate(quick_rects):
                            if rect.collidepoint(mx, my):
                                play_sound("click")
                                if idx == 0:
                                    game_state = "SHOP"; confirm_purchase = False; insufficient_coins_timer = 0
                                elif idx == 1:
                                    game_state = "QUESTS"; quests_tab = "daily"
                                elif idx == 2:
                                    game_state = "CASES"; last_won_reward = None; case_rolling = False; show_chances_modal = False
                                elif idx == 3:
                                    game_state = "ACHIEVEMENTS"
                                elif idx == 4:
                                    game_state = "HELP"
                                elif idx == 5:
                                    game_mode = "APOCALYPSE" if game_mode == "CLASSIC" else "CLASSIC"
                                break
                elif game_state == "SHOP":
                    if confirm_purchase:
                        if pygame.Rect(WIDTH//2-150, 565, 300, 48).collidepoint(mx, my):
                            play_sound("click")
                            item = SHOP_ITEMS[category_names[shop_category_idx]][selected_item_indices[shop_category_idx]]
                            if game_data["coins"] >= item["price"]:
                                confirm_purchase = True
                                # Route through the existing confirmation keyboard flow; click confirms purchase below.
                                game_data["coins"] -= item["price"]
                                if item["type"] == "skin": game_data["unlocked_skins"].append(item["id"]); game_data["current_skin"] = item["id"]
                                elif item["type"] == "life": game_data["lives_count"] += 1
                                elif item["type"] == "theme": game_data["unlocked_themes"].append(item["id"]); game_data["current_theme"] = item["id"]
                                elif item["type"] == "accessory": game_data["unlocked_accessories"].append(item["id"]); game_data["current_accessory"] = item["id"]
                                save_game_data(game_data); purchased_item_name = item["name"]; purchase_anim_timer = 45
                                confirm_purchase = False; play_sound("purchase")
                            else:
                                insufficient_coins_timer = 40; play_sound("error")
                        elif pygame.Rect(43, 125, 720, 38).collidepoint(mx, my):
                            shop_category_idx = max(0, min(3, (mx - 43) // 180)); play_sound("click")
                        elif pygame.Rect(55, 430, 95, 55).collidepoint(mx, my):
                            items = SHOP_ITEMS[category_names[shop_category_idx]]
                            selected_item_indices[shop_category_idx] = (selected_item_indices[shop_category_idx]-1) % len(items); play_sound("click")
                        elif pygame.Rect(650, 430, 95, 55).collidepoint(mx, my):
                            items = SHOP_ITEMS[category_names[shop_category_idx]]
                            selected_item_indices[shop_category_idx] = (selected_item_indices[shop_category_idx]+1) % len(items); play_sound("click")
                        elif pygame.Rect(WIDTH//2-150, 565, 300, 48).collidepoint(mx, my):
                            confirm_purchase = True; play_sound("click")
                    else:
                        if pygame.Rect(43, 125, 720, 38).collidepoint(mx, my):
                            shop_category_idx = max(0, min(3, (mx - 43) // 180)); play_sound("click")
                        elif pygame.Rect(55, 430, 95, 55).collidepoint(mx, my):
                            items = SHOP_ITEMS[category_names[shop_category_idx]]
                            selected_item_indices[shop_category_idx] = (selected_item_indices[shop_category_idx]-1) % len(items); play_sound("click")
                        elif pygame.Rect(650, 430, 95, 55).collidepoint(mx, my):
                            items = SHOP_ITEMS[category_names[shop_category_idx]]
                            selected_item_indices[shop_category_idx] = (selected_item_indices[shop_category_idx]+1) % len(items); play_sound("click")
                        elif pygame.Rect(WIDTH//2-150, 565, 300, 48).collidepoint(mx, my):
                            item = SHOP_ITEMS[category_names[shop_category_idx]][selected_item_indices[shop_category_idx]]
                            unlocked = ((item["type"] == "skin" and item["id"] in game_data["unlocked_skins"]) or
                                        (item["type"] == "theme" and item["id"] in game_data["unlocked_themes"]) or
                                        (item["type"] == "accessory" and item["id"] in game_data["unlocked_accessories"]))
                            if unlocked:
                                if item["type"] == "skin": game_data["current_skin"] = item["id"]
                                elif item["type"] == "theme": game_data["current_theme"] = item["id"]
                                elif item["type"] == "accessory": game_data["current_accessory"] = item["id"]
                                save_game_data(game_data); play_sound("purchase")
                            elif game_data["coins"] >= item["price"]:
                                confirm_purchase = True; play_sound("click")
                            else:
                                insufficient_coins_timer = 40; play_sound("error")
                        elif my > HEIGHT-70:
                            game_state = "MENU"; play_sound("click")
                elif game_state == "QUESTS":
                    if pygame.Rect(WIDTH//2-310, 65, 300, 50).collidepoint(mx, my):
                        quests_tab = "daily"; play_sound("click")
                    elif pygame.Rect(WIDTH//2+10, 65, 300, 50).collidepoint(mx, my):
                        quests_tab = "global"; play_sound("click")
                    elif my > HEIGHT-70:
                        game_state = "MENU"; play_sound("click")
                elif game_state == "CASES":
                    if show_chances_modal:
                        show_chances_modal = False; play_sound("click")
                    elif pygame.Rect(WIDTH//2+230, 35, 45, 45).collidepoint(mx, my):
                        show_chances_modal = True; play_sound("click")
                    elif case_rolling:
                        pass
                    elif last_won_reward is not None:
                        last_won_reward = None; play_sound("click")
                    elif pygame.Rect(WIDTH//2-120, HEIGHT//2-90, 240, 140).collidepoint(mx, my):
                        case_price = 75
                        if game_data["coins"] >= case_price:
                            game_data["coins"] -= case_price
                            case_rolling = True; roll_timer = 30
                            rolling_items = [roll_case() for _ in range(6)]
                            final_won = rolling_items[-1]
                            save_game_data(game_data); play_sound("purchase")
                        else:
                            play_sound("error")
                    elif my > HEIGHT-70:
                        game_state = "MENU"; play_sound("click")
                elif game_state in ["ACHIEVEMENTS", "HELP"] and my > HEIGHT-70:
                    game_state = "MENU"; play_sound("click")

            elif event.type == pygame.KEYDOWN:
                char = event.unicode.lower() if hasattr(event, 'unicode') else ""
                scancode = getattr(event, 'scancode', -1)

                is_m = (event.key == pygame.K_m) or (char in ['m', 'м', 'ь']) or (scancode in [50, 44])
                is_a = (event.key == pygame.K_a) or (char in ['a', 'ф']) or (scancode in [38, 30])
                is_q = (event.key == pygame.K_q) or (char in ['q', 'й']) or (scancode in [24, 16])
                is_r = (event.key == pygame.K_r) or (char in ['r', 'к']) or (scancode in [19, 27])
                is_h = (event.key == pygame.K_h) or (char in ['h', 'р', 'ч']) or (scancode in [43, 35])
                is_c = (event.key == pygame.K_c) or (char in ['c', 'с', 'ц']) or (scancode in [46, 51])
                is_y = (event.key == pygame.K_y) or (char in ['y', 'н']) or (scancode in [29, 21])
                is_n = (event.key == pygame.K_n) or (char in ['n', 'т']) or (scancode in [57, 49])
                is_w = (event.key in [pygame.K_UP, pygame.K_w]) or (char in ['w', 'ц']) or (scancode in [26, 17])
                is_s = (event.key in [pygame.K_DOWN, pygame.K_s]) or (char in ['s', 'ы']) or (scancode in [31, 22])
                is_d = (event.key in [pygame.K_RIGHT, pygame.K_d]) or (char in ['d', 'в']) or (scancode in [32, 23])

                if game_state == "REGISTRATION":
                    if event.key == pygame.K_RETURN:
                        if len(reg_text.strip()) > 0:
                            game_data["player_name"] = reg_text.strip()
                            save_game_data(game_data)
                            game_state = "SPLASH"
                            splash_started = time.time()
                    elif event.key == pygame.K_BACKSPACE:
                        reg_text = reg_text[:-1]
                    else:
                        if event.unicode and re.match(r'^[a-zA-Z0-9_\-\.\!\@\#\$\%\^\&\*]+$', event.unicode):
                            if len(reg_text) < 15:
                                reg_text += event.unicode

                elif game_state == "SPLASH":
                    # Любая клавиша может продолжить, но таймер больше не пропускает интро сам.
                    game_state = "HOME"
                    play_sound("click")

                elif game_state == "HOME":
                    if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        game_state = "MENU"
                    elif event.key == pygame.K_s:
                        game_state = "SETTINGS"
                    elif event.key == pygame.K_i:
                        game_state = "INFO"
                elif game_state == "SETTINGS":
                    if event.key == pygame.K_ESCAPE:
                        game_state = "HOME"
                    elif event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                        idx = LANG_CODES.index(game_data.get("language", "ru")) if game_data.get("language", "ru") in LANG_CODES else 0
                        idx = (idx + (1 if event.key == pygame.K_RIGHT else -1)) % len(LANG_CODES)
                        game_data["language"] = LANG_CODES[idx]
                        save_game_data(game_data)
                    elif event.key == pygame.K_RETURN:
                        game_state = "HOME"
                elif game_state == "INFO":
                    if event.key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE]:
                        game_state = "HOME"
                elif game_state == "MENU":
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                        snake.reset()
                        foods.clear()
                        viruses.clear()
                        spiders.clear()
                        mines.clear()
                        lasers.clear()
                        fireballs.clear()
                        spawn_food(snake.body, foods, viruses, spiders, mines, "apple")
                        score = 0
                        earned_coins_match = 0
                        bosses_killed_match = 0
                        match_time_seconds = 0
                        frame_counter = 0
                        eaten_count = 0
                        combo = 1
                        active_buffs = {"slowmo": 0, "magnet": 0, "freeze": 0, "shield": 0}
                        current_event = None
                        event_timer = 0
                        game_state = "RUNNING"
                    elif is_r:
                        game_mode = "APOCALYPSE" if game_mode == "CLASSIC" else "CLASSIC"
                    elif is_m:
                        game_state = "SHOP"
                        confirm_purchase = False
                        insufficient_coins_timer = 0
                    elif is_c:
                        game_state = "CASES"
                        last_won_reward = None
                        case_rolling = False
                        show_chances_modal = False
                    elif is_a:
                        game_state = "ACHIEVEMENTS"
                    elif is_q:
                        game_state = "QUESTS"
                        quests_tab = "daily"
                    elif is_h:
                        game_state = "HELP"

                elif game_state in ["ACHIEVEMENTS", "HELP"]:
                    if event.key == pygame.K_ESCAPE:
                        game_state = "MENU"

                elif game_state == "QUESTS":
                    if event.key == pygame.K_ESCAPE:
                        game_state = "MENU"
                    elif is_a or event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB]:
                        quests_tab = "global" if quests_tab == "daily" else "daily"

                elif game_state == "CASES":
                    if show_chances_modal:
                        if event.key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE] or char in ['q', 'й']:
                            show_chances_modal = False
                    else:
                        if case_rolling:
                            pass
                        elif last_won_reward is not None:
                            if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]:
                                last_won_reward = None
                        else:
                            if event.key == pygame.K_ESCAPE:
                                game_state = "MENU"
                            elif event.key == pygame.K_q or char in ['q', 'й'] or event.key == pygame.K_F1:
                                show_chances_modal = True
                            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                                case_price = 75
                                if game_data["coins"] >= case_price:
                                    game_data["coins"] -= case_price
                                    case_rolling = True
                                    roll_timer = 30
                                    rolling_items = [roll_case() for _ in range(6)]
                                    final_won = rolling_items[-1]

                                    if final_won["type"] == "coins":
                                        game_data["coins"] += final_won["amount"]
                                    elif final_won["type"] == "life":
                                        game_data["lives_count"] += 1
                                    elif final_won["type"] == "theme":
                                        if final_won["id"] not in game_data["unlocked_themes"]:
                                            game_data["unlocked_themes"].append(final_won["id"])
                                    elif final_won["type"] == "skin":
                                        if final_won["id"] not in game_data["unlocked_skins"]:
                                            game_data["unlocked_skins"].append(final_won["id"])
                                    save_game_data(game_data)
                                    play_sound("purchase")
                                    last_won_reward = final_won

                elif game_state == "SHOP":
                    cat_key = category_names[shop_category_idx]
                    current_items = SHOP_ITEMS[cat_key]
                    item_idx = selected_item_indices[shop_category_idx]
                    item_info = current_items[item_idx]

                    if confirm_purchase:
                        if event.key in [pygame.K_y, pygame.K_RETURN] or is_y:
                            if game_data["coins"] >= item_info["price"]:
                                game_data["coins"] -= item_info["price"]
                                if item_info["type"] == "skin":
                                    game_data["unlocked_skins"].append(item_info["id"])
                                    game_data["current_skin"] = item_info["id"]
                                elif item_info["type"] == "life":
                                    game_data["lives_count"] += 1
                                elif item_info["type"] == "theme":
                                    game_data["unlocked_themes"].append(item_info["id"])
                                    game_data["current_theme"] = item_info["id"]
                                elif item_info["type"] == "accessory":
                                    game_data["unlocked_accessories"].append(item_info["id"])
                                    game_data["current_accessory"] = item_info["id"]
                                save_game_data(game_data)

                                play_sound("purchase")
                                purchased_item_name = item_info["name"]
                                purchase_anim_timer = 50
                                confetti_list = [
                                    ConfettiParticle(random.randint(100, WIDTH - 100), random.randint(150, 300)) for _
                                    in range(35)]

                            confirm_purchase = False
                        elif event.key in [pygame.K_n, pygame.K_ESCAPE] or is_n:
                            confirm_purchase = False
                    else:
                        if event.key == pygame.K_ESCAPE:
                            game_state = "MENU"
                        elif is_w:
                            shop_category_idx = (shop_category_idx - 1) % len(category_names)
                            insufficient_coins_timer = 0
                        elif is_s:
                            shop_category_idx = (shop_category_idx + 1) % len(category_names)
                            insufficient_coins_timer = 0
                        elif is_a or event.key == pygame.K_LEFT:
                            selected_item_indices[shop_category_idx] = (item_idx - 1) % len(current_items)
                            insufficient_coins_timer = 0
                        elif is_d or event.key == pygame.K_RIGHT:
                            selected_item_indices[shop_category_idx] = (item_idx + 1) % len(current_items)
                            insufficient_coins_timer = 0
                        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                            is_unlocked = False
                            if item_info["type"] == "skin" and item_info["id"] in game_data["unlocked_skins"]:
                                is_unlocked = True
                            elif item_info["type"] == "theme" and item_info["id"] in game_data["unlocked_themes"]:
                                is_unlocked = True
                            elif item_info["type"] == "accessory" and item_info["id"] in game_data[
                                "unlocked_accessories"]:
                                is_unlocked = True

                            if is_unlocked:
                                if item_info["type"] == "skin":
                                    game_data["current_skin"] = item_info["id"]
                                elif item_info["type"] == "theme":
                                    game_data["current_theme"] = item_info["id"]
                                elif item_info["type"] == "accessory":
                                    game_data["current_accessory"] = item_info["id"]
                                save_game_data(game_data)
                            else:
                                if game_data["coins"] >= item_info["price"]:
                                    confirm_purchase = True
                                else:
                                    insufficient_coins_timer = 40
                                    play_sound("error")
                        elif is_y:
                            if game_data["coins"] >= item_info["price"]:
                                confirm_purchase = True
                            else:
                                insufficient_coins_timer = 40
                                play_sound("error")

                elif game_state == "REVIVE_PROMPT":
                    if is_y:
                        game_data["lives_count"] -= 1
                        save_game_data(game_data)
                        snake.revive()
                        active_buffs["shield"] = 80
                        viruses.clear()
                        spiders.clear()
                        mines.clear()
                        lasers.clear()
                        game_state = "RUNNING"
                    elif event.key == pygame.K_l or char in ['l', 'д']:
                        play_sound("gameover")
                        game_data["coins"] += earned_coins_match
                        game_data["max_coins_earned"] = max(game_data["max_coins_earned"], game_data["coins"])
                        if score > game_data["high_score"]: game_data["high_score"] = score
                        if match_time_seconds > game_data["max_time_survived"]: game_data[
                            "max_time_survived"] = match_time_seconds
                        if bosses_killed_match > game_data["max_bosses_killed"]: game_data[
                            "max_bosses_killed"] = bosses_killed_match
                        if combo > game_data.get("max_combo", 1): game_data["max_combo"] = combo
                        save_game_data(game_data)
                        game_state = "GAME_OVER"

                elif game_state == "GAME_OVER":
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                        game_state = "MENU"

                elif game_state == "RUNNING":
                    if event.key in [pygame.K_ESCAPE, pygame.K_p] or char in ['p', 'з']:
                        game_state = "PAUSED"
                    elif (event.key == pygame.K_f or char in ['f', 'а']) and game_data.get(
                            "current_skin") == "dragon" and snake.fireball_cooldown <= 0:
                        snake.fireball_cooldown = 15
                        fireballs.append(Fireball(snake.body[0], snake.direction))
                        play_sound("eat")
                    elif (event.key == pygame.K_e or char in ['e', 'у']) and snake.ability_cooldown <= 0:
                        curr_s = game_data.get("current_skin")
                        if curr_s == "zeus":
                            snake.ability_cooldown = 60
                            viruses.clear()
                            for sp in spiders[:]:
                                sp.hit_and_bounce(snake.body)
                                if sp.health <= 0:
                                    score += 150
                                    bosses_killed_match += 1
                                    spiders.remove(sp)
                            play_sound("powerup")
                            pickup_text = "МОЛНИЯ ЗЕВСА!"
                            pickup_text_timer = 40
                        elif curr_s == "void_lord":
                            snake.ability_cooldown = 60
                            head_p = snake.body[0]
                            for f in foods:
                                f['pos'] = head_p
                            play_sound("purchase")
                            pickup_text = "ЧЁРНАЯ ДЫРА!"
                            pickup_text_timer = 40

                    elif event.key == pygame.K_SPACE and snake.ult_charge >= 100.0:
                        snake.ult_charge = 0.0
                        viruses.clear()
                        spiders.clear()
                        mines.clear()
                        lasers.clear()
                        snake.hp = min(snake.max_hp, snake.hp + 30)
                        play_sound("purchase")
                        screen_shake_timer = 20
                    elif is_w and snake.direction != (0, 1):
                        snake.next_direction = (0, -1)
                    elif is_s and snake.direction != (0, -1):
                        snake.next_direction = (0, 1)
                    elif is_a and snake.direction != (1, 0):
                        snake.next_direction = (-1, 0)
                    elif is_d and snake.direction != (-1, 0):
                        snake.next_direction = (1, 0)

                elif game_state == "PAUSED":
                    if event.key in [pygame.K_ESCAPE, pygame.K_p] or char in ['p', 'з']:
                        game_state = "RUNNING"

        if game_state == "CASES" and case_rolling:
            roll_timer -= 1
            if roll_timer <= 0:
                case_rolling = False

        skin_key = game_data.get("current_skin", "classic")
        speed_modifier = (2 if game_mode == "APOCALYPSE" else 0) + (1 if skin_key == "soccer" else 0)
        base_delay = max(2, 6 - (eaten_count // 5) - speed_modifier)
        move_delay = 8 if active_buffs["slowmo"] > 0 else base_delay

        if game_state == "RUNNING":
            frame_counter += 1
            particles.update()

            if screen_shake_timer > 0: screen_shake_timer -= 1
            if pickup_text_timer > 0: pickup_text_timer -= 1
            if insufficient_coins_timer > 0: insufficient_coins_timer -= 1

            if combo_timer > 0:
                combo_timer -= 1
                if combo_timer == 0: combo = 1

            if frame_counter % 700 == 0:
                current_event = random.choice(["МЕТЕОРИТЫ", "ЗАТМЕНИЕ", "МАГНИТНАЯ БУРЯ"])
                event_timer = 200

            if event_timer > 0:
                event_timer -= 1
                if current_event == "МЕТЕОРИТЫ" and frame_counter % 20 == 0:
                    meteor_shadows.append(
                        {'pos': (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1)), 'timer': 20})
                elif current_event == "МАГНИТНАЯ БУРЯ" and frame_counter % 5 == 0:
                    for f in foods:
                        f['pos'] = ((f['pos'][0] + random.choice([-1, 0, 1])) % GRID_WIDTH,
                                    (f['pos'][1] + random.choice([-1, 0, 1])) % GRID_HEIGHT)
                if event_timer == 0:
                    current_event = None

            for m in meteor_shadows[:]:
                m['timer'] -= 1
                if m['timer'] <= 0:
                    if snake.body[0] == m['pos']:
                        snake.take_damage(40, is_shielded=(active_buffs["shield"] > 0))
                        screen_shake_timer = 15
                    meteor_shadows.remove(m)

            if frame_counter % 20 == 0:
                match_time_seconds += 1
                update_quest_progress("survive", amount=1, match_time=match_time_seconds)
                update_quest_progress("survival_check", amount=1)
                check_achievements(match_time_seconds, bosses_killed_match, combo,
                                   is_apocalypse=(game_mode == "APOCALYPSE"))

            for b in list(active_buffs.keys()):
                if active_buffs[b] > 0:
                    active_buffs[b] -= 1

            for f in foods[:]:
                if 'timer' in f:
                    f['timer'] -= 1
                    if f['timer'] <= 0:
                        foods.remove(f)

            for fb in fireballs[:]:
                fb.update()
                if not fb.active:
                    fireballs.remove(fb)
                    continue
                for v in viruses[:]:
                    if int(fb.pos[0]) == v.pos[0] and int(fb.pos[1]) == v.pos[1]:
                        viruses.remove(v)
                        fb.active = False
                        break
                for sp in spiders[:]:
                    if abs(fb.pos[0] - sp.pos[0]) <= 1 and abs(fb.pos[1] - sp.pos[1]) <= 1:
                        fb.active = False
                        sp.hit_and_bounce(snake.body)
                        if sp.health <= 0:
                            score += 150
                            bosses_killed_match += 1
                            update_quest_progress("boss", amount=1)
                            spiders.remove(sp)
                        break

            laser_cooldown = 80 if game_mode == "APOCALYPSE" else 250
            if frame_counter % laser_cooldown == 0 and len(lasers) < (2 if game_mode == "APOCALYPSE" else 1):
                lasers.append(
                    {'y': random.randint(0, GRID_HEIGHT - 1), 'timer': 40 if game_mode == "APOCALYPSE" else 60})

            for l in lasers[:]:
                l['timer'] -= 1
                if l['timer'] == 0:
                    lasers.remove(l)

            mag_range = 6 if skin_key == "phoenix" else 4
            if active_buffs["magnet"] > 0:
                head_pos = snake.body[0]
                for f in foods:
                    dist = abs(head_pos[0] - f['pos'][0]) + abs(head_pos[1] - f['pos'][1])
                    if dist <= mag_range and dist > 0:
                        fx, fy = f['pos']
                        f['pos'] = (fx + (1 if head_pos[0] > fx else (-1 if head_pos[0] < fx else 0)),
                                    fy + (1 if head_pos[1] > fy else (-1 if head_pos[1] < fy else 0)))

            if frame_counter % move_delay == 0:
                if not snake.update() or snake.hp <= 0:
                    if game_data.get("lives_count", 0) > 0:
                        game_state = "REVIVE_PROMPT"
                    else:
                        play_sound("gameover")
                        game_data["coins"] += earned_coins_match
                        game_data["max_coins_earned"] = max(game_data["max_coins_earned"], game_data["coins"])
                        if score > game_data["high_score"]: game_data["high_score"] = score
                        update_quest_progress("score_check", score_val=score)
                        if match_time_seconds > game_data["max_time_survived"]: game_data[
                            "max_time_survived"] = match_time_seconds
                        if bosses_killed_match > game_data["max_bosses_killed"]: game_data[
                            "max_bosses_killed"] = bosses_killed_match
                        if combo > game_data.get("max_combo", 1): game_data["max_combo"] = combo
                        save_game_data(game_data)
                        game_state = "GAME_OVER"

                head = snake.body[0]

                laser_damage = 50 if game_mode == "APOCALYPSE" else 30
                for l in lasers:
                    if l['timer'] < 15 and head[1] == l['y']:
                        snake.take_damage(laser_damage, viruses, is_shielded=(active_buffs["shield"] > 0))
                        screen_shake_timer = 20

                mine_damage = 45 if game_mode == "APOCALYPSE" else 25
                if head in mines:
                    mines.remove(head)
                    if skin_key != "void_lord":
                        snake.take_damage(mine_damage, viruses, is_shielded=(active_buffs["shield"] > 0))
                    screen_shake_timer = 20

                if active_buffs["freeze"] <= 0:
                    for virus in viruses:
                        virus.move_towards(head)

                    for spider in spiders[:]:
                        for m in spider.minis: m.move_randomly()
                        for m in spider.minis[:]:
                            if head == m.pos:
                                snake.take_damage(int(snake.max_hp * 0.2), viruses,
                                                  is_shielded=(active_buffs["shield"] > 0))
                                spider.minis.remove(m)

                        if abs(head[0] - spider.pos[0]) <= 1 and abs(head[1] - spider.pos[1]) <= 1:
                            spider.hit_and_bounce(snake.body)
                            snake.grow_pending = True
                            if spider.health <= 0:
                                score += 150
                                bosses_killed_match += 1
                                update_quest_progress("boss", amount=1)
                                spiders.remove(spider)

                for virus in viruses[:]:
                    if head == virus.pos:
                        score += 50
                        viruses.remove(virus)
                    elif virus.pos in snake.body:
                        snake.take_damage(25, viruses, is_shielded=(active_buffs["shield"] > 0))
                        viruses.remove(virus)

                for f in foods[:]:
                    if head == f['pos']:
                        foods.remove(f)
                        eaten_count += 1
                        snake.grow_pending = True

                        coin_mult = (3 if game_mode == "APOCALYPSE" else 1) * (
                            1.5 if skin_key == "soccer" else (2.0 if skin_key == "crystal_king" else 1.0))
                        earned_coins_match += int(1 * coin_mult)
                        update_quest_progress("coins", amount=int(1 * coin_mult))

                        ult_add = 12.0 * (1.2 if skin_key == "cyber" else 1.0)
                        snake.ult_charge = min(100.0, snake.ult_charge + ult_add)

                        particles.add(head[0] * GRID_SIZE + GRID_SIZE // 2, head[1] * GRID_SIZE + GRID_SIZE // 2,
                                      GOLD_COLOR)

                        combo = min(5, combo + 1)
                        combo_timer = 50
                        update_quest_progress("combo", amount=combo)

                        if f['type'] in ["apple", "special_apple"]:
                            score += int((10 * combo) * coin_mult)
                            update_quest_progress("apple", amount=1)
                            update_quest_progress("score_check", score_val=score)
                            play_sound("eat")
                        elif f['type'] == "freeze":
                            freeze_dur = 200 if skin_key == "ghost" else 120
                            active_buffs["freeze"] = freeze_dur
                            update_quest_progress("bonus", amount=1)
                            pickup_text = "ЗАМОРОЗКА ВРЕМЕНИ!"
                            pickup_text_timer = 40
                            play_sound("powerup")
                        elif f['type'] == "shield":
                            active_buffs["shield"] = 120
                            update_quest_progress("bonus", amount=1)
                            pickup_text = "АКТИВЕН ЩИТ!"
                            pickup_text_timer = 40
                            play_sound("powerup")
                        elif f['type'] == "nuke":
                            viruses.clear()
                            spiders.clear()
                            mines.clear()
                            update_quest_progress("bonus", amount=1)
                            pickup_text = "ЯДЕРНЫЙ УДАР!"
                            pickup_text_timer = 40
                            screen_shake_timer = 25
                            play_sound("purchase")
                        elif f['type'] == "slowmo":
                            active_buffs["slowmo"] = 160
                            update_quest_progress("bonus", amount=1)
                            pickup_text = "УМЕНЬШЕНИЕ СКОРОСТИ!"
                            pickup_text_timer = 40
                            play_sound("powerup")
                        elif f['type'] == "magnet":
                            active_buffs["magnet"] = 200
                            update_quest_progress("bonus", amount=1)
                            pickup_text = "МАГНИТ ЕДЫ!"
                            pickup_text_timer = 40
                            play_sound("powerup")
                        elif f['type'] == "armor_bonus":
                            snake.armor = min(snake.max_armor, snake.armor + 50)
                            update_quest_progress("bonus", amount=1)
                            pickup_text = "ПОЛУЧЕНА БРОНЯ!"
                            pickup_text_timer = 40
                            play_sound("bonus")
                        elif f['type'] == "medkit":
                            snake.hp = min(snake.max_hp, snake.hp + 25)
                            update_quest_progress("bonus", amount=1)
                            pickup_text = "АПТЕЧКА (ЛЕЧЕНИЕ)!"
                            pickup_text_timer = 40
                            play_sound("bonus")

                        if random.random() < 0.12: spawn_food(snake.body, foods, viruses, spiders, mines, "freeze")
                        if random.random() < 0.10: spawn_food(snake.body, foods, viruses, spiders, mines, "shield")
                        if random.random() < 0.08: spawn_food(snake.body, foods, viruses, spiders, mines, "armor_bonus")
                        if random.random() < 0.08: spawn_food(snake.body, foods, viruses, spiders, mines, "medkit")
                        if random.random() < 0.05: spawn_food(snake.body, foods, viruses, spiders, mines, "nuke")

                        mine_freq = 3 if game_mode == "APOCALYPSE" else 12
                        virus_freq = 3 if game_mode == "APOCALYPSE" else 15
                        spider_freq = 6 if game_mode == "APOCALYPSE" else 25

                        if eaten_count % mine_freq == 0: mines.append(
                            (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1)))
                        if eaten_count % virus_freq == 0: viruses.append(VirusEnemy(snake.body))
                        if eaten_count % spider_freq == 0: spiders.append(SpiderBoss(snake.body))

                        if not any(item['type'] in ["apple", "special_apple"] for item in foods):
                            spawn_food(snake.body, foods, viruses, spiders, mines, "apple")

        shake_x = random.randint(-5, 5) if screen_shake_timer > 0 else 0
        shake_y = random.randint(-5, 5) if screen_shake_timer > 0 else 0

        temp_surface = pygame.Surface((WIDTH, HEIGHT))
        draw_background(temp_surface, game_mode, current_event)

        for ms in meteor_shadows:
            px, py = ms['pos'][0] * GRID_SIZE, ms['pos'][1] * GRID_SIZE
            pygame.draw.circle(temp_surface, (255, 50, 0), (px + GRID_SIZE // 2, py + GRID_SIZE // 2), GRID_SIZE // 2,
                               2)

        for l in lasers:
            ly = l['y'] * GRID_SIZE
            col = (255, 255, 255) if l['timer'] % 4 < 2 else LASER_COLOR
            pygame.draw.rect(temp_surface, col, (0, ly + 6, WIDTH, 8))

        for m in mines:
            mx, my = m[0] * GRID_SIZE, m[1] * GRID_SIZE
            pygame.draw.circle(temp_surface, MINE_COLOR, (mx + GRID_SIZE // 2, my + GRID_SIZE // 2), 7)

        for f in foods:
            px, py = f['pos'][0] * GRID_SIZE, f['pos'][1] * GRID_SIZE
            center_x = px + GRID_SIZE // 2
            center_y = py + GRID_SIZE // 2

            if f['type'] == "apple":
                pygame.draw.rect(temp_surface, FOOD_COLOR, pygame.Rect(px + 2, py + 2, GRID_SIZE - 4, GRID_SIZE - 4),
                                 border_radius=6)
            elif f['type'] == "medkit":
                pill_rect = pygame.Rect(px + 2, py + 5, GRID_SIZE - 4, GRID_SIZE - 10)
                half_left = pygame.Rect(px + 2, py + 5, (GRID_SIZE - 4) // 2, GRID_SIZE - 10)
                half_right = pygame.Rect(center_x, py + 5, (GRID_SIZE - 4) // 2, GRID_SIZE - 10)
                pygame.draw.rect(temp_surface, (230, 40, 40), half_left, border_top_left_radius=6,
                                 border_bottom_left_radius=6)
                pygame.draw.rect(temp_surface, (245, 245, 245), half_right, border_top_right_radius=6,
                                 border_bottom_right_radius=6)
                pygame.draw.rect(temp_surface, (200, 200, 200), pill_rect, 1, border_radius=6)
                pygame.draw.line(temp_surface, (180, 180, 180), (center_x, py + 5), (center_x, py + GRID_SIZE - 5), 1)
            elif f['type'] == "armor_bonus":
                pygame.draw.rect(temp_surface, ARMOR_BONUS_COLOR,
                                 pygame.Rect(px + 4, py + 3, GRID_SIZE - 8, GRID_SIZE - 6), border_radius=4)
                pygame.draw.rect(temp_surface, (240, 240, 255),
                                 pygame.Rect(px + 7, py + 6, GRID_SIZE - 14, GRID_SIZE - 12), border_radius=2)
            elif f['type'] == "freeze":
                pygame.draw.circle(temp_surface, FREEZE_COLOR, (center_x, center_y), GRID_SIZE // 2 - 2)
                pygame.draw.line(temp_surface, (255, 255, 255), (center_x - 5, center_y), (center_x + 5, center_y), 2)
                pygame.draw.line(temp_surface, (255, 255, 255), (center_x, center_y - 5), (center_x, center_y + 5), 2)
            elif f['type'] == "nuke":
                pygame.draw.circle(temp_surface, NUKES_COLOR, (center_x, center_y), GRID_SIZE // 2 - 2)
                pygame.draw.circle(temp_surface, (30, 30, 30), (center_x, center_y), 3)
            else:
                rect = pygame.Rect(px + 2, py + 2, GRID_SIZE - 4, GRID_SIZE - 4)
                color = SHIELD_COLOR if f['type'] == "shield" else (
                    SLOWMO_COLOR if f['type'] == "slowmo" else MAGNET_COLOR)
                pygame.draw.rect(temp_surface, color, rect, border_radius=6)

            if 'timer' in f:
                secs_left = math.ceil(f['timer'] / 20)
                t_surf = font_tiny.render(f"{secs_left}s", True, GOLD_COLOR)
                temp_surface.blit(t_surf, (px + 2, py - 12))

        for fb in fireballs: fb.draw(temp_surface)
        for virus in viruses: virus.draw(temp_surface)
        for spider in spiders: spider.draw(temp_surface)

        snake.draw(temp_surface, foods, is_shielded=(active_buffs["shield"] > 0))
        particles.draw(temp_surface)

        if current_event == "ЗАТМЕНИЕ":
            dark_mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark_mask.fill((0, 0, 0, 235))
            hx, hy = snake.body[0][0] * GRID_SIZE + GRID_SIZE // 2, snake.body[0][1] * GRID_SIZE + GRID_SIZE // 2
            pygame.draw.circle(dark_mask, (0, 0, 0, 0), (hx, hy), 100)
            temp_surface.blit(dark_mask, (0, 0))

        if pickup_text_timer > 0:
            p_surf = font_large.render(pickup_text, True, GOLD_COLOR)
            temp_surface.blit(p_surf, (WIDTH // 2 - p_surf.get_width() // 2, HEIGHT // 2 - 100))

        if game_state == "RUNNING":
            draw_hud(temp_surface, score, game_data["high_score"], snake.hp, snake.max_hp, snake.armor, snake.max_armor,
                     game_data["coins"] + earned_coins_match, game_data["lives_count"], active_buffs, snake.ult_charge,
                     combo, game_mode, current_event)
            draw_dev_watermarks(temp_surface, show_side_author=False)
            # Кнопка паузы в правом верхнем углу, нажимается мышью.
            pause_rect = pygame.Rect(WIDTH - 58, 12, 42, 42)
            pygame.draw.rect(temp_surface, (14, 25, 43), pause_rect, border_radius=9)
            pygame.draw.rect(temp_surface, (0, 255, 200), pause_rect, 2, border_radius=9)
            pygame.draw.rect(temp_surface, (0, 255, 200), (WIDTH - 45, 23, 5, 20), border_radius=2)
            pygame.draw.rect(temp_surface, (0, 255, 200), (WIDTH - 34, 23, 5, 20), border_radius=2)

        elif game_state == "REGISTRATION":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 255))
            temp_surface.blit(overlay, (0, 0))

            t1 = font_title.render("РЕГИСТРАЦИЯ ИГРОКА", True, GOLD_COLOR)
            t2 = font_small.render("Введите ник (только латиница, цифры и символы):", True, TEXT_COLOR)

            box_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 20, 400, 45)
            pygame.draw.rect(temp_surface, (30, 30, 50), box_rect, border_radius=6)
            pygame.draw.rect(temp_surface, SNAKE_HEAD_COLOR, box_rect, 2, border_radius=6)

            t_input = font_small.render(reg_text + "_", True, GOLD_COLOR)
            temp_surface.blit(t_input, (box_rect.x + 15, box_rect.y + 12))

            t_hint = font_small.render("Нажмите ENTER для подтверждения", True, (160, 160, 190))

            temp_surface.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 100))
            temp_surface.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 - 60))
            temp_surface.blit(t_hint, (WIDTH // 2 - t_hint.get_width() // 2, HEIGHT // 2 + 50))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "HELP":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 245))
            temp_surface.blit(overlay, (0, 0))

            t_title = font_title.render("БАЗА ЗНАНИЙ И ЭНЦИКЛОПЕДИЯ", True, GOLD_COLOR)
            temp_surface.blit(t_title, (WIDTH // 2 - t_title.get_width() // 2, 25))

            info_cards = [
                {"type": "virus", "title": "Вирус (Враг)",
                 "desc": "Преследует змейку, наносит 25 ед. урона при касании."},
                {"type": "spider", "title": "Паук-Босс",
                 "desc": "3 HP. Выпускает паутину, отскакивает и спавнит паучков."},
                {"type": "mine", "title": "Мина", "desc": "Взрывается и наносит 25/45 урона при наступании."},
                {"type": "medkit", "title": "Аптечка 💊", "desc": "Восстанавливает +25 HP. Имеет таймер исчезновения!"},
                {"type": "armor", "title": "Броня 🛡️", "desc": "Дает +50 Брони (поглощает входящий урон)."},
                {"type": "freeze", "title": "Заморозка ❄️", "desc": "Останавливает движение врагов и вирусов."},
                {"type": "shield", "title": "Щит 🛡️", "desc": "Делает змейку полностью неуязвимой на время."},
                {"type": "nuke", "title": "Ядерный удар ☢️", "desc": "Мгновенно уничтожает всех вирусов и мины с поля."}
            ]

            for idx, item in enumerate(info_cards):
                y_pos = 80 + (idx * 58)
                x_ic = 80

                if item["type"] == "virus":
                    pygame.draw.circle(temp_surface, (180, 20, 50), (x_ic + 12, y_pos + 12), 10)
                elif item["type"] == "spider":
                    pygame.draw.circle(temp_surface, SPIDER_COLOR, (x_ic + 12, y_pos + 12), 11)
                elif item["type"] == "mine":
                    pygame.draw.circle(temp_surface, MINE_COLOR, (x_ic + 12, y_pos + 12), 8)
                elif item["type"] == "medkit":
                    p_rect = pygame.Rect(x_ic, y_pos + 2, 22, 14)
                    pygame.draw.rect(temp_surface, (230, 40, 40), p_rect, border_radius=4)
                elif item["type"] == "armor":
                    pygame.draw.rect(temp_surface, ARMOR_BONUS_COLOR, (x_ic, y_pos, 22, 22), border_radius=4)
                else:
                    c_col = FREEZE_COLOR if item["type"] == "freeze" else (
                        SHIELD_COLOR if item["type"] == "shield" else NUKES_COLOR)
                    pygame.draw.rect(temp_surface, c_col, (x_ic, y_pos, 22, 22), border_radius=4)

                t_t = font_small.render(item["title"], True, GOLD_COLOR)
                t_d = font_tiny.render(item["desc"], True, TEXT_COLOR)
                temp_surface.blit(t_t, (115, y_pos - 2))
                temp_surface.blit(t_d, (115, y_pos + 18))

            t_back = font_small.render("Нажмите ESC для возврата в главное меню", True, GOLD_COLOR)
            temp_surface.blit(t_back, (WIDTH // 2 - t_back.get_width() // 2, HEIGHT - 45))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "PAUSED":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 210))
            temp_surface.blit(overlay, (0, 0))

            t_pause1 = font_title.render("ИГРА НА ПАУЗЕ", True, GOLD_COLOR)
            t_pause2 = font_tiny.render("Нажмите ESC / P или выберите действие мышью", True, TEXT_COLOR)
            temp_surface.blit(t_pause1, (WIDTH // 2 - t_pause1.get_width() // 2, HEIGHT // 2 - 105))
            temp_surface.blit(t_pause2, (WIDTH // 2 - t_pause2.get_width() // 2, HEIGHT // 2 - 55))
            resume_rect = pygame.Rect(WIDTH // 2 - 145, HEIGHT // 2 + 5, 290, 48)
            exit_rect = pygame.Rect(WIDTH // 2 - 145, HEIGHT // 2 + 65, 290, 48)
            draw_menu_button(temp_surface, resume_rect, "ПРОДОЛЖИТЬ", (0, 255, 170), resume_rect.collidepoint(pygame.mouse.get_pos()))
            draw_menu_button(temp_surface, exit_rect, "ВЫЙТИ В МЕНЮ", (255, 100, 100), exit_rect.collidepoint(pygame.mouse.get_pos()))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "SPLASH":
            elapsed = time.time() - splash_started
            temp_surface.fill((3, 5, 14))
            # Мягкое появление логотипа из чёрного экрана.
            alpha = max(0, min(255, int((elapsed / 2.2) * 255)))
            glow = int(100 + 100 * abs(math.sin(elapsed * 2.4)))
            logo = font_title.render("CYBER SNAKE", True, (0, 255, 170))
            subtitle = font_large.render("NEON SURVIVAL", True, (255, 210, 70))
            logo.set_alpha(alpha)
            subtitle.set_alpha(max(0, alpha-25))
            # Неоновая змейка вместо декоративного кольца.
            snake_points = [(344, 245), (351, 222), (372, 207), (397, 210),
                            (418, 228), (423, 249), (410, 266), (388, 268), (372, 253)]
            snake_glow = (0, max(0, min(255, glow)), 150)
            pygame.draw.lines(temp_surface, (0, 85, 85), False, snake_points, 19)
            pygame.draw.lines(temp_surface, snake_glow, False, snake_points, 11)
            for point in snake_points[1:-1]:
                pygame.draw.circle(temp_surface, snake_glow, point, 5)
            head_x, head_y = snake_points[0]
            pygame.draw.circle(temp_surface, (0, 255, 175), (head_x, head_y), 12)
            pygame.draw.circle(temp_surface, (5, 15, 30), (head_x - 3, head_y - 3), 2)
            pygame.draw.circle(temp_surface, (5, 15, 30), (head_x + 4, head_y - 3), 2)
            pygame.draw.line(temp_surface, (255, 100, 150), (head_x - 1, head_y + 5), (head_x + 6, head_y + 5), 2)
            logo_y = HEIGHT//2 - 70
            temp_surface.blit(logo, (WIDTH//2-logo.get_width()//2, logo_y))
            temp_surface.blit(subtitle, (WIDTH//2-subtitle.get_width()//2, HEIGHT//2-15))
            dev = font_tiny.render("Developed by MONZAY", True, (100, 220, 210))
            dev.set_alpha(alpha)
            temp_surface.blit(dev, (WIDTH//2-dev.get_width()//2, HEIGHT//2+30))
            if elapsed > 2.3:
                hint = font_small.render("НАЖМИТЕ МЫШЬЮ ИЛИ ЛЮБУЮ КЛАВИШУ", True, (220, 230, 245))
                hint.set_alpha(int(150 + 105 * abs(math.sin(elapsed*3))))
                temp_surface.blit(hint, (WIDTH//2-hint.get_width()//2, HEIGHT//2+55))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "HOME":
            temp_surface.fill((5, 8, 22))
            # Фоновые неоновые кольца и декоративные звёзды.
            for i in range(7):
                radius = 65 + i*34
                pygame.draw.circle(temp_surface, (8, 35+i*3, 46+i*2), (WIDTH//2, 190), radius, 1)
            title = font_title.render("CYBER SNAKE", True, SNAKE_HEAD_COLOR)
            subtitle = font_small.render("NEON ARCADE EXPERIENCE", True, (170, 190, 215))
            temp_surface.blit(title, (WIDTH//2-title.get_width()//2, 115))
            temp_surface.blit(subtitle, (WIDTH//2-subtitle.get_width()//2, 175))
            developer = font_tiny.render("Developed by MONZAY", True, (0, 230, 190))
            temp_surface.blit(developer, (WIDTH//2-developer.get_width()//2, 202))
            welcome = font_small.render(f"{game_data.get('player_name', 'Player')}  •  {game_data['coins']} coins", True, GOLD_COLOR)
            temp_surface.blit(welcome, (WIDTH//2-welcome.get_width()//2, 245))
            mouse_pos = pygame.mouse.get_pos()
            draw_menu_button(temp_surface, pygame.Rect(WIDTH//2-170, 360, 340, 54), ui("start"), (0,255,170), pygame.Rect(WIDTH//2-170,360,340,54).collidepoint(mouse_pos))
            draw_menu_button(temp_surface, pygame.Rect(WIDTH//2-170, 430, 340, 54), ui("settings"), (80,170,255), pygame.Rect(WIDTH//2-170,430,340,54).collidepoint(mouse_pos))
            draw_menu_button(temp_surface, pygame.Rect(WIDTH//2-170, 500, 340, 54), ui("info"), (255,205,70), pygame.Rect(WIDTH//2-170,500,340,54).collidepoint(mouse_pos))
            hint = font_tiny.render(ui("hint"), True, (140,155,180))
            temp_surface.blit(hint, (WIDTH//2-hint.get_width()//2, 580))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "SETTINGS":
            temp_surface.fill((5, 8, 22))
            title = font_title.render(ui("settings"), True, SNAKE_HEAD_COLOR)
            temp_surface.blit(title, (WIDTH//2-title.get_width()//2, 180))
            lang_title = font_small.render(ui("choose_lang"), True, GOLD_COLOR)
            temp_surface.blit(lang_title, (WIDTH//2-lang_title.get_width()//2, 300))
            idx = LANG_CODES.index(game_data.get("language", "ru")) if game_data.get("language", "ru") in LANG_CODES else 0
            draw_menu_button(temp_surface, pygame.Rect(WIDTH//2-190, 360, 55, 48), "◀", (80,170,255), pygame.Rect(WIDTH//2-190,360,55,48).collidepoint(pygame.mouse.get_pos()))
            draw_menu_button(temp_surface, pygame.Rect(WIDTH//2-130, 360, 260, 48), LANGUAGES[idx], (0,255,170))
            draw_menu_button(temp_surface, pygame.Rect(WIDTH//2+135, 360, 55, 48), "▶", (80,170,255), pygame.Rect(WIDTH//2+135,360,55,48).collidepoint(pygame.mouse.get_pos()))
            tip = font_tiny.render("← / →  или кнопки мышью", True, (155,170,195))
            temp_surface.blit(tip, (WIDTH//2-tip.get_width()//2, 430))
            draw_menu_button(temp_surface, pygame.Rect(WIDTH//2-120, 520, 240, 52), ui("back"), (255,205,70), pygame.Rect(WIDTH//2-120,520,240,52).collidepoint(pygame.mouse.get_pos()))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "INFO":
            temp_surface.fill((5, 8, 22))
            title = font_title.render(ui("about"), True, SNAKE_HEAD_COLOR)
            temp_surface.blit(title, (WIDTH//2-title.get_width()//2, 55))
            lines = [ui("about1"), ui("about2"), ui("buffs"), ui("freeze"), ui("shield"), ui("magnet"), ui("slowmo"), ui("enemies"), ui("spider"), ui("virus")]
            y = 140
            for i, line in enumerate(lines):
                color = GOLD_COLOR if i in (2, 7) else (225, 235, 250)
                font = font_small if i in (2, 7) else font_tiny
                rendered = font.render(line, True, color)
                temp_surface.blit(rendered, (WIDTH//2-rendered.get_width()//2, y))
                y += 34 if i in (2, 7) else 28
            draw_menu_button(temp_surface, pygame.Rect(WIDTH//2-120, 690, 240, 52), ui("back"), (255,205,70), pygame.Rect(WIDTH//2-120,690,240,52).collidepoint(pygame.mouse.get_pos()))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "MENU":
            # Главный игровой хаб: отдельные панели для режима, ресурсов,
            # быстрых разделов и статистики. Управление осталось прежним.
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 8, 22, 238))
            temp_surface.blit(overlay, (0, 0))
            draw_neon_panel(temp_surface, pygame.Rect(24, 18, WIDTH - 48, HEIGHT - 66), accent=(0, 225, 190))

            # Заголовок и автор
            title = font_title.render("CYBER SNAKE", True, SNAKE_HEAD_COLOR)
            temp_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 48))
            subtitle = ui_font(14).render("ARCADE SURVIVAL  •  by. Monzay", True, (140, 220, 235))
            temp_surface.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 100))

            # Информация об игроке и игровые ресурсы
            top_card = pygame.Rect(48, 135, WIDTH - 96, 82)
            pygame.draw.rect(temp_surface, (14, 25, 43), top_card, border_radius=14)
            pygame.draw.rect(temp_surface, (0, 190, 180), top_card, 2, border_radius=14)
            player_label = game_data.get('player_name') or "Игрок"
            player_text = font_small.render(f"ПРИВЕТ, {player_label.upper()}", True, GOLD_COLOR)
            temp_surface.blit(player_text, (top_card.x + 18, top_card.y + 13))
            coin_text = font_small.render(f"Монеты: {game_data['coins']}", True, TEXT_COLOR)
            lives_text = font_small.render(f"Жизни: {game_data['lives_count']}", True, TEXT_COLOR)
            temp_surface.blit(coin_text, (top_card.x + 18, top_card.y + 47))
            temp_surface.blit(lives_text, (top_card.x + 205, top_card.y + 47))

            # Режим игры и большая кнопка-подсказка запуска
            mode_str = "АПОКАЛИПСИС  •  x3 НАГРАДЫ" if game_mode == "APOCALYPSE" else "КЛАССИКА"
            mode_color = (255, 95, 105) if game_mode == "APOCALYPSE" else SNAKE_HEAD_COLOR
            mode_card = pygame.Rect(48, 232, WIDTH - 96, 66)
            pygame.draw.rect(temp_surface, (20, 23, 42), mode_card, border_radius=12)
            pygame.draw.rect(temp_surface, mode_color, mode_card, 2, border_radius=12)
            mode_label = font_small.render(f"РЕЖИМ: {mode_str}", True, mode_color)
            temp_surface.blit(mode_label, (WIDTH // 2 - mode_label.get_width() // 2, mode_card.y + 8))
            # Кнопки выбора режима — нарисованные стрелки слева и справа.
            arrow_y = mode_card.y + 31
            pygame.draw.polygon(temp_surface, (180, 235, 255), [(68, arrow_y), (86, arrow_y - 12), (86, arrow_y + 12)])
            pygame.draw.polygon(temp_surface, (180, 235, 255), [(732, arrow_y), (714, arrow_y - 12), (714, arrow_y + 12)])
            play_label = font_small.render("[ ПРОБЕЛ ]  НАЧАТЬ ИГРУ", True, (245, 255, 255))
            temp_surface.blit(play_label, (WIDTH // 2 - play_label.get_width() // 2, mode_card.y + 36))

            # Плитки быстрых разделов
            quick_items = [
                ("[ M ]  МАГАЗИН", "Скины, жизни и аксессуары", (0, 220, 190)),
                ("[ Q ]  КВЕСТЫ", "Ежедневные и глобальные миссии", (70, 180, 255)),
                ("[ C ]  КЕЙСЫ И НАГРАДЫ", "Открывай кейсы за монеты", (255, 205, 75)),
                ("[ A ]  ДОСТИЖЕНИЯ", "Рекорды и цели игрока", (190, 125, 255)),
                ("[ H ]  СПРАВКА", "Управление и правила", (100, 220, 255)),
                ("[ R ]  РЕЖИМ ИГРЫ", "Классика или апокалипсис", (255, 110, 120)),
            ]
            tile_w, tile_h, tile_gap = 336, 66, 12
            tile_xs = [48, 416]
            for idx, (label, desc, accent) in enumerate(quick_items):
                col, row = idx % 2, idx // 2
                tile = pygame.Rect(tile_xs[col], 315 + row * (tile_h + tile_gap), tile_w, tile_h)
                pygame.draw.rect(temp_surface, (15, 25, 43), tile, border_radius=11)
                pygame.draw.rect(temp_surface, accent, tile, 2, border_radius=11)
                label_surf = ui_font(17).render(label, True, accent)
                desc_surf = ui_font(13).render(desc, True, (205, 220, 235))
                temp_surface.blit(label_surf, (tile.x + 12, tile.y + 10))
                temp_surface.blit(desc_surf, (tile.x + 12, tile.y + 39))

            # Карточка статистики с ровными строками
            stats_card = pygame.Rect(48, 552, WIDTH - 96, 139)
            pygame.draw.rect(temp_surface, (12, 20, 36), stats_card, border_radius=13)
            pygame.draw.rect(temp_surface, (85, 110, 155), stats_card, 1, border_radius=13)
            stats_title = font_small.render("ВАША СТАТИСТИКА", True, GOLD_COLOR)
            temp_surface.blit(stats_title, (stats_card.x + 16, stats_card.y + 10))
            stats = [
                (f"Рекорд: {game_data['high_score']} очков", (245, 250, 255)),
                (f"Лучшее время: {game_data['max_time_survived']} сек.", (190, 225, 255)),
                (f"Боссы: {game_data['max_bosses_killed']}", (190, 255, 220)),
                (f"Всего монет: {game_data['max_coins_earned']}", (255, 220, 110)),
                (f"Макс. комбо: x{game_data.get('max_combo', 1)}", (255, 160, 100)),
            ]
            positions = [(stats_card.x + 16, stats_card.y + 43),
                         (stats_card.x + 16, stats_card.y + 68),
                         (stats_card.x + 16, stats_card.y + 93),
                         (stats_card.x + 390, stats_card.y + 43),
                         (stats_card.x + 390, stats_card.y + 68)]
            for (label, color), pos in zip(stats, positions):
                stat_surf = font_tiny.render(label, True, color)
                temp_surface.blit(stat_surf, pos)

            draw_dev_watermarks(temp_surface, show_side_author=False)

        elif game_state == "CASES":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 8, 22, 238))
            temp_surface.blit(overlay, (0, 0))
            draw_neon_panel(temp_surface, pygame.Rect(35, 18, WIDTH-70, HEIGHT-70), accent=(255, 205, 70))
            draw_section_heading(temp_surface, "НАГРАДЫ И КЕЙСЫ", "Открывай кейсы и собирай коллекцию", accent=(255, 205, 70))


            q_btn_rect = pygame.Rect(WIDTH // 2 + 230, 35, 45, 45)
            pygame.draw.rect(temp_surface, (40, 40, 70), q_btn_rect, border_radius=8)
            pygame.draw.rect(temp_surface, GOLD_COLOR, q_btn_rect, 2, border_radius=8)
            t_q_sym = font_small.render("[ ? ]", True, GOLD_COLOR)
            temp_surface.blit(t_q_sym, (q_btn_rect.x + 8, q_btn_rect.y + 12))

            if show_chances_modal:
                modal_rect = pygame.Rect(WIDTH // 2 - 260, HEIGHT // 2 - 180, 520, 360)
                pygame.draw.rect(temp_surface, (20, 20, 35), modal_rect, border_radius=10)
                pygame.draw.rect(temp_surface, GOLD_COLOR, modal_rect, 2, border_radius=10)

                t_m_title = font_small.render("ВОЗМОЖНЫЕ НАГРАДЫ И ШАНСЫ", True, GOLD_COLOR)
                temp_surface.blit(t_m_title, (WIDTH // 2 - t_m_title.get_width() // 2, modal_rect.y + 15))

                for idx, rew in enumerate(CASE_REWARDS):
                    ry = modal_rect.y + 50 + (idx * 28)
                    # Цветная мини-карточка и уникальная иконка для каждой награды
                    draw_case_reward_icon(temp_surface, rew, modal_rect.x + 12, ry - 2, 23)
                    t_r_name = font_small.render(rew["name"], True, TEXT_COLOR)
                    t_r_chance = font_small.render(rew["chance"], True, (100, 220, 255))
                    temp_surface.blit(t_r_name, (modal_rect.x + 45, ry))
                    temp_surface.blit(t_r_chance, (modal_rect.right - 70, ry))

                t_m_close = font_tiny.render("Нажмите [ ESC / Q / ПРОБЕЛ ] чтобы закрыть", True, (180, 180, 210))
                temp_surface.blit(t_m_close, (WIDTH // 2 - t_m_close.get_width() // 2, modal_rect.bottom - 30))

            elif case_rolling:
                box_rect = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 - 80, 320, 120)
                pygame.draw.rect(temp_surface, (35, 35, 60), box_rect, border_radius=10)
                pygame.draw.rect(temp_surface, (255, 100, 0), box_rect, 3, border_radius=10)

                t_spin = font_small.render("Открытие кейса...", True, (255, 200, 50))
                temp_surface.blit(t_spin, (WIDTH // 2 - t_spin.get_width() // 2, box_rect.y + 15))

                cur_display_item = rolling_items[(30 - roll_timer) % len(rolling_items)]
                t_curr_name = font_large.render(cur_display_item["name"], True, TEXT_COLOR)
                temp_surface.blit(t_curr_name, (WIDTH // 2 - t_curr_name.get_width() // 2, box_rect.y + 55))

            elif last_won_reward is None:
                box_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 - 90, 240, 140)
                pygame.draw.rect(temp_surface, (35, 35, 60), box_rect, border_radius=10)
                pygame.draw.rect(temp_surface, GOLD_COLOR, box_rect, 2, border_radius=10)

                t_c1 = font_small.render("Стоимость кейса:", True, TEXT_COLOR)
                t_c2 = font_small.render("75 монет", True, GOLD_COLOR)
                t_c3 = font_small.render("Нажмите [ ПРОБЕЛ ]", True, SNAKE_HEAD_COLOR)

                temp_surface.blit(t_c1, (WIDTH // 2 - t_c1.get_width() // 2, HEIGHT // 2 - 70))
                temp_surface.blit(t_c2, (WIDTH // 2 - t_c2.get_width() // 2, HEIGHT // 2 - 45))
                temp_surface.blit(t_c3, (WIDTH // 2 - t_c3.get_width() // 2, HEIGHT // 2 - 10))

                t_my = font_small.render(f"Ваши монеты: {game_data['coins']}", True, GOLD_COLOR)
                temp_surface.blit(t_my, (WIDTH // 2 - t_my.get_width() // 2, HEIGHT // 2 + 80))
            else:
                win_rect = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 120, 440, 220)
                pygame.draw.rect(temp_surface, (25, 25, 45), win_rect, border_radius=12)
                pygame.draw.rect(temp_surface, GOLD_COLOR, win_rect, 3, border_radius=12)

                t_win_title = font_small.render(last_won_reward["congrats"], True, GOLD_COLOR)
                t_item_name = font_large.render(last_won_reward["name"], True, (255, 255, 255))
                t_item_desc = font_small.render(last_won_reward["desc"], True, TEXT_COLOR)
                t_btn = font_small.render("Нажмите [ ПРОБЕЛ ] чтобы забрать", True, SNAKE_HEAD_COLOR)

                temp_surface.blit(t_win_title, (WIDTH // 2 - t_win_title.get_width() // 2, HEIGHT // 2 - 100))
                temp_surface.blit(t_item_name, (WIDTH // 2 - t_item_name.get_width() // 2, HEIGHT // 2 - 50))
                temp_surface.blit(t_item_desc, (WIDTH // 2 - t_item_desc.get_width() // 2, HEIGHT // 2 + 10))
                temp_surface.blit(t_btn, (WIDTH // 2 - t_btn.get_width() // 2, HEIGHT // 2 + 70))

            t_back = font_small.render("Нажмите ESC для возврата в меню", True, GOLD_COLOR)
            temp_surface.blit(t_back, (WIDTH // 2 - t_back.get_width() // 2, HEIGHT - 50))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "SHOP":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 8, 22, 238))
            temp_surface.blit(overlay, (0, 0))
            draw_neon_panel(temp_surface, pygame.Rect(28, 18, WIDTH-56, HEIGHT-70), accent=(0, 220, 190))
            draw_section_heading(temp_surface, "НЕОНОВЫЙ МАГАЗИН", "Скины • жизни • игровые поля • аксессуары")


            cat_labels = ["1  СКИНЫ", "2  ЖИЗНИ", "3  ПОЛЯ", "4  АКСЕССУАРЫ"]
            for idx, label in enumerate(cat_labels):
                tab_rect = pygame.Rect(43 + idx * 180, 125, 170, 38)
                selected = idx == shop_category_idx
                pygame.draw.rect(temp_surface, (20, 48, 62) if selected else (15, 22, 40), tab_rect, border_radius=10)
                pygame.draw.rect(temp_surface, (0, 255, 180) if selected else (65, 85, 115), tab_rect, 2, border_radius=10)
                lbl_surf = font_tiny.render(label, True, GOLD_COLOR if selected else (150, 170, 195))
                temp_surface.blit(lbl_surf, (tab_rect.centerx - lbl_surf.get_width()//2, tab_rect.centery - lbl_surf.get_height()//2))
            draw_neon_panel(temp_surface, pygame.Rect(WIDTH//2-260, HEIGHT//2-155, 520, 360), accent=(0, 160, 220), fill=(10, 17, 34), radius=18, glow=False)

            cat_key = category_names[shop_category_idx]
            current_items = SHOP_ITEMS[cat_key]
            item_idx = selected_item_indices[shop_category_idx]
            item_info = current_items[item_idx]

            if item_info["type"] == "skin":
                sample_start_x = WIDTH // 2 - 40
                sample_y = HEIGHT // 2 - 70
                for i in range(4):
                    seg_rect = pygame.Rect(sample_start_x + (i * 25), sample_y, 22, 22)
                    pygame.draw.rect(temp_surface, item_info["head"] if i == 0 else item_info["body"], seg_rect,
                                     border_radius=4)

                is_unlocked = item_info["id"] in game_data["unlocked_skins"]
                is_equipped = game_data["current_skin"] == item_info["id"]
                status_text = "[ НАДЕТО ]" if is_equipped else (
                    "[ НАЖМИТЕ ПРОБЕЛ ]" if is_unlocked else f"ЦЕНА: {item_info['price']} монет | [ Y ]")

                abil_text = font_small.render(item_info["ability"], True, (100, 220, 255))
                temp_surface.blit(abil_text, (WIDTH // 2 - abil_text.get_width() // 2, HEIGHT // 2 - 20))

            elif item_info["type"] == "life":
                draw_heart_icon(temp_surface, WIDTH // 2 - 14, HEIGHT // 2 - 50, 28)
                status_text = f"КУПЛЕНО: {game_data['lives_count']} шт. | ЦЕНА: {item_info['price']} монет | [ Y ]"

            elif item_info["type"] == "theme":
                theme_data = THEMES.get(item_info["id"], THEMES["cosmos"])
                prev_rect = pygame.Rect(WIDTH // 2 - 80, HEIGHT // 2 - 100, 160, 90)
                temp_surface.fill(theme_data["bg"], prev_rect)
                pygame.draw.rect(temp_surface, GOLD_COLOR, prev_rect, 2, border_radius=6)

                is_unlocked = item_info["id"] in game_data["unlocked_themes"]
                is_equipped = game_data["current_theme"] == item_info["id"]
                status_text = "[ УСТАНОВЛЕНО ]" if is_equipped else (
                    "[ НАЖМИТЕ ПРОБЕЛ ]" if is_unlocked else f"ЦЕНА: {item_info['price']} монет | [ Y ]")

            elif item_info["type"] == "accessory":
                # Большой визуальный предпросмотр: видно форму самого аксессуара.
                preview_card = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 105, 200, 125)
                pygame.draw.rect(temp_surface, (18, 25, 48), preview_card, border_radius=16)
                pygame.draw.rect(temp_surface, (0, 220, 255), preview_card, 2, border_radius=16)
                draw_accessory_preview(temp_surface, item_info["id"], WIDTH // 2, HEIGHT // 2 - 42)

                is_unlocked = item_info["id"] in game_data["unlocked_accessories"]
                is_equipped = game_data["current_accessory"] == item_info["id"]
                status_text = "[ НАДЕТО ]" if is_equipped else (
                    "[ НАЖМИТЕ ПРОБЕЛ ]" if is_unlocked else f"ЦЕНА: {item_info['price']} монет | [ Y ]")

            t_name = font_small.render(f"{item_info['name']} ({item_idx + 1}/{len(current_items)})", True, TEXT_COLOR)
            temp_surface.blit(t_name, (WIDTH // 2 - t_name.get_width() // 2, HEIGHT // 2 + 25))

            t_status = font_small.render(status_text, True, GOLD_COLOR)
            temp_surface.blit(t_status, (WIDTH // 2 - t_status.get_width() // 2, HEIGHT // 2 + 65))

            # Явные мышиные кнопки управления товаром и покупки.
            prev_rect = pygame.Rect(55, 430, 95, 46)
            next_rect = pygame.Rect(650, 430, 95, 46)
            draw_menu_button(temp_surface, prev_rect, "НАЗАД", (75, 190, 255), prev_rect.collidepoint(pygame.mouse.get_pos()))
            draw_menu_button(temp_surface, next_rect, "ВПЕРЁД", (75, 190, 255), next_rect.collidepoint(pygame.mouse.get_pos()))
            # Стрелки рисуются геометрией, поэтому не превращаются в квадратики из-за шрифта.
            pygame.draw.polygon(temp_surface, (170, 235, 255), [(65, 453), (77, 444), (77, 462)])
            pygame.draw.polygon(temp_surface, (170, 235, 255), [(735, 453), (723, 444), (723, 462)])
            action_rect = pygame.Rect(WIDTH//2-150, 565, 300, 48)
            action_label = "ПОДТВЕРДИТЬ ПОКУПКУ" if confirm_purchase else "КУПИТЬ / НАДЕТЬ"
            draw_menu_button(temp_surface, action_rect, action_label, (0, 255, 170), action_rect.collidepoint(pygame.mouse.get_pos()))

            t_coins = font_small.render(f"Ваши монеты: {game_data['coins']}", True, GOLD_COLOR)
            temp_surface.blit(t_coins, (WIDTH // 2 - t_coins.get_width() // 2, HEIGHT // 2 + 110))

            if insufficient_coins_timer > 0:
                t_err = font_small.render("У вас недостаточно монеток!", True, (255, 60, 60))
                temp_surface.blit(t_err, (WIDTH // 2 - t_err.get_width() // 2, HEIGHT // 2 + 145))

            if confirm_purchase:
                box_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 90, 400, 160)
                pygame.draw.rect(temp_surface, (25, 25, 45), box_rect, border_radius=10)
                pygame.draw.rect(temp_surface, GOLD_COLOR, box_rect, 2, border_radius=10)

                t_conf1 = font_small.render(f"Купить «{item_info['name']}»", True, TEXT_COLOR)
                t_conf2 = font_small.render(f"за {item_info['price']} монет?", True, GOLD_COLOR)
                t_conf3 = font_tiny.render("Нажмите [ Y ] — Да  |  [ N / ESC ] — Отмена", True, (180, 180, 210))

                temp_surface.blit(t_conf1, (WIDTH // 2 - t_conf1.get_width() // 2, HEIGHT // 2 - 50))
                temp_surface.blit(t_conf2, (WIDTH // 2 - t_conf2.get_width() // 2, HEIGHT // 2 - 20))
                temp_surface.blit(t_conf3, (WIDTH // 2 - t_conf3.get_width() // 2, HEIGHT // 2 + 30))

            if purchase_anim_timer > 0:
                purchase_anim_timer -= 1

                for c in confetti_list:
                    c.update()
                    c.draw(temp_surface)

                congrat_card = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 60, 500, 120)
                pygame.draw.rect(temp_surface, (15, 25, 45), congrat_card, border_radius=15)
                pygame.draw.rect(temp_surface, (0, 255, 140), congrat_card, 3, border_radius=15)

                cg_t1 = font_small.render("🎉 ПОЗДРАВЛЯЕМ С ПОКУПКОЙ! 🎉", True, GOLD_COLOR)
                cg_t2 = font_large.render(purchased_item_name, True, (255, 255, 255))
                temp_surface.blit(cg_t1, (WIDTH // 2 - cg_t1.get_width() // 2, congrat_card.y + 20))
                temp_surface.blit(cg_t2, (WIDTH // 2 - cg_t2.get_width() // 2, congrat_card.y + 55))

            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "QUESTS":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 8, 22, 238))
            temp_surface.blit(overlay, (0, 0))
            draw_neon_panel(temp_surface, pygame.Rect(28, 18, WIDTH-56, HEIGHT-70), accent=(80, 190, 255))
            draw_section_heading(temp_surface, "ЦЕНТР МИССИЙ", "Выполняй задания, получай монеты и редкие награды", accent=(80, 190, 255))


            tab_d_col = GOLD_COLOR if quests_tab == "daily" else (120, 120, 150)
            tab_g_col = GOLD_COLOR if quests_tab == "global" else (120, 120, 150)
            tab_d_rect = pygame.Rect(WIDTH//2-310, 65, 300, 50)
            tab_g_rect = pygame.Rect(WIDTH//2+10, 65, 300, 50)
            draw_menu_button(temp_surface, tab_d_rect, "ЕЖЕДНЕВНЫЕ КВЕСТЫ", (80, 190, 255), quests_tab == "daily" or tab_d_rect.collidepoint(pygame.mouse.get_pos()))
            draw_menu_button(temp_surface, tab_g_rect, "ГЛОБАЛЬНЫЕ КВЕСТЫ", (80, 190, 255), quests_tab == "global" or tab_g_rect.collidepoint(pygame.mouse.get_pos()))

            if quests_tab == "daily":
                remaining = max(0, 21600 - int(time.time() - game_data.get("last_daily_reset", time.time())))
                hours_left = remaining // 3600
                minutes_left = (remaining % 3600) // 60
                reset_bg = pygame.Rect(55, 105, WIDTH - 110, 36)
                pygame.draw.rect(temp_surface, (14, 35, 55), reset_bg, border_radius=10)
                pygame.draw.rect(temp_surface, (0, 190, 255), reset_bg, 1, border_radius=10)
                reset_label = font_tiny.render(
                    f"ОБНОВЛЕНИЕ ЧЕРЕЗ  {hours_left:02d}:{minutes_left:02d}  •  НОВЫЕ МИССИИ КАЖДЫЕ 6 ЧАСОВ",
                    True, (110, 225, 255))
                temp_surface.blit(reset_label, (WIDTH // 2 - reset_label.get_width() // 2, reset_bg.y + 11))

                quest_descs = {
                    "eat_apples": "Съесть 15 яблок",
                    "survive_45": "Продержаться 45 секунд",
                    "kill_boss_daily": "Победить паука-босса",
                    "collect_bonuses": "Собрать 5 бонусов",
                    "earn_coins": "Заработать 50 монет",
                    "reach_combo_3": "Достичь комбо x3"
                }
                quest_icons = {
                    "eat_apples": "ЯБЛОКИ", "survive_45": "ВЫЖИВАНИЕ",
                    "kill_boss_daily": "БОСС", "collect_bonuses": "БОНУСЫ",
                    "earn_coins": "МОНЕТЫ", "reach_combo_3": "КОМБО"
                }
                card_w, card_h = 332, 154
                card_xs, card_ys = [54, 414], [154, 322, 490]
                for idx, (qid, qval) in enumerate(game_data["daily_quests"].items()):
                    col, row = idx % 2, idx // 2
                    card = pygame.Rect(card_xs[col], card_ys[row], card_w, card_h)
                    done = bool(qval["done"])
                    accent = (45, 220, 145) if done else (45, 165, 225)
                    pygame.draw.rect(temp_surface, (13, 25, 43), card, border_radius=13)
                    pygame.draw.rect(temp_surface, accent, card, 2, border_radius=13)
                    tag = pygame.Rect(card.x + 12, card.y + 11, card_w - 24, 25)
                    pygame.draw.rect(temp_surface, (22, 43, 62), tag, border_radius=7)
                    tag_surf = font_tiny.render(quest_icons.get(qid, "МИССИЯ"), True, accent)
                    temp_surface.blit(tag_surf, (tag.x + 9, tag.y + 6))
                    title_surf = font_small.render(quest_descs[qid], True, (245, 250, 255))
                    temp_surface.blit(title_surf, (card.x + 14, card.y + 48))
                    progress = min(qval["progress"], qval["target"])
                    progress_text = "ВЫПОЛНЕНО" if done else f"Прогресс: {progress} / {qval['target']}"
                    progress_surf = font_tiny.render(progress_text, True, accent if done else (190, 210, 230))
                    temp_surface.blit(progress_surf, (card.x + 14, card.y + 80))
                    bar = pygame.Rect(card.x + 14, card.y + 104, card_w - 28, 8)
                    pygame.draw.rect(temp_surface, (32, 43, 60), bar, border_radius=4)
                    ratio = (progress / qval["target"]) if qval["target"] else 0
                    fill_w = int(bar.width * max(0, min(1, ratio)))
                    if fill_w:
                        pygame.draw.rect(temp_surface, accent, pygame.Rect(bar.x, bar.y, fill_w, bar.height), border_radius=4)
                    reward_bg = pygame.Rect(card.x + 12, card.y + 122, card_w - 24, 23)
                    pygame.draw.rect(temp_surface, (34, 35, 49), reward_bg, border_radius=7)
                    reward_surf = font_tiny.render(f"НАГРАДА  +{qval['reward']} МОНЕТ", True, (255, 220, 100))
                    temp_surface.blit(reward_surf, (reward_bg.x + 9, reward_bg.y + 5))

            else:
                for idx, (qid, qval) in enumerate(game_data["global_quests"].items()):
                    info = GLOBAL_QUESTS_INFO[qid]
                    curr_prog = "ВЫПОЛНЕНО" if qval['done'] else f"{qval['progress']}/{qval['target']}"
                    status_str = f"[{curr_prog} | Награда: +{qval['reward_coins']} монет + Скин '{info['skin_name']}']"
                    color = (50, 240, 120) if qval['done'] else (255, 255, 255)

                    q_title_surf = font_small.render(f"{info['name']}: {info['desc']}", True, GOLD_COLOR)
                    q_prog_surf = font_tiny.render(status_str, True, color)

                    y_pos = 125 + (idx * 75)
                    temp_surface.blit(q_title_surf, (WIDTH // 2 - 340, y_pos))
                    temp_surface.blit(q_prog_surf, (WIDTH // 2 - 340, y_pos + 24))

            back_rect = pygame.Rect(WIDTH//2-150, HEIGHT-62, 300, 42)
            draw_menu_button(temp_surface, back_rect, "← НАЗАД В МЕНЮ", (255, 205, 70), back_rect.collidepoint(pygame.mouse.get_pos()))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "ACHIEVEMENTS":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 8, 22, 238))
            temp_surface.blit(overlay, (0, 0))
            draw_neon_panel(temp_surface, pygame.Rect(28, 18, WIDTH-56, HEIGHT-70), accent=(190, 120, 255))
            draw_section_heading(temp_surface, "ЗАЛ ДОСТИЖЕНИЙ", "Каждый рекорд приближает тебя к следующей награде", accent=(190, 120, 255))


            for idx, ach in enumerate(ACHIEVEMENTS_LIST):
                is_done = game_data["achievements"].get(ach["id"], False)
                status_str = f"[ ВЫПОЛНЕНО (+{ach['reward']} монет) ]" if is_done else "[ В ПРОЦЕССЕ ]"
                color = (50, 240, 120) if is_done else (150, 150, 180)

                y_pos = 115 + (idx * 65)
                card = pygame.Rect(70, y_pos - 8, WIDTH - 140, 55)
                pygame.draw.rect(temp_surface, (18, 25, 46), card, border_radius=10)
                pygame.draw.rect(temp_surface, (80, 200, 160) if is_done else (75, 85, 120), card, 1, border_radius=10)
                ach_text = font_small.render(f"✦  {ach['name']} — {ach['desc']}", True, TEXT_COLOR)
                status_text = font_tiny.render(status_str, True, color)
                temp_surface.blit(ach_text, (card.x + 16, y_pos))
                temp_surface.blit(status_text, (card.x + 16, y_pos + 23))

            t_back = font_small.render("Нажмите ESC для возврата в меню", True, GOLD_COLOR)
            temp_surface.blit(t_back, (WIDTH // 2 - t_back.get_width() // 2, HEIGHT - 50))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "REVIVE_PROMPT":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 230))
            temp_surface.blit(overlay, (0, 0))

            t1 = font_title.render("ВТОРАЯ ЖИЗНЬ?", True, GOLD_COLOR)
            t2 = font_small.render(f"У вас есть вторые жизни (в наличии: {game_data['lives_count']} шт.)", True,
                                   TEXT_COLOR)
            t3 = font_small.render("Нажмите [ Y ] — Использовать жизнь  |  [ L ] — Закончить игру", True,
                                   (180, 180, 210))

            temp_surface.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 50))
            temp_surface.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2))
            temp_surface.blit(t3, (WIDTH // 2 - t3.get_width() // 2, HEIGHT // 2 + 50))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        elif game_state == "GAME_OVER":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 230))
            temp_surface.blit(overlay, (0, 0))

            t1 = font_title.render("УПС, ВЫ ПРОИГРАЛИ!", True, FOOD_COLOR)
            t2 = font_small.render(f"Счет: {score} | Заработано монет: +{earned_coins_match}", True, GOLD_COLOR)
            t3 = font_small.render("Нажмите ПРОБЕЛ для возврата в меню", True, (160, 160, 190))

            temp_surface.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 50))
            temp_surface.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2))
            temp_surface.blit(t3, (WIDTH // 2 - t3.get_width() // 2, HEIGHT // 2 + 50))
            draw_dev_watermarks(temp_surface, show_side_author=True)

        screen.blit(temp_surface, (shake_x, shake_y))
        pygame.display.flip()
        clock.tick(20)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback

        traceback.print_exc()
        input("\nПроизошла ошибка! Нажмите Enter, чтобы закрыть окно...")
