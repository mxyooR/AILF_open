# __init__.py - 场景定义聚合模块 V2
# 导入所有场景定义并提供统一的访问接口
# 所有场景已转换为新格式：不含 position/parent_nodes/child_nodes，关系通过 edges 表示

from .medical import MEDICAL_SCENE
from .ecommerce import ECOMMERCE_SCENE
from .train_ticket import TRAIN_TICKET_SCENE
from .logistics import LOGISTICS_SCENE
from .finance import FINANCE_SCENE
from .hrm import HRM_SCENE
from .education import EDUCATION_SCENE
from .banking import BANKING_SCENE
from .hotel import HOTEL_SCENE
from .catering import CATERING_SCENE
from .government import GOVERNMENT_SCENE
from .realestate import REALESTATE_SCENE
from .noise import NOISE_SCENES

DEFINITIONS = {
    "medical": MEDICAL_SCENE,
    "ecommerce": ECOMMERCE_SCENE,
    "train_ticket": TRAIN_TICKET_SCENE,
    "logistics": LOGISTICS_SCENE,
    "finance": FINANCE_SCENE,
    "hrm": HRM_SCENE,
    "education": EDUCATION_SCENE,
    "banking": BANKING_SCENE,
    "hotel": HOTEL_SCENE,
    "catering": CATERING_SCENE,
    "government": GOVERNMENT_SCENE,
    "realestate": REALESTATE_SCENE,
    "gaming": NOISE_SCENES["gaming"],
    "social": NOISE_SCENES["social"],
    "smarthome": NOISE_SCENES["smarthome"]
}

__all__ = [
    'DEFINITIONS',
    'MEDICAL_SCENE',
    'ECOMMERCE_SCENE',
    'TRAIN_TICKET_SCENE',
    'LOGISTICS_SCENE',
    'FINANCE_SCENE',
    'HRM_SCENE',
    'EDUCATION_SCENE',
    'BANKING_SCENE',
    'HOTEL_SCENE',
    'CATERING_SCENE',
    'GOVERNMENT_SCENE',
    'REALESTATE_SCENE',
    'NOISE_SCENES'
]
