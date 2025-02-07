from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Optional, Dict
from enum import Enum

# Load environment variables
load_dotenv()

app = FastAPI(title="MindMirror API",
             description="AI-powered behavior analysis and relationship advice",
             version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize OpenAI client with DeepSeek configuration
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("DEEPSEEK_API_KEY environment variable is not set")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"  # 修正API地址
)

# Models
class RelationType(str, Enum):
    # 家庭关系
    FAMILY = "家人"
    PARTNER = "伴侣"
    
    # 社交关系
    FRIEND = "朋友"
    ACQUAINTANCE = "普通认识"
    
    # 职场关系
    SUPERIOR = "上司"
    PEER = "平级同事"
    SUBORDINATE = "下属"
    CLIENT = "客户"
    SUPPLIER = "上游供应商"
    
    # 社会关系
    PATRON = "贵人"
    BACKER = "靠山"
    DEPENDENT = "依附对象"
    POWER_FIGURE = "权势之人"
    OTHER = "其他"

def get_relation_groups() -> Dict[str, List[str]]:
    groups = {
        "家庭关系": [RelationType.FAMILY.value, RelationType.PARTNER.value],
        "社交关系": [RelationType.FRIEND.value, RelationType.ACQUAINTANCE.value],
        "职场关系": [RelationType.SUPERIOR.value, RelationType.PEER.value, 
                 RelationType.SUBORDINATE.value, RelationType.CLIENT.value, 
                 RelationType.SUPPLIER.value],
        "社会关系": [RelationType.PATRON.value, RelationType.BACKER.value,
                 RelationType.DEPENDENT.value, RelationType.POWER_FIGURE.value],
        "其他": [RelationType.OTHER.value]
    }
    return groups

class BehaviorInput(BaseModel):
    behavior_description: str
    context: Optional[str] = None
    relation_type: RelationType

class AnalysisResponse(BaseModel):
    motivation: str
    suggestions: List[str]
    psychological_insights: str
    reasoning_chain: Optional[str] = None

class FeedbackInput(BaseModel):
    analysis_id: str
    rating: int
    comment: Optional[str] = None

async def analyze_behavior(behavior: str, relation_type: RelationType, context: Optional[str] = None) -> dict:
    """
    Analyze behavior using DeepSeek-R1 API
    """
    if not behavior.strip():
        raise ValueError("行为描述不能为空")

    prompt = f"""作为一名心理行为分析师，请分析以下行为。请严格按照指定的JSON格式返回分析结果。

行为描述：{behavior}
关系类型：{relation_type.value}
{f'情境背景：{context}' if context else ''}

分析要求：
1. 基于{relation_type.value}关系的潜在动机分析
2. 针对{relation_type.value}关系的三个具体互动建议
3. 结合关系特点的心理洞察

请直接返回以下JSON格式，不要添加任何其他内容：
{{
    "motivation": "这里是对行为动机的分析",
    "suggestions": [
        "这里是第一个具体建议",
        "这里是第二个具体建议",
        "这里是第三个具体建议"
    ],
    "psychological_insights": "这里是心理洞察分析"
}}

注意：
1. 请确保返回的是合法的JSON格式
2. 不要添加任何额外的说明或标记
3. 使用简单的标点符号，避免使用特殊字符"""

    messages = [{"role": "user", "content": prompt}]
    
    try:
        print(f"Sending request to DeepSeek API...")
        print(f"Model: deepseek-reasoner")
        print(f"Messages: {messages}")
        
        # Create non-streaming response for better reliability
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=False  # 禁用流式响应以提高可靠性
        )
        
        print(f"API Response object: {response}")  # 打印完整响应对象
        
        if not response.choices:
            raise ValueError("API返回的响应中没有内容")
            
        # Get the response content
        content = response.choices[0].message.content
        if not content:
            raise ValueError("API返回的响应内容为空")
            
        print(f"Raw API response content: {content}")  # 添加调试日志
        
        # Parse the JSON response from content
        import json
        try:
            # 清理响应内容
            content = content.strip()
            
            # 尝试找到JSON内容的开始和结束
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx < 0 or end_idx <= start_idx:
                raise ValueError("无法在响应中找到有效的JSON内容")
                
            content = content[start_idx:end_idx]
            print(f"Extracted JSON content: {content}")  # 添加调试日志
            
            # 尝试解析JSON
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # 如果解析失败，尝试清理内容后重新解析
                content = ' '.join(content.split())  # 清理换行符和多余的空格
                content = content.replace('\\"', '"')  # 处理转义的引号
                print(f"Cleaned JSON content: {content}")  # 添加调试日志
                analysis = json.loads(content)
            
            # 验证响应格式
            required_fields = ['motivation', 'suggestions', 'psychological_insights']
            missing_fields = [field for field in required_fields if field not in analysis]
            if missing_fields:
                print(f"Missing fields in response: {missing_fields}")  # 添加调试日志
                raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")
            
            # 清理和验证字段内容
            def clean_text(text):
                if isinstance(text, str):
                    return ' '.join(text.split()).strip()
                return text

            # 清理所有文本字段
            analysis['motivation'] = clean_text(analysis.get('motivation', ''))
            analysis['psychological_insights'] = clean_text(analysis.get('psychological_insights', ''))
            
            # 处理建议列表
            suggestions = analysis.get('suggestions', [])
            if isinstance(suggestions, str):
                suggestions = [suggestions]
            elif not isinstance(suggestions, list):
                suggestions = []
                
            analysis['suggestions'] = [clean_text(s) for s in suggestions if s] or ['暂无具体建议']
            
            # 添加分析过程说明
            analysis['reasoning_chain'] = "基于提供的行为和情境完成分析"
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {str(e)}")
            print(f"原始内容: {content}")
            return {
                'motivation': '无法解析API响应',
                'suggestions': ['请重试', '如果问题持续存在请联系支持', '检查输入内容是否合适'],
                'psychological_insights': '分析失败',
                'reasoning_chain': f'JSON解析错误: {str(e)}'
            }
        except ValueError as e:
            print(f"验证错误: {str(e)}")
            return {
                'motivation': '响应格式不完整',
                'suggestions': ['请重试', '尝试提供更详细的行为描述', '确保输入内容清晰明确'],
                'psychological_insights': '无法完成分析',
                'reasoning_chain': str(e)
            }
    except Exception as e:
        print(f"API错误: {str(e)}")
        print(f"完整错误信息: {repr(e)}")  # 添加更详细的错误信息
        print(f"错误类型: {type(e)}")  # 打印错误类型
        return {
            'motivation': 'API调用失败',
            'suggestions': ['系统暂时无法处理您的请求', '请稍后重试', '如果问题持续存在请联系支持'],
            'psychological_insights': '无法完成分析',
            'reasoning_chain': f'错误信息: {str(e)}'
        }

@app.get("/")
async def root():
    """
    Serve the main HTML page
    """
    return FileResponse('app/static/index.html')

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_behavior_endpoint(input_data: BehaviorInput):
    """
    Endpoint to analyze behavior and provide insights
    """
    try:
        analysis = await analyze_behavior(input_data.behavior_description, input_data.relation_type, input_data.context)
        return AnalysisResponse(**analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackInput):
    """
    Endpoint to collect user feedback on analysis
    """
    # Here you would typically store the feedback in a database
    # For now, we'll just return a success message
    return {"message": "Feedback received successfully"} 