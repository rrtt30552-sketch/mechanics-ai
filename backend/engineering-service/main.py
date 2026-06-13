from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from shared.llm import llm_client

app = FastAPI(title="Engineering Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SYSTEM_PROMPT = """你是一位资深机械工程师，拥有20年以上工程设计经验。
回答时请给出具体参数和数据，引用相关标准(GB/ISO/DIN)，考虑制造可行性和成本。"""


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


class DesignAdviceRequest(BaseModel):
    description: str
    constraints: List[str] = []
    material_preference: Optional[str] = None

class SelectionRequest(BaseModel):
    component_type: str
    requirements: dict
    budget: Optional[str] = None

class BOMRequest(BaseModel):
    assembly_description: str
    requirements: dict = {}

class DFMARequest(BaseModel):
    component_description: str
    manufacturing_process: Optional[str] = None

class FMEARequest(BaseModel):
    system_description: str
    failure_modes: List[str] = []


@app.get("/health")
async def health():
    return {"status": "ok", "service": "engineering-service"}


@app.post("/api/engineering/design-advice")
async def design_advice(req: DesignAdviceRequest):
    constraints = "\n".join(f"  - {c}" for c in req.constraints) if req.constraints else "无"
    prompt = f"""请对以下设计需求给出专业建议：

【需求】{req.description}
【约束】{constraints}
{"【材料偏好】" + req.material_preference if req.material_preference else ""}

请给出：设计方案、关键尺寸公差、材料选型(含牌号)、加工工艺、强度校核要点、风险规避、参考标准。"""
    return {"reply": await call_llm(prompt), "type": "design_advice"}


@app.post("/api/engineering/selection")
async def component_selection(req: SelectionRequest):
    reqs = "\n".join(f"  - {k}: {v}" for k, v in req.requirements.items())
    prompt = f"""请为以下零部件选型：

【类型】{req.component_type}
【工况】
{reqs}

请给出：选型计算过程、推荐型号规格、安全系数、安装注意事项。"""
    return {"reply": await call_llm(prompt), "type": "selection", "component": req.component_type}


@app.post("/api/engineering/bom")
async def bom_analysis(req: BOMRequest):
    prompt = f"""请为以下装配体生成 BOM 物料清单：

【描述】{req.assembly_description}

以表格输出：序号|零件名|材料|规格|数量|单价估算|备注，再给总成本和采购建议。"""
    return {"reply": await call_llm(prompt), "type": "bom"}


@app.post("/api/engineering/dfma")
async def dfma_analysis(req: DFMARequest):
    prompt = f"""请对以下零件进行 DFMA 分析：

【描述】{req.component_description}
{"【工艺】" + req.manufacturing_process if req.manufacturing_process else ""}

从可制造性、可装配性、成本优化、公差分析、改进建议、评分(1-10) 六个方面分析。"""
    return {"reply": await call_llm(prompt), "type": "dfma"}


@app.post("/api/engineering/fmea")
async def fmea_analysis(req: FMEARequest):
    prompt = f"""请对以下系统进行 FMEA 分析：

【系统】{req.system_description}

以表格输出：失效模式|原因|影响|严重度(S)|发生度(O)|探测度(D)|RPN|措施。
列出 RPN 前 5 的高风险项和改进措施。"""
    return {"reply": await call_llm(prompt), "type": "fmea"}
