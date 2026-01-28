"""
沙盒工具单元测试
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from geomind.config import get_settings
from geomind.tools.base import ToolStatus
from geomind.tools.registry import get_registry
from geomind.tools.sandbox import (
    BaseSandbox,
    CodeExecutionTool,
    DockerSandbox,
    E2BSandbox,
    LocalSandbox,
    SandboxError,
    SandboxResult,
    create_sandbox,
    execute_code,
)


class TestSandboxResult:
    """测试 SandboxResult"""

    def test_sandbox_result_success(self):
        """测试成功的沙盒结果"""
        result = SandboxResult(
            stdout="Hello, World!\n",
            stderr="",
            exit_code=0,
            execution_time=0.5,
        )
        assert result.success is True
        assert result.stdout == "Hello, World!\n"
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.error is None

    def test_sandbox_result_failure(self):
        """测试失败的沙盒结果"""
        result = SandboxResult(
            stdout="",
            stderr="Error occurred\n",
            exit_code=1,
            execution_time=0.3,
            error="Execution failed",
        )
        assert result.success is False
        assert result.exit_code == 1
        assert result.error == "Execution failed"

    def test_sandbox_result_to_dict(self):
        """测试转换为字典"""
        result = SandboxResult(
            stdout="output",
            stderr="error",
            exit_code=0,
            execution_time=1.0,
        )
        result_dict = result.to_dict()
        assert result_dict["stdout"] == "output"
        assert result_dict["stderr"] == "error"
        assert result_dict["exit_code"] == 0
        assert result_dict["execution_time"] == 1.0
        assert result_dict["success"] is True


class TestLocalSandbox:
    """测试 LocalSandbox"""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """测试初始化本地沙盒"""
        sandbox = LocalSandbox(timeout=30)
        await sandbox.initialize()
        assert sandbox._initialized is True
        assert sandbox.working_dir.exists()
        await sandbox.cleanup()

    @pytest.mark.asyncio
    async def test_execute_simple_code(self):
        """测试执行简单代码"""
        sandbox = LocalSandbox(timeout=30)
        await sandbox.initialize()

        code = "print('Hello, World!')"
        result = await sandbox.execute(code)

        assert result.success is True
        assert "Hello, World!" in result.stdout
        assert result.exit_code == 0

        await sandbox.cleanup()

    @pytest.mark.asyncio
    async def test_execute_code_with_error(self):
        """测试执行有错误的代码"""
        sandbox = LocalSandbox(timeout=30)
        await sandbox.initialize()

        code = "raise ValueError('Test error')"
        result = await sandbox.execute(code)

        assert result.success is False
        assert result.exit_code != 0
        assert "ValueError" in result.stderr or "Test error" in result.stderr

        await sandbox.cleanup()

    @pytest.mark.asyncio
    async def test_execute_code_timeout(self):
        """测试代码执行超时"""
        sandbox = LocalSandbox(timeout=1)
        await sandbox.initialize()

        code = "import time; time.sleep(10)"
        result = await sandbox.execute(code)

        assert result.success is False
        assert result.exit_code == 124  # Timeout exit code
        assert "timed out" in result.error.lower()

        await sandbox.cleanup()

    @pytest.mark.asyncio
    async def test_execute_unsupported_language(self):
        """测试执行不支持的语言"""
        sandbox = LocalSandbox(timeout=30)
        await sandbox.initialize()

        result = await sandbox.execute("console.log('test')", language="javascript")

        assert result.success is False
        assert "Unsupported language" in result.error

        await sandbox.cleanup()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试上下文管理器"""
        async with LocalSandbox(timeout=30) as sandbox:
            assert sandbox._initialized is True
            result = await sandbox.execute("print('test')")
            assert result.success is True

        # 上下文退出后应该已清理
        assert sandbox._initialized is False


class TestDockerSandbox:
    """测试 DockerSandbox"""

    @pytest.mark.asyncio
    async def test_initialize_docker_not_available(self):
        """测试 Docker 不可用时的初始化"""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # 模拟 Docker 不可用
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            sandbox = DockerSandbox(timeout=30)
            with pytest.raises(SandboxError, match="Docker is not available"):
                await sandbox.initialize()

    @pytest.mark.asyncio
    async def test_initialize_docker_not_installed(self):
        """测试 Docker 未安装时的初始化"""
        with patch(
            "asyncio.create_subprocess_exec", side_effect=FileNotFoundError()
        ) as mock_exec:
            sandbox = DockerSandbox(timeout=30)
            with pytest.raises(SandboxError, match="Docker is not installed"):
                await sandbox.initialize()

    @pytest.mark.asyncio
    async def test_execute_simple_code(self):
        """测试在 Docker 中执行简单代码"""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # 模拟初始化（docker --version 和 docker pull）
            init_process = AsyncMock()
            init_process.communicate = AsyncMock(return_value=(b"Docker version", b""))
            init_process.returncode = 0

            pull_process = AsyncMock()
            pull_process.communicate = AsyncMock(return_value=(b"", b""))
            pull_process.returncode = 0

            # 模拟代码执行
            exec_process = AsyncMock()
            exec_process.communicate = AsyncMock(
                return_value=(b"Hello, World!\n", b"")
            )
            exec_process.returncode = 0

            mock_exec.side_effect = [init_process, pull_process, exec_process]

            sandbox = DockerSandbox(timeout=30)
            await sandbox.initialize()

            code = "print('Hello, World!')"
            result = await sandbox.execute(code)

            assert result.success is True
            assert "Hello, World!" in result.stdout
            assert result.exit_code == 0

            await sandbox.cleanup()

    @pytest.mark.asyncio
    async def test_execute_code_timeout(self):
        """测试 Docker 代码执行超时"""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # 模拟初始化
            init_process = AsyncMock()
            init_process.communicate = AsyncMock(return_value=(b"Docker version", b""))
            init_process.returncode = 0

            pull_process = AsyncMock()
            pull_process.communicate = AsyncMock(return_value=(b"", b""))
            pull_process.returncode = 0

            # 模拟超时
            exec_process = AsyncMock()
            exec_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            exec_process.kill = AsyncMock()
            exec_process.wait = AsyncMock()

            mock_exec.side_effect = [init_process, pull_process, exec_process]

            sandbox = DockerSandbox(timeout=1)
            await sandbox.initialize()

            code = "import time; time.sleep(10)"
            result = await sandbox.execute(code)

            assert result.success is False
            assert result.exit_code == 124
            assert "timed out" in result.error.lower()

            await sandbox.cleanup()


