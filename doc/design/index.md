# 屋檐 系统设计总览

本文档描述屋檐项目的整体技术架构、技术栈选型以及前后端交互流程。

---

## 系统架构图

```mermaid
graph LR
    A[用户浏览器] -->|HTTP| B[前端应用]
    B -->|REST API| C[后端服务]
    C -->|读写| D[数据库]
    C -->|采集| E[国家统计局]
```

---

## 技术栈

| 层级 | 技术 | 用途 |
|---|---|---|
| 前端 | React 18 + TypeScript + Vite | 用户界面与交互 |
| 后端 | Python + FastAPI | 业务逻辑与接口服务 |
| 数据库 | SQLite + SQLAlchemy | 数据持久化与ORM |
| 采集 | Python requests | 数据采集（规划中） |
| 部署 | 待定 | 应用发布与托管 |

---

## 前后端交互流程

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户
    participant F as 前端
    participant API as 后端 API
    participant DB as 数据库

    U->>F: 发起操作
    F->>API: 发送请求（含参数）
    API->>DB: 查询/写入数据
    DB-->>API: 返回数据
    API-->>F: 返回响应
    F-->>U: 展示结果
```

---

## 核心设计决策

### 为什么用 FastAPI 而不是 Flask/Django？

- FastAPI 原生支持异步，性能更好
- 自动 API 文档生成（Swagger UI），便于前后端协作
- 内置数据验证（Pydantic），减少样板代码
- 当前阶段轻量够用，后续可扩展

### 为什么用 React + TypeScript？

- TypeScript 提供类型安全，减少运行时错误
- React 生态成熟，组件化开发效率高
- Vite 构建速度快，开发体验好

### 为什么用 SQLite？

- MVP 阶段数据量小，SQLite 足够使用
- 零配置，部署简单
- 后续可平滑迁移到 PostgreSQL/MySQL

---

## 模块划分

```mermaid
graph TD
    A[屋檐系统] --> B[前端应用]
    A --> C[后端服务]
    A --> D[数据采集]
    B --> B1[页面展示]
    B --> B2[图表组件]
    C --> C1[API接口]
    C --> C2[数据分析]
    C --> C3[数据库操作]
    D --> D1[国家统计局]
    D --> D2[数据清洗]
```

---

## 相关文档

- [数据模型](data-model.md)
- [API 接口说明](api-overview.md)
- [页面设计](pages/index.md)
- [决策记录](../decisions/index.md)
- [产品总览](../product/index.md)
