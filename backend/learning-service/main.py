from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional, List
import json

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from shared.cors import add_cors_middleware
from shared.llm import llm_client
from shared.rag import rag_service
from shared.security import get_current_user

app = FastAPI(title="Learning Service", version="1.0.0")
add_cors_middleware(app)


# ==================== Schemas ====================

class CourseTutorRequest(BaseModel):
    topic: str
    level: str = "undergraduate"
    question: Optional[str] = None

class ExerciseRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    count: int = 5
    type: str = "choice"

class ExamPrepRequest(BaseModel):
    exam_type: str = "考研"
    subjects: List[str] = []
    focus_areas: List[str] = []

class MistakeAnalysisRequest(BaseModel):
    question: str
    student_answer: str
    correct_answer: Optional[str] = None


# ==================== Helper ====================

async def get_ai_response(system_prompt: str, user_prompt: str) -> str:
    """调用 LLM（自动选择可用模型）"""
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await llm_client.chat(messages, model_key="mimo-flash")
    except ValueError as e:
        return f"请先配置 API Key: {e}"
    except Exception as e:
        return f"AI 调用失败: {e}"


async def get_rag_context(query: str, top_k: int = 3) -> str:
    try:
        return await rag_service.get_context(query, top_k=top_k)
    except Exception:
        return ""


SYSTEM_PROMPT = "你是一位专业的机械工程教育专家，擅长教学、出题和考试辅导。请用专业但易懂的方式回答。"


# ==================== Endpoints ====================

@app.get("/health")
async def health():
    return {"status": "ok", "service": "learning-service"}


@app.post("/api/learning/tutor")
async def course_tutor(req: CourseTutorRequest, user=Depends(get_current_user)):
    context = await get_rag_context(req.topic + " " + (req.question or ""))
    level_map = {"undergraduate": "本科", "graduate": "研究生", "professional": "工程实践"}
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

    reply = await get_ai_response(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "topic": req.topic, "level": req.level}


@app.post("/api/learning/exercises")
async def generate_exercises(req: ExerciseRequest, user=Depends(get_current_user)):
    context = await get_rag_context(req.topic)
    type_map = {
        "choice": "选择题（含4个选项A/B/C/D，标注正确答案）",
        "fill": "填空题",
        "solve": "计算题（给出完整解题过程）",
        "essay": "论述题",
    }

    prompt = f"""请生成{req.count}道机械工程练习题。

【主题】{req.topic}
【难度】{req.difficulty}
【题型】{type_map.get(req.type, "选择题")}

要求：题目专业准确，每题给出答案和解析。
以 JSON 数组格式返回，每题包含: question, answer, explanation。
{"参考知识库：" + context if context else ""}
直接返回 JSON，不要额外文字。"""

    reply = await get_ai_response(SYSTEM_PROMPT, prompt)
    try:
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
async def exam_prep(req: ExamPrepRequest, user=Depends(get_current_user)):
    subjects_str = "、".join(req.subjects) if req.subjects else "机械原理、机械设计、材料力学"
    context = await get_rag_context(f"{req.exam_type} {subjects_str}")

    prompt = f"""请为{req.exam_type}提供复习指导。

【科目】{subjects_str}
{"【重点】" + "、".join(req.focus_areas) if req.focus_areas else ""}

请提供：各科核心考点 Top 5、常见题型、复习策略、易错点、推荐参考书。
{"参考知识库：" + context if context else ""}"""

    reply = await get_ai_response(SYSTEM_PROMPT, prompt)
    return {"reply": reply, "exam_type": req.exam_type, "subjects": req.subjects}


@app.post("/api/learning/mistake-analysis")
async def mistake_analysis(req: MistakeAnalysisRequest, user=Depends(get_current_user)):
    prompt = f"""学生做错了一道机械工程题，请分析。

【题目】{req.question}
【学生答案】{req.student_answer}
{"【正确答案】" + req.correct_answer if req.correct_answer else ""}

请分析：错误类型、正确思路、核心知识点、避免方法。"""

    reply = await get_ai_response(SYSTEM_PROMPT, prompt)
    return {"reply": reply}
