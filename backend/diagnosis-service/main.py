from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import httpx

import sys
sys.path.insert(0, os.path.dirname(__file__))

app = FastAPI(title="Diagnosis Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ==================== Schemas ====================

class FaultDiagnosisRequest(BaseModel):
    equipment: str  # 设备类型
    symptoms: List[str]  # 故障现象列表
    operating_conditions: Optional[dict] = None  # 运行工况
    history: Optional[str] = None  # 历史维修记录

class VibrationAnalysisRequest(BaseModel):
    equipment: str
    vibration_data: Optional[str] = None  # 振动数据描述
    frequency_info: Optional[str] = None  # 频率特征
    measurement_point: Optional[str] = None  # 测点位置

class WearAnalysisRequest(BaseModel):
    component: str  # 磨损零件
    wear_type: str  # 磨损类型：磨粒/粘着/疲劳/腐蚀/微动
    severity: str = "moderate"  # 程度：light/moderate/severe
    operating_env: Optional[str] = None  # 工作环境

class MaintenancePlanRequest(BaseModel):
    equipment: str
    equipment_age: Optional[str] = None
    criticality: str = "medium"  # low/medium/high/critical
    current_issues: List[str] = []


# ==================== Helper ====================

async def call_llm(system_prompt: str, user_prompt: str) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    if not api_key:
        return "请先配置 DEEPSEEK_API_KEY 环境变量"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.4,
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


SYSTEM_PROMPT = """你是一位高级设备诊断工程师，精通机械故障诊断、振动分析、磨损机理和预防性维护。
你有丰富的现场经验，能从有限的信息中推断出最可能的故障原因。
回答时请：
1. 按可能性从高到低排列故障原因
2. 给出具体的检查方法和验证步骤
3. 提供量化判断标准（振动值、温度、间隙等）
4. 给出维修/更换建议和预防措施
5. 注意安全事项"""


# ==================== Endpoints ====================

@app.get("/health")
async def health():
    return {"status": "ok", "service": "diagnosis-service"}


@app.post("/api/diagnosis/fault")
async def fault_diagnosis(req: FaultDiagnosisRequest):
    """故障诊断 — 综合分析故障原因"""
    symptoms_str = "\n".join(f"  - {s}" for s in req.symptoms)
    cond_str = "\n".join(f"  - {k}: {v}" for k, v in req.operating_conditions.items()) if req.operating_conditions else "未提供"

    prompt = f"""请对以下设备故障进行诊断分析：

【设备类型】{req.equipment}
【故障现象】
{symptoms_str}
【运行工况】
{cond_str}
{"【历史维修记录】" + req.history if req.history else ""}

请提供：
1. 最可能的故障原因（按概率排序，Top 5）
2. 每个原因的判断依据
3. 排查步骤（从简单到复杂）
4. 需要的检测工具和方法
5. 临时应急措施
6. 彻底修复方案
7. 预防措施建议"""

    reply = await call_llm(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "type": "fault_diagnosis", "equipment": req.equipment}


@app.post("/api/diagnosis/vibration")
async def vibration_analysis(req: VibrationAnalysisRequest):
    """振动分析 — 基于振动特征判断故障"""
    prompt = f"""请对以下设备进行振动分析：

【设备类型】{req.equipment}
{"【振动数据描述】" + req.vibration_data if req.vibration_data else ""}
{"【频率特征】" + req.frequency_info if req.frequency_info else ""}
{"【测点位置】" + req.measurement_point if req.measurement_point else ""}

请提供：
1. 振动特征解读（频率与故障类型的对应关系）
2. 常见的振动故障模式：
   - 不平衡 (1X 频率)
   - 不对中 (2X 频率)
   - 机械松动 (多倍频)
   - 轴承故障 (BPFO/BSF/FTF)
   - 齿轮啮合 (GMF)
3. 判断标准（ISO 10816 振动等级）
4. 建议的测量方案
5. 处理措施"""

    reply = await call_llm(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "type": "vibration_analysis"}


@app.post("/api/diagnosis/wear")
async def wear_analysis(req: WearAnalysisRequest):
    """磨损分析 — 分析磨损原因和对策"""
    prompt = f"""请对以下零件磨损进行分析：

【磨损零件】{req.component}
【磨损类型】{req.wear_type}
【严重程度】{req.severity}
{"【工作环境】" + req.operating_env if req.operating_env else ""}

请提供：
1. 该磨损类型的机理说明
2. 可能的加速因素
3. 磨损阶段判断（初期/发展期/严重期）
4. 残余寿命估算方法
5. 改善措施：
   - 材料升级建议
   - 表面处理方案
   - 润滑优化
   - 工况调整
6. 监控建议（油液分析/振动/温度）"""

    reply = await call_llm(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "type": "wear_analysis"}


@app.post("/api/diagnosis/maintenance-plan")
async def maintenance_plan(req: MaintenancePlanRequest):
    """维护计划 — 生成预防性维护方案"""
    issues_str = "\n".join(f"  - {i}" for i in req.current_issues) if req.current_issues else "无已知问题"

    prompt = f"""请为以下设备制定维护计划：

【设备类型】{req.equipment}
{"【设备年龄】" + req.equipment_age if req.equipment_age else ""}
【重要程度】{req.criticality}
【当前问题】
{issues_str}

请提供：
1. 维护策略建议（预防性/预测性/以可靠性为中心）
2. 日常巡检清单（日检/周检/月检）
3. 定期保养项目和周期
4. 关键备件清单和建议库存
5. 状态监测指标和阈值
6. 大修/翻新建议周期
7. 维护成本估算框架"""

    reply = await call_llm(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "type": "maintenance_plan"}
