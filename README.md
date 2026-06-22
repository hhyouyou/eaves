# 屋檐 - 城市住房数据分析平台

愿景：希望每个人都有自己的屋檐，庇护生活

## 项目结构

```
eaves/
├── backend/          # Python 后端
│   ├── app/          # FastAPI 应用入口
│   ├── data/         # 数据采集模块
│   ├── analysis/     # 数据分析模块
│   ├── db/           # 数据库模型
│   └── requirements.txt
├── frontend/         # React + TypeScript 前端
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── doc/              # 项目文档
```

## 技术栈

- **前端**: React 18 + TypeScript + Vite
- **后端**: Python + FastAPI + SQLAlchemy
- **数据库**: SQLite

## 启动方式

### 后端
```bash
cd backend
pip install -r requirements.txt
python app/main.py
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## 开发阶段

- 第一期：MVP 基础框架
- 第二期：多项数据综合分析
- 第三期：多维度数据源
- 第四期：全自动化流程
- 第五期：待定
