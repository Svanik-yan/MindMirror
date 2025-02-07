# MindMirror

MindMirror is an AI-powered behavior analysis tool that helps users understand the underlying motivations of people's actions. By analyzing behavioral patterns and context, it provides insights and communication suggestions to improve interpersonal relationships.

## Features

- 🧠 Behavior Analysis: Input descriptions of people's actions and get deep psychological insights
- 💡 AI-Powered Understanding: Leverages DeepSeek-R1 for advanced behavioral pattern recognition
- 🤝 Communication Tips: Receive personalized suggestions for better interaction
- ⭐ Feedback System: Rate AI analysis to help improve future responses

## Tech Stack

- FastAPI: Modern, fast web framework for building APIs
- DeepSeek-R1: Advanced language model for behavior analysis
- Vercel: Deployment platform
- React: Frontend framework
- TailwindCSS: Utility-first CSS framework

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mindmirror.git
cd mindmirror
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory and add:
```
DEEPSEEK_API_KEY=your_api_key
```

4. Run the development server:
```bash
uvicorn app.main:app --reload
```

## Deployment

The application is automatically deployed to Vercel through GitHub integration. Push to the main branch to trigger a deployment.

## Project Structure

```
mindmirror/
├── app/
│   ├── main.py           # FastAPI application
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic
│   └── api/             # API routes
├── frontend/            # React frontend
├── tests/              # Test files
├── requirements.txt    # Python dependencies
└── vercel.json        # Vercel configuration
```

## 📝 版本历史

- v1.0.0 (MVP) - 基础功能实现
  - 用户注册登录
  - 行为分析功能
  - 基础沟通建议
  - 用户反馈系统

## �� 许可证

MIT License 