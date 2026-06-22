# [项目名称] API 接口说明

本文档列出 [项目名称] 提供的 API 接口、调用方式及示例。

---

## 接口分组图

```mermaid
graph LR
    A[API 接口] --> B[内容接口]
    A --> C[搜索接口]
    A --> D[用户接口]
    B --> B1[GET /api/items]
    B --> B2[GET /api/items/:id]
    C --> C1[GET /api/search]
    D --> D1[POST /api/users/favorites]
```

---

## 接口详情

### 内容接口

| 方法 | 路径 | 说明 | 主要参数 |
|---|---|---|---|
| GET | `/api/items` | 获取内容列表 | `page`, `pageSize` |
| GET | `/api/items/:id` | 获取内容详情 | `id`（路径参数） |

### 搜索接口

| 方法 | 路径 | 说明 | 主要参数 |
|---|---|---|---|
| GET | `/api/search` | 关键词搜索 | `q`（关键词） |

### 用户接口

| 方法 | 路径 | 说明 | 主要参数 |
|---|---|---|---|
| POST | `/api/users/favorites` | 添加收藏 | `item_id` |

---

## 调用链路示例

### 场景一：浏览首页

```mermaid
sequenceDiagram
    participant F as 前端
    participant API as 后端 API
    participant DB as 数据库

    F->>API: GET /api/stats
    API->>DB: 查询统计数据
    DB-->>API: 返回统计结果
    API-->>F: { total: ..., categories: ... }
```

### 场景二：搜索内容

```mermaid
sequenceDiagram
    participant F as 前端
    participant API as 后端 API
    participant DB as 数据库

    F->>API: GET /api/search?q=关键词
    API->>DB: 执行搜索查询
    DB-->>API: 返回结果列表
    API-->>F: { items: [...] }
```

---

## 响应格式

### 成功响应示例

```json
{
  "code": 0,
  "data": {
    "items": [],
    "total": 0
  },
  "message": "success"
}
```

### 错误响应示例

```json
{
  "code": 1001,
  "data": null,
  "message": "参数错误"
}
```

---

## 相关文档

- [设计总览](index.md)
- [数据模型](data-model.md)
- [页面设计](pages/index.md)
