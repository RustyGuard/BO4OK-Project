SERVER_EVENT_UPDATE = 25
SERVER_EVENT_SEC = 26
CLIENT_EVENT_UPDATE = 27
CLIENT_EVENT_SEC = 28
#
# EVENT_UPDATE = 25
# EVENT_SEC = 26

SERVER_EVENT_SYNC = 29

COLOR_LIST = [
    (0, 0, 0),  # 'black'
    (69, 220, 220),  # 'aqua'
    (0, 0, 255),  # 'blue'
    (0, 255, 0),  # 'green'
    (102, 255, 102),  # 'light_green'
    (255, 125, 0),  # 'orange'
    (255, 192, 203),  # 'pink'
    (160, 32, 240),  # 'purple'
    (255, 0, 0),  # 'red'
    (255, 255, 0),  # 'yellow'
    (195, 195, 195)  # server
]

CAMERA_MAX_SPEED = 30.0
CAMERA_MIN_SPEED = 2.0
CAMERA_STEP_FASTER = 0.1
CAMERA_STEP_SLOWER = 0.25
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

MONEY_PER_PUNCH = 5
WOOD_PER_PUNCH = 10

K_HP_DEFAULT = 1
K_HP_UP = 1.5
K_DAMAGE_DEFAULT = 1
K_DAMAGE_UP = 1.5
K_BUILDHP_DEFAULT = 1
K_BUILDHP_UP = 1.5
K_BUILDHP_UP2 = 2

WORLD_SIZE = 8000

MINIMAP_OFFSETX = 45
MINIMAP_OFFSETY = 835
MINIMAP_SIZEX = 250
MINIMAP_SIZEY = 245
MINIMAP_ICON_SIZE = 12

# Количество генерируемых деревьев
FORESTS_COUNT = 10
TREES_PER_FOREST = 30
TREES_RANGE = 300

BASE_MEAT = 10  # todo Баланс
MEAT_PER_FARM = 5  # todo Баланс
MAX_MEAT_VALUE = 500  # todo Баланс

CLIENT = 1
SERVER = 2

# Каждые десять секунд срабатывает шанс на восстановление n% хп шахты в случае если она ипчерпана
MINE_REGEN_CHANCE = 25  # (50%)
MINE_REGEN_MULT = 0.25  # (25% здоровья при срабатывании)

MONEY_FROM_START = 500.0  # todo Баланс
WOOD_FROM_START = 200.0  # todo Баланс
