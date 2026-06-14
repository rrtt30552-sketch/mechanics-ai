from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from shared.cors import add_cors_middleware
from shared.llm import llm_client

app = FastAPI(title="Diagnosis Service", version="1.0.0")
add_cors_middleware(app)

SYSTEM_PROMPT = """你是一位高级设备诊断工程师，精通机械故障诊断、振动分析、磨损机理和预防性维护。
回答时按可能性排序，给出具体检查方法和量化判断标准。"""


async def call_llm(user_prompt: str) -> str:
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        return await llm_client.chat(messages, model_key="mimo")
    except ValueError as e:
        return f"请先配置 API Key: {e}"
    except Exception as e:
        return f"AI 调用失败: {e}"


class FaultDiagnosisRequest(BaseModel):
    equipment: str
    symptoms: List[str]
    operating_conditions: Optional[dict] = None
    history: Optional[str] = None

class VibrationAnalysisRequest(BaseModel):
    equipment: str
    vibration_data: Optional[str] = None
    frequency_info: Optional[str] = None

class WearAnalysisRequest(BaseModel):
    component: str
    wear_type: str
    severity: str = "moderate"
    operating_env: Optional[str] = None

class MaintenancePlanRequest(BaseModel):
    equipment: str
    equipment_age: Optional[str] = None
    criticality: str = "medium"
    current_issues: List[str] = []


@app.get("/health")
async def health():
    return {"status": "ok", "service": "diagnosis-service"}


@app.post("/api/diagnosis/fault")
async def fault_diagnosis(req: FaultDiagnosisRequest):
    symptoms = "\n".join(f"  - {s}" for s in req.symptoms)
    conds = "\n".join(f"  - {k}: {v}" for k, v in req.operating_conditions.items()) if req.operating_conditions else "未提供"
    prompt = f"""请诊断以下设备故障：

【设备】{req.equipment}
【现象】
{symptoms}
【工况】
{conds}
{"【历史】" + req.history if req.history else ""}

请给出：最可能原因 Top 5（含判断依据）、排查步骤、检测工具、应急措施、修复方案、预防措施。"""
    return {"reply": await call_llm(prompt), "type": "fault_diagnosis"}


@app.post("/api/diagnosis/vibration")
async def vibration_analysis(req: VibrationAnalysisRequest):
    prompt = f"""请对以下设备进行振动分析：

【设备】{req.equipment}
{"【振动数据】" + req.vibration_data if req.vibration_data else ""}
{"【频率特征】" + req.frequency_info if req.frequency_info else ""}

请给出：频率与故障对应关系、常见故障模式(不平衡/不对中/松动/轴承/齿轮)、ISO 10816 判断标准、处理措施。"""
    return {"reply": await call_llm(prompt), "type": "vibration_analysis"}


@app.post("/api/diagnosis/wear")
async def wear_analysis(req: WearAnalysisRequest):
    prompt = f"""请分析以下磨损问题：

【零件】{req.component}
【类型】{req.wear_type}
【程度】{req.severity}
{"【环境】" + req.operating_env if req.operating_env else ""}

请给出：磨损机理、加速因素、阶段判断、残余寿命估算、改善措施(材料/表面处理/润滑)、监控建议。"""
    return {"reply": await call_llm(prompt), "type": "wear_analysis"}


@app.post("/api/diagnosis/maintenance-plan")
async def maintenance_plan(req: MaintenancePlanRequest):
    issues = "\n".join(f"  - {i}" for i in req.current_issues) if req.current_issues else "无"
    prompt = f"""请为以下设备制定维护计划：

【设备】{req.equipment}
{"【年龄】" + req.equipment_age if req.equipment_age else ""}
【重要度】{req.criticality}
【当前问题】
{issues}

请给出：维护策略、日/周/月巡检清单、定期保养项目、备件清单、状态监测指标、大修周期、成本估算。"""
    return {"reply": await call_llm(prompt), "type": "maintenance_plan"}
