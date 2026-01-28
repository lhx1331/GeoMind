# 贡献指南

感谢您对 GeoMind 项目的关注！我们欢迎各种形式的贡献。

## 开发环境设置

1. Fork 并克隆仓库
```bash
git clone https://github.com/your-username/GeoMind.git
cd GeoMind
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装开发依赖
```bash
pip install -e ".[dev]"
```

4. 安装 pre-commit hooks
```bash
pre-commit install
```

## 代码规范

### 代码风格

- 使用 **Black** 进行代码格式化
- 使用 **Ruff** 进行代码检查
- 遵循 **PEP 8** 规范

```bash
# 格式化代码
black geomind tests

# 检查代码
ruff check geomind tests

# 类型检查
mypy geomind
```

### 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```bash
git commit -m "feat: 添加自定义工具注册功能"
git commit -m "fix: 修复 GeoCLIP 模型加载问题"
```

## 开发流程

1. 从 `main` 分支创建新分支
```bash
git checkout -b feature/your-feature-name
```

2. 进行开发和测试
3. 确保所有测试通过
```bash
pytest
```

4. 提交代码（遵循提交规范）
5. 推送到您的 fork
```bash
git push origin feature/your-feature-name
```

6. 创建 Pull Request

## 测试

### 编写测试

- 单元测试放在 `tests/unit/`
- 集成测试放在 `tests/integration/`
- 使用 pytest fixtures 共享测试数据

### 运行测试

```bash
# 所有测试
pytest

# 特定测试文件
pytest tests/unit/test_agent.py

# 带覆盖率
pytest --cov=geomind --cov-report=html
```

## 文档

- 代码注释使用 Google 风格
- API 文档使用 docstring
- 更新相关文档（README、GUIDE 等）

## Pull Request 检查清单

- [ ] 代码遵循项目规范
- [ ] 所有测试通过
- [ ] 添加了新功能的测试
- [ ] 更新了相关文档
- [ ] 提交信息遵循规范
- [ ] 没有引入新的警告或错误

## 问题反馈

如果发现 bug 或有功能建议，请：

1. 检查是否已有相关 issue
2. 创建新的 issue，提供详细信息
3. 对于 bug，请包含复现步骤

感谢您的贡献！