class TestE2BSandbox:
    """测试 E2BSandbox"""

    @pytest.mark.asyncio
    async def test_initialize_without_sdk(self):
        """测试 E2B SDK 未安装时的初始化"""
        sandbox = E2BSandbox(api_key="test_key")
        sandbox._e2b = None  # 直接设置为 None 模拟 SDK 未安装
        with pytest.raises(SandboxError, match="E2B SDK not installed"):
            await sandbox.initialize()

    @pytest.mark.asyncio
    async def test_initialize_without_api_key(self):
        """测试没有 API key 时的初始化"""
        # Mock E2B SDK
        mock_e2b = MagicMock()
        sandbox = E2BSandbox(api_key=None)
        sandbox._e2b = mock_e2b
        with pytest.raises(SandboxError, match="E2B API key is required"):
            await sandbox.initialize()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="E2B SDK not installed - skipping E2B integration tests")
    async def test_execute_simple_code(self):
        """测试在 E2B 中执行简单代码"""
        pass

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="E2B SDK not installed - skipping E2B integration tests")
    async def test_execute_code_with_error(self):
        """测试在 E2B 中执行有错误的代码"""
        pass


class TestCreateSandbox:
    """测试沙盒工厂函数"""

    def test_create_local_sandbox(self):
        """测试创建本地沙盒"""
        sandbox = create_sandbox(provider="local", timeout=30)
        assert isinstance(sandbox, LocalSandbox)
        assert sandbox.timeout == 30

    def test_create_docker_sandbox(self):
        """测试创建 Docker 沙盒"""
        sandbox = create_sandbox(provider="docker", memory_limit=256)
        assert isinstance(sandbox, DockerSandbox)
        assert sandbox.memory_limit == 256

    def test_create_e2b_sandbox(self):
        """测试创建 E2B 沙盒"""
        sandbox = create_sandbox(provider="e2b", api_key="test_key")
        assert isinstance(sandbox, E2BSandbox)
        assert sandbox.api_key == "test_key"

    def test_create_sandbox_unsupported_provider(self):
        """测试创建不支持的沙盒提供商"""
        with pytest.raises(ValueError, match="Unsupported sandbox provider"):
            create_sandbox(provider="invalid")

    def test_create_sandbox_with_config(self):
        """测试使用配置创建沙盒"""
        settings = get_settings()
        sandbox = create_sandbox()
        # 默认应该是 LOCAL
        assert isinstance(sandbox, LocalSandbox)


class TestCodeExecutionTool:
    """测试代码执行工具"""

    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        tool = CodeExecutionTool()
        assert tool.name == "execute_code"
        assert tool.category == "沙盒"
        assert "代码执行" in tool.tags

    @pytest.mark.asyncio
    async def test_tool_execute_simple_code(self):
        """测试工具执行简单代码"""
        tool = CodeExecutionTool()

        result = await tool.execute(code="print('Hello from tool')")

        assert result.status == ToolStatus.SUCCESS
        assert "Hello from tool" in result.output["stdout"]
        assert result.output["success"] is True

        # 清理
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_tool_execute_code_with_timeout(self):
        """测试工具执行代码并自定义超时"""
        tool = CodeExecutionTool()

        # 使用较短的超时执行长时间运行的代码
        result = await tool.execute(code="import time; time.sleep(5)", timeout=1)

        assert result.status == ToolStatus.SUCCESS
        assert result.output["success"] is False
        assert result.output["exit_code"] == 124
        assert "timed out" in result.output["error"].lower()

        # 清理
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_tool_execute_code_error(self):
        """测试工具执行错误代码"""
        tool = CodeExecutionTool()

        result = await tool.execute(code="1 / 0")

        assert result.status == ToolStatus.SUCCESS
        assert result.output["success"] is False
        assert result.output["exit_code"] != 0

        # 清理
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_tool_registered(self):
        """测试工具是否已注册"""
        registry = get_registry()
        assert "execute_code" in registry


class TestExecuteCodeFunction:
    """测试 execute_code 便捷函数"""

    @pytest.mark.asyncio
    async def test_execute_code_success(self):
        """测试成功执行代码"""
        result = await execute_code("x = 10\nprint(x * 2)")

        assert result["success"] is True
        assert "20" in result["stdout"]
        assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_execute_code_failure(self):
        """测试执行失败的代码"""
        result = await execute_code("invalid python code !!!")
        # 语法错误的代码会返回失败结果
        assert result["success"] is False
        assert result["exit_code"] != 0

    @pytest.mark.asyncio
    async def test_execute_code_with_timeout(self):
        """测试执行代码并自定义超时"""
        result = await execute_code("import time; time.sleep(10)", timeout=1)
        # 超时的代码会返回失败结果
        assert result["success"] is False
        assert result["exit_code"] == 124


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

