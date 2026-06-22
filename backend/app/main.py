from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db.models import init_db, get_db

# 初始化数据库
init_db()

app = FastAPI(
    title="屋檐 - 城市住房数据分析平台",
    description="基于真实数据分析房屋相关信息，城市房价，宜居性等",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "欢迎来到屋檐 - 城市住房数据分析平台",
        "version": "1.0.0"
    }

# TODO: 添加业务路由

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
