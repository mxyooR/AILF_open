"""
Scene Loader - 加载所有场景定义
从 Model/scene 目录加载所有业务场景和干扰场景
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

sys.path.append(str(Path(__file__).parent.parent.parent))

from Model.scene.medical import MEDICAL_SCENE
from Model.scene.finance import FINANCE_SCENE
from Model.scene.ecommerce import ECOMMERCE_SCENE
from Model.scene.train_ticket import TRAIN_TICKET_SCENE
from Model.scene.logistics import LOGISTICS_SCENE
from Model.scene.hrm import HRM_SCENE
from Model.scene.education import EDUCATION_SCENE
from Model.scene.catering import CATERING_SCENE
from Model.scene.hotel import HOTEL_SCENE
from Model.scene.banking import BANKING_SCENE
from Model.scene.government import GOVERNMENT_SCENE
from Model.scene.realestate import REALESTATE_SCENE
from Model.scene.noise import NOISE_SCENES
from Model.scene.common_options import COMMON_OPTIONS_APIS, FIELD_TO_OPTIONS_API


class SceneLoader:
    """场景加载器"""
    
    def __init__(self):
        self.core_scenes = {
            "medical": MEDICAL_SCENE,
            "finance": FINANCE_SCENE,
            "ecommerce": ECOMMERCE_SCENE,
            "train_ticket": TRAIN_TICKET_SCENE,
            "logistics": LOGISTICS_SCENE,
            "hrm": HRM_SCENE,
            "education": EDUCATION_SCENE,
            "catering": CATERING_SCENE,
            "hotel": HOTEL_SCENE,
            "banking": BANKING_SCENE,
            "government": GOVERNMENT_SCENE,
            "realestate": REALESTATE_SCENE
        }
        
        self.noise_scenes = NOISE_SCENES
        
        # 🔥 通用选项 API
        self.common_options_apis = COMMON_OPTIONS_APIS
        self.field_to_options_api = FIELD_TO_OPTIONS_API
        
    def get_all_apis(self, domain: str = None) -> List[Dict[str, Any]]:
        """获取所有API定义"""
        apis = []
        
        if domain and domain in self.core_scenes:
            apis.extend(self.core_scenes[domain]["apis"])
        elif not domain:
            for scene in self.core_scenes.values():
                apis.extend(scene["apis"])
                
        return apis
    
    def get_all_workflows(self, domain: str = None) -> List[Dict[str, Any]]:
        """获取所有工作流定义"""
        workflows = []
        
        if domain and domain in self.core_scenes:
            workflows.extend(self.core_scenes[domain]["workflows"])
        elif not domain:
            for scene in self.core_scenes.values():
                workflows.extend(scene["workflows"])
                
        return workflows
    
    def get_noise_apis(self) -> List[Dict[str, Any]]:
        """获取干扰域API"""
        noise_apis = []
        for domain, scene in self.noise_scenes.items():
            for api in scene["apis"]:
                api_copy = api.copy()
                api_copy["domain"] = domain
                noise_apis.append(api_copy)
        return noise_apis
    
    def get_domain_apis(self, domain: str) -> List[Dict[str, Any]]:
        """获取指定域的API"""
        if domain in self.core_scenes:
            return self.core_scenes[domain]["apis"]
        return []
    
    def get_domain_workflows(self, domain: str) -> List[Dict[str, Any]]:
        """获取指定域的工作流"""
        if domain in self.core_scenes:
            return self.core_scenes[domain]["workflows"]
        return []
    
    def get_all_domains(self) -> List[str]:
        """获取所有核心域名称"""
        return list(self.core_scenes.keys())
    
    def get_workflow_by_id(self, workflow_id: str) -> Dict[str, Any]:
        """根据ID获取工作流"""
        for scene in self.core_scenes.values():
            for wf in scene["workflows"]:
                if wf["id"] == workflow_id:
                    return wf
        return None
    
    def get_api_by_id(self, api_id: str) -> Dict[str, Any]:
        """根据ID获取API"""
        for scene in self.core_scenes.values():
            for api in scene["apis"]:
                if api["id"] == api_id:
                    return api
        # 🔥 也检查通用选项 API
        for api in self.common_options_apis:
            if api["id"] == api_id:
                return api
        return None
    
    def get_options_api_for_field(self, field_name: str) -> Dict[str, Any]:
        """🔥 根据字段名获取对应的选项 API"""
        return self.field_to_options_api.get(field_name)
    
    def get_all_options_apis(self) -> List[Dict[str, Any]]:
        """🔥 获取所有通用选项 API"""
        return self.common_options_apis
