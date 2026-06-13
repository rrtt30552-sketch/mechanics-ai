from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import httpx

import sys
sys.path.insert(0, os.path.dirname(__file__))

app = FastAPI(title="Engineering Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ==================== Schemas ====================

class DesignAdviceRequest(BaseModel):
    description: str
    constraints: List[str] = []
    material_preference: Optional[str] = None

class SelectionRequest(BaseModel):
    component_type: str  # 轴承/齿轮/电机/联轴器/密封件...
    requirements: dict  # 载荷/转速/工况等
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
                "temperature": 0.5,
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


SYSTEM_PROMPT = """你是一位资深的机械工程师，拥有20年以上的工程设计和制造经验。
你的专长包括：机械设计、材料选型、加工工艺、质量控制、成本优化。
回答时请：
1. 给出具体的参数和数据（而非泛泛而谈）
2. 引用相关标准（GB/ISO/DIN/ASTM）
3. 考虑制造可行性和成本
4. 标注关键的安全系数和裕度"""


# ==================== Endpoints ====================

@app.get("/health")
async def health():
    return {"status": "ok", "service": "engineering-service"}


@app.post("/api/engineering/design-advice")
async def design_advice(req: DesignAdviceRequest):
    """设计建议 — 根据需求给出设计方案和注意事项"""
    constraints_str = "\n".join(f"  - {c}" for c in req.constraints) if req.constraints else "无特殊约束"

    prompt = f"""请对以下机械设计需求给出专业的设计建议：

【设计需求】{req.description}
【约束条件】
{constraints_str}
{"【材料偏好】" + req.material_preference if req.material_preference else ""}

请提供：
1. 推荐的设计方案（含结构描述）
2. 关键尺寸和公差建议
3. 材料选型建议（含牌号和热处理）
4. 加工工艺路线
5. 强度校核要点
6. 可能的设计风险和规避措施
7. 参考标准规范"""

    reply = await call_llm(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "type": "design_advice"}


@app.post("/api/engineering/selection")
async def component_selection(req: SelectionRequest):
    """选型计算 — 根据工况推荐零部件"""
    req_str = "\n".join(f"  - {k}: {v}" for k, v in req.requirements.items())

    prompt = f"""请为以下零部件进行工程选型：

【零部件类型】{req.component_type}
【工况要求】
{req_str}
{"【预算限制】" + req.budget if req.budget else ""}

请提供：
1. 选型计算过程（含公式和计算步骤）
2. 推荐的型号和规格（含品牌建议）
3. 安全系数校验
4. 安装和维护注意事项
5. 常见选型误区提醒"""

    reply = await call_llm(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "type": "selection", "component": req.component_type}


@app.post("/api/engineering/bom")
async def bom_analysis(req: BOMRequest):
    """BOM 分析 — 生成物料清单和成本估算"""
    prompt = f"""请为以下装配体生成 BOM（物料清单）：

【装配体描述】{req.assembly_description}
{chr(10).join(f"【{k}】{v}" for k, v in req.requirements.items()) if req.requirements else ""}

请以表格形式输出：
| 序号 | 零件名称 | 材料 | 规格/尺寸 | 数量 | 单价估算(元) | 备注 |

然后给出：
1. 总成本估算
2. 关键件和长周期件标注
3. 采购建议（国产/进口、替代方案）"""

    reply = await call_llm(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "type": "bom"}


@app.post("/api/engineering/dfma")
async def dfma_analysis(req: DFMARequest):
    """DFMA 分析 — 面向制造和装配的设计评审"""
    prompt = f"""请对以下零件/装配体进行 DFMA（面向制造和装配的设计）分析：

【零件描述】{req.component_description}
{"【制造工艺】" + req.manufacturing_process if req.manufacturing_process else ""}

请从以下角度分析：
1. 可制造性评估（工艺可行性、精度可达性）
2. 可装配性评估（装配顺序、定位基准）
3. 成本优化建议（减少工序、材料利用率）
4. 公差分析建议
5. 改进设计建议（简化结构、减少零件数）
6. 评分（1-10 分制）"""

    reply = await call_llm(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "type": "dfma"}


@app.post("/api/engineering/fmea")
async def fmea_analysis(req: FMEARequest):
    """FMEA 分析 — 失效模式与影响分析"""
    failure_str = "\n".join(f"  - {f}" for f in req.failure_modes) if req.failure_modes else "请自行识别潜在失效模式"

    prompt = f"""请对以下系统进行 FMEA（失效模式与影响分析）：

【系统描述】{req.system_description}
【已知失效模式】
{failure_str}

请以表格形式输出 FMEA 分析表：
| 失效模式 | 失效原因 | 失效影响 | 严重度(S) | 发生度(O) | 探测度(D) | RPN | 建议措施 |

其中 RPN = S × O × D（风险优先数）

然后给出：
1. RPN 排名前 5 的高风险项
2. 建议的优先改进措施
3. 需要重点监控的参数"""

    reply = await call_llm(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "type": "fmea"}
