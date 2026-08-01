# Take-Home Assignment Session Summary

## 项目
US Census Data Assistant - 自然语言查询 Census 数据的 AI 聊天助手

## 技术栈
- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: Snowflake (Census Marketplace data)
- **LLM**: Claude Opus 4.5 (Anthropic API)

## 架构
Guardrails → Topic Router → SQL Generator → Snowflake → Answer Generator → Streaming Response

## 主要挑战 & 解决
1. **Snowflake MFA 问题** → 改用 key-pair 认证
2. **Snowflake 大小写敏感** → 所有 identifiers 加双引号
3. **模糊查询** → 加了 clarification prompts
4. **Streamlit Cloud secrets** → TOML 格式 + 一行行复制

## 关键文件
- `app.py` - Streamlit UI
- `agent/core.py` - Pipeline 编排
- `agent/guardrails.py` - 过滤 off-topic
- `agent/sql_generator.py` - Text-to-SQL
- `db/connector.py` - Snowflake 连接 (key-pair auth)
- `db/schema.py` - Census 表 metadata

## 技术决策
1. Streamlit vs FastAPI+React → 快速开发
2. Text-to-SQL vs RAG → 结构化数据更适合 SQL
3. Keyword routing vs LLM routing → 快速、可预测
4. Static schema vs dynamic discovery → 速度优先

## 测试
- 50 个 unit/integration tests
- Mock-heavy 策略，无需真实 API 调用

## AI 工具使用
- Claude Code 全程辅助
- 架构设计、调试、代码生成、测试、文档

## 最终交付
- GitHub: https://github.com/valerie1122/snowflake-census-agent
- Demo: https://app-census-agent-2xw8tvr4lzc2ndukfkvp9d.streamlit.app
