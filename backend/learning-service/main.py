from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from shared.security import get_current_user
from shared.rag import rag_service

app = FastAPI(title="Learning Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ==================== Schemas ====================

class CourseTutorRequest(BaseModel):
    topic: str
    level: str = "undergraduate"  # undergraduate / graduate / professional
    question: Optional[str] = None

class ExerciseRequest(BaseModel):
    topic: str
    difficulty: str = "medium"  # easy / medium / hard
    count: int = 5
    type: str = "choice"  # choice / fill / solve / essay

class ExamPrepRequest(BaseModel):
    exam_type: str = "考研"  # 考研 / 期末 / 注册工程师
    subjects: List[str] = []
    focus_areas: List[str] = []

class MistakeAnalysisRequest(BaseModel):
    question: str
    student_answer: str
    correct_answer: Optional[str] = None


# ==================== Helpers ====================

async def get_ai_response(prompt: str, model_key: str = "deepseek") -> str:
    """调用 LLM 获取回答"""
    import httpx

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
                    {"role": "system", "content": "你是一位专业的机械工程教育专家，擅长教学、出题和考试辅导。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def get_rag_context(query: str, top_k: int = 3) -> str:
    """从知识库检索相关上下文"""
    try:
        return await rag_service.get_context(query, top_k=top_k)
    except Exception:
        return ""


# ==================== Endpoints ====================

@app.get("/health")
async def health():
    return {"status": "ok", "service": "learning-service"}


@app.post("/api/learning/tutor")
async def course_tutor(req: CourseTutorRequest):
    """课程辅导 — 针对指定主题进行深入讲解"""
    context = await get_rag_context(req.topic + " " + (req.question or ""))

    level_map = {
        "undergraduate": "本科",
        "graduate": "研究生",
        "professional": "工程实践",
    }
    level_cn = level_map.get(req.level, "本科")

    prompt = f"""你正在为一位{level_cn}水平的学生进行机械工程课程辅导。

【学习主题】{req.topic}
{"【学生问题】" + req.question if req.question else "请对这个主题进行全面讲解。"}

要求：
1. 用通俗易懂的语言解释核心概念
2. 给出必要的公式和参数
3. 结合实际工程案例说明
4. 如果有标准规范请引用
{"5. 参考以下知识库内容：" + context if context else ""}"""

    reply = await get_ai_response(prompt)
    return {"reply": reply, "topic": req.topic, "level": req.level}


@app.post("/api/learning/exercises")
async def generate_exercises(req: ExerciseRequest):
    """习题生成 — 根据主题和难度生成练习题"""
    context = await get_rag_context(req.topic)

    type_map = {
        "choice": "选择题（含4个选项A/B/C/D，标注正确答案）",
        "fill": "填空题（留空让填写关键参数或概念）",
        "solve": "计算题（给出完整解题过程）",
        "essay": "论述题（需要展开分析的开放题）",
    }
    type_desc = type_map.get(req.type, "选择题")

    prompt = f"""请生成{req.count}道机械工程相关的练习题。

【主题】{req.topic}
【难度】{req.difficulty}
【题型】{type_desc}

要求：
1. 题目要专业、准确，符合工程实际
2. 每道题给出标准答案和详细解析
3. 难度适中，覆盖核心知识点
4. 以 JSON 数组格式返回，每题包含: question, options(选择题), answer, explanation
{"5. 参考知识库：" + context if context else ""}

直接返回 JSON，不要额外文字。"""

    reply = await get_ai_response(prompt)

    # 尝试解析 JSON
    try:
        # 处理可能的 markdown 代码块
        clean = reply.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
        exercises = json.loads(clean)
    except json.JSONDecodeError:
        exercises = [{"question": reply, "answer": "见解析", "explanation": ""}]

    return {"exercises": exercises, "topic": req.topic, "count": len(exercises)}


@app.post("/api/learning/exam-prep")
async def exam_prep(req: ExamPrepRequest):
    """考研/考试辅导 — 生成复习计划和重点"""
    subjects_str = "、".join(req.subjects) if req.subjects else "机械原理、机械设计、材料力学"
    focus_str = "、".join(req.focus_areas) if req.focus_areas else "全部重点"

    context = await get_rag_context(f"{req.exam_type} {subjects_str} 复习重点")

    prompt = f"""你是一位经验丰富的{req.exam_type}辅导老师。

【考试类型】{req.exam_type}
【考试科目】{subjects_str}
【重点关注】{focus_str}

请提供：
1. 各科目的核心考点梳理（列出 Top 5 高频考点）
2. 常见题型和分值分布
3. 高效复习策略和时间安排建议
4. 易错点和注意事项
5. 推荐参考资料

{"参考知识库内容：" + context if context else ""}"""

    reply = await get_ai_response(prompt)
    return {"reply": reply, "exam_type": req.exam_type, "subjects": req.subjects}


@app.post("/api/learning/mistake-analysis")
async def mistake_analysis(req: MistakeAnalysisRequest):
    """错题分析 — 分析学生做错的原因并给出指导"""
    prompt = f"""学生在机械工程学习中做错了一道题，请帮他分析。

【题目】{req.question}
【学生答案】{req.student_answer}
{"【正确答案】" + req.correct_answer if req.correct_answer else ""}

请分析：
1. 学生可能犯的错误类型（概念混淆/计算错误/理解偏差/知识盲区）
2. 正确的解题思路
3. 涉及的核心知识点
4. 如何避免类似错误的建议
5. 推荐的巩固练习方向"""

    reply = await get_ai_response(prompt)
    return {"reply": reply, "analysis_type": "mistake"}
