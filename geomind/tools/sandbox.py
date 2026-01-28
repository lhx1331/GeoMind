"""
沙盒工具实现

提供安全的代码执行环境，支持多种后端（E2B、Docker、本地）。
"""

import asyncio
import io
import subprocess
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from geomind.config import get_settings
from geomind.tools.base import BaseTool, ToolParameter, ToolResult, ToolStatus
from geomind.tools.registry import register_tool
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


class SandboxError(Exception):
    """沙盒执行错误"""

    pass


class SandboxTimeoutError(SandboxError):
    """沙盒执行超时错误"""

    pass


class SandboxResult:
    """沙盒执行结果"""

    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
        execution_time: float = 0.0,
        error: Optional[str] = None,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.execution_time = execution_time
        self.error = error

    @property
    def success(self) -> bool:
        """执行是否成功"""
        return self.exit_code == 0 and self.error is None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "error": self.error,
            "success": self.success,
        }


class BaseSandbox(ABC):
    """沙盒基类"""

    def __init__(
        self,
        timeout: int = 60,
        memory_limit: int = 512,
        disable_network: bool = True,
    ):
        """
        初始化沙盒

        Args:
            timeout: 超时时间（秒）
            memory_limit: 内存限制（MB）
            disable_network: 是否禁用网络访问
        """
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.disable_network = disable_network
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """初始化沙盒环境"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理沙盒环境"""
        pass

    @abstractmethod
    async def execute(
        self, code: str, language: str = "python", **kwargs: Any
    ) -> SandboxResult:
        """
        执行代码

        Args:
            code: 要执行的代码
            language: 编程语言
            **kwargs: 其他参数

        Returns:
            SandboxResult: 执行结果
        """
        pass

    async def __aenter__(self):
        """上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        await self.cleanup()


class LocalSandbox(BaseSandbox):
    """
    本地沙盒实现

    使用子进程和资源限制实现基本的沙盒功能。
    注意：这不是一个完全安全的沙盒，仅用于开发和测试。
    """

    def __init__(
        self,
        timeout: int = 60,
        memory_limit: int = 512,
        disable_network: bool = True,
        working_dir: Optional[Path] = None,
    ):
        super().__init__(timeout, memory_limit, disable_network)
        settings = get_settings()
        self.working_dir = working_dir or settings.sandbox.local_working_dir
        self.working_dir = Path(self.working_dir)

    async def initialize(self) -> None:
        """初始化本地沙盒"""
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info(f"Local sandbox initialized at {self.working_dir}")

    async def cleanup(self) -> None:
        """清理本地沙盒"""
        # 可选：清理工作目录
        self._initialized = False
        logger.info("Local sandbox cleaned up")

    async def execute(
        self, code: str, language: str = "python", **kwargs: Any
    ) -> SandboxResult:
        """
        在本地执行代码

        Args:
            code: 要执行的代码
            language: 编程语言（目前仅支持 python）
            **kwargs: 其他参数

        Returns:
            SandboxResult: 执行结果
        """
        if language != "python":
            return SandboxResult(
                exit_code=1, error=f"Unsupported language: {language}"
            )

        start_time = time.time()
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        exit_code = 0
        error = None

        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                dir=self.working_dir,
                delete=False,
                encoding="utf-8",
            ) as f:
                f.write(code)
                temp_file = Path(f.name)

            try:
                # 使用子进程执行代码
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    str(temp_file),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.working_dir),
                )

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        process.communicate(), timeout=self.timeout
                    )
                    stdout_buffer.write(stdout_bytes.decode("utf-8", errors="replace"))
                    stderr_buffer.write(stderr_bytes.decode("utf-8", errors="replace"))
                    exit_code = process.returncode or 0
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    error = f"Execution timed out after {self.timeout} seconds"
                    exit_code = 124  # Timeout exit code
                    logger.warning(f"Code execution timeout: {self.timeout}s")
            finally:
                # 清理临时文件
                temp_file.unlink(missing_ok=True)

        except Exception as e:
            error = f"Execution error: {str(e)}"
            exit_code = 1
            logger.error(f"Local sandbox execution error: {e}", exc_info=True)

        execution_time = time.time() - start_time

        return SandboxResult(
            stdout=stdout_buffer.getvalue(),
            stderr=stderr_buffer.getvalue(),
            exit_code=exit_code,
            execution_time=execution_time,
            error=error,
        )


class DockerSandbox(BaseSandbox):
    """
    Docker 沙盒实现

    使用 Docker 容器提供隔离的执行环境。
    """

    def __init__(
        self,
        timeout: int = 60,
        memory_limit: int = 512,
        disable_network: bool = True,
        image: str = "python:3.10-slim",
        network_mode: str = "none",
    ):
        super().__init__(timeout, memory_limit, disable_network)
        settings = get_settings()
        self.image = image or settings.sandbox.docker_image
        self.network_mode = network_mode or settings.sandbox.docker_network_mode
        self._container_id: Optional[str] = None

    async def initialize(self) -> None:
        """初始化 Docker 沙盒"""
        # 检查 Docker 是否可用
        try:
            process = await asyncio.create_subprocess_exec(
                "docker",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            if process.returncode != 0:
                raise SandboxError("Docker is not available")
        except FileNotFoundError:
            raise SandboxError("Docker is not installed")

        # 拉取镜像（如果需要）
        logger.info(f"Checking Docker image: {self.image}")
        process = await asyncio.create_subprocess_exec(
            "docker",
            "pull",
            self.image,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()

        self._initialized = True
        logger.info(f"Docker sandbox initialized with image: {self.image}")

    async def cleanup(self) -> None:
        """清理 Docker 沙盒"""
        if self._container_id:
            try:
                # 停止并删除容器
                process = await asyncio.create_subprocess_exec(
                    "docker",
                    "rm",
                    "-f",
                    self._container_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()
                logger.info(f"Removed Docker container: {self._container_id}")
            except Exception as e:
                logger.warning(f"Failed to remove container {self._container_id}: {e}")
            finally:
                self._container_id = None

        self._initialized = False
        logger.info("Docker sandbox cleaned up")

    async def execute(
        self, code: str, language: str = "python", **kwargs: Any
    ) -> SandboxResult:
        """
        在 Docker 容器中执行代码

        Args:
            code: 要执行的代码
            language: 编程语言（目前仅支持 python）
            **kwargs: 其他参数

        Returns:
            SandboxResult: 执行结果
        """
        if language != "python":
            return SandboxResult(
                exit_code=1, error=f"Unsupported language: {language}"
            )

        start_time = time.time()
        exit_code = 0
        error = None
        stdout = ""
        stderr = ""

        try:
            # 准备 Docker 运行参数
            docker_args = [
                "docker",
                "run",
                "--rm",  # 自动删除容器
                "-i",  # 交互模式
                f"--memory={self.memory_limit}m",  # 内存限制
                f"--network={self.network_mode}",  # 网络模式
                "--cpus=1",  # CPU 限制
                self.image,
                "python",
                "-c",
                code,
            ]

            # 执行 Docker 容器
            process = await asyncio.create_subprocess_exec(
                *docker_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=self.timeout
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                exit_code = process.returncode or 0
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                error = f"Execution timed out after {self.timeout} seconds"
                exit_code = 124
                logger.warning(f"Docker execution timeout: {self.timeout}s")

        except Exception as e:
            error = f"Docker execution error: {str(e)}"
            exit_code = 1
            logger.error(f"Docker sandbox execution error: {e}", exc_info=True)

        execution_time = time.time() - start_time

        return SandboxResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time=execution_time,
            error=error,
        )


class E2BSandbox(BaseSandbox):
    """
    E2B 沙盒实现

    使用 E2B (https://e2b.dev) 提供的云端沙盒环境。
    """

    def __init__(
        self,
        timeout: int = 60,
        memory_limit: int = 512,
        disable_network: bool = True,
        api_key: Optional[str] = None,
        template: str = "Python3",
    ):
        super().__init__(timeout, memory_limit, disable_network)
        settings = get_settings()
        self.api_key = api_key or settings.sandbox.e2b_api_key
        self.template = template or settings.sandbox.e2b_template
        self._session = None

        # 检查 E2B SDK 是否安装
        try:
            import e2b

            self._e2b = e2b
        except ImportError:
            logger.warning(
                "E2B SDK not installed. Install with: pip install e2b e2b-code-interpreter"
            )
            self._e2b = None

    async def initialize(self) -> None:
        """初始化 E2B 沙盒"""
        if not self._e2b:
            raise SandboxError(
                "E2B SDK not installed. Install with: pip install e2b e2b-code-interpreter"
            )

        if not self.api_key:
            raise SandboxError("E2B API key is required")

        try:
            # 创建 E2B 会话
            from e2b_code_interpreter import CodeInterpreter

            self._session = CodeInterpreter(api_key=self.api_key)
            self._initialized = True
            logger.info(f"E2B sandbox initialized with template: {self.template}")
        except Exception as e:
            raise SandboxError(f"Failed to initialize E2B sandbox: {e}")

    async def cleanup(self) -> None:
        """清理 E2B 沙盒"""
        if self._session:
            try:
                self._session.close()
                logger.info("E2B sandbox session closed")
            except Exception as e:
                logger.warning(f"Failed to close E2B session: {e}")
            finally:
                self._session = None

        self._initialized = False
        logger.info("E2B sandbox cleaned up")

    async def execute(
        self, code: str, language: str = "python", **kwargs: Any
    ) -> SandboxResult:
        """
        在 E2B 沙盒中执行代码

        Args:
            code: 要执行的代码
            language: 编程语言（目前仅支持 python）
            **kwargs: 其他参数

        Returns:
            SandboxResult: 执行结果
        """
        if language != "python":
            return SandboxResult(
                exit_code=1, error=f"Unsupported language: {language}"
            )

        if not self._session:
            return SandboxResult(exit_code=1, error="E2B session not initialized")

        start_time = time.time()
        exit_code = 0
        error = None
        stdout = ""
        stderr = ""

        try:
            # 执行代码
            result = await asyncio.wait_for(
                asyncio.to_thread(self._session.notebook.exec_cell, code),
                timeout=self.timeout,
            )

            # 提取结果
            if result.error:
                error = str(result.error)
                stderr = error
                exit_code = 1
            else:
                stdout = "\n".join([str(output) for output in result.results])
                if result.logs:
                    stderr = "\n".join([str(log) for log in result.logs.stderr])
                    stdout_logs = "\n".join([str(log) for log in result.logs.stdout])
                    if stdout_logs:
                        stdout = f"{stdout_logs}\n{stdout}" if stdout else stdout_logs

        except asyncio.TimeoutError:
            error = f"Execution timed out after {self.timeout} seconds"
            exit_code = 124
            logger.warning(f"E2B execution timeout: {self.timeout}s")
        except Exception as e:
            error = f"E2B execution error: {str(e)}"
            exit_code = 1
            logger.error(f"E2B sandbox execution error: {e}", exc_info=True)

        execution_time = time.time() - start_time

        return SandboxResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time=execution_time,
            error=error,
        )


def create_sandbox(
    provider: Optional[str] = None,
    timeout: Optional[int] = None,
    memory_limit: Optional[int] = None,
    disable_network: Optional[bool] = None,
    **kwargs: Any,
) -> BaseSandbox:
    """
    创建沙盒实例的工厂函数

    Args:
        provider: 沙盒提供商 (e2b, docker, local)
        timeout: 超时时间（秒）
        memory_limit: 内存限制（MB）
        disable_network: 是否禁用网络访问
        **kwargs: 其他参数

    Returns:
        BaseSandbox: 沙盒实例
    """
    settings = get_settings()
    provider = provider or settings.sandbox.provider.value
    timeout = timeout or settings.sandbox.timeout
    memory_limit = memory_limit or settings.sandbox.memory_limit
    disable_network = (
        disable_network
        if disable_network is not None
        else settings.sandbox.disable_network
    )

    if provider == "e2b":
        return E2BSandbox(
            timeout=timeout,
            memory_limit=memory_limit,
            disable_network=disable_network,
            api_key=kwargs.get("api_key"),
            template=kwargs.get("template", settings.sandbox.e2b_template),
        )
    elif provider == "docker":
        return DockerSandbox(
            timeout=timeout,
            memory_limit=memory_limit,
            disable_network=disable_network,
            image=kwargs.get("image", settings.sandbox.docker_image),
            network_mode=kwargs.get(
                "network_mode", settings.sandbox.docker_network_mode
            ),
        )
    elif provider == "local":
        return LocalSandbox(
            timeout=timeout,
            memory_limit=memory_limit,
            disable_network=disable_network,
            working_dir=kwargs.get("working_dir", settings.sandbox.local_working_dir),
        )
    else:
        raise ValueError(f"Unsupported sandbox provider: {provider}")


@register_tool(
    name="execute_code",
    category="沙盒",
    tags=["代码执行", "沙盒", "安全"],
)
class CodeExecutionTool(BaseTool):
    """代码执行工具"""

    def __init__(self):
        super().__init__()
        self._sandbox: Optional[BaseSandbox] = None

    @property
    def name(self) -> str:
        """工具名称"""
        return "execute_code"

    @property
    def description(self) -> str:
        """工具描述"""
        return "在安全的沙盒环境中执行 Python 代码"

    @property
    def category(self) -> Optional[str]:
        """工具分类"""
        return "沙盒"

    @property
    def tags(self) -> List[str]:
        """工具标签"""
        return ["代码执行", "沙盒", "安全"]

    async def _get_sandbox(self) -> BaseSandbox:
        """获取或创建沙盒实例"""
        if self._sandbox is None or not self._sandbox._initialized:
            self._sandbox = create_sandbox()
            await self._sandbox.initialize()
        return self._sandbox

    async def execute(self, code: str, timeout: Optional[int] = None, **kwargs: Any) -> ToolResult:
        """
        执行代码

        Args:
            code: 要执行的 Python 代码
            timeout: 超时时间（秒）
            **kwargs: 其他参数

        Returns:
            ToolResult: 工具执行结果
        """
        try:
            logger.info(f"Executing code in sandbox (timeout={timeout})")

            # 获取沙盒
            sandbox = await self._get_sandbox()

            # 如果指定了超时，临时修改沙盒超时设置
            original_timeout = sandbox.timeout
            if timeout is not None:
                sandbox.timeout = timeout

            try:
                # 执行代码
                result = await sandbox.execute(code, language="python")

                # 记录结果
                if result.success:
                    logger.info(
                        f"Code execution successful (time={result.execution_time:.2f}s)"
                    )
                else:
                    logger.warning(
                        f"Code execution failed with exit code {result.exit_code}"
                    )

                return ToolResult.success(
                    output=result.to_dict(),
                    metadata={"tool": self.name}
                )

            finally:
                # 恢复原始超时设置
                if timeout is not None:
                    sandbox.timeout = original_timeout

        except Exception as e:
            logger.error(f"Code execution error: {e}", exc_info=True)
            return ToolResult.error(
                error=str(e),
                metadata={"tool": self.name}
            )

    async def cleanup(self) -> None:
        """清理沙盒资源"""
        if self._sandbox:
            await self._sandbox.cleanup()
            self._sandbox = None


# 创建全局工具实例
_code_execution_tool = CodeExecutionTool()


async def execute_code(code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    便捷函数：在沙盒中执行代码

    Args:
        code: 要执行的 Python 代码
        timeout: 超时时间（秒）

    Returns:
        执行结果字典
    """
    result = await _code_execution_tool.execute(code=code, timeout=timeout)
    if result.status == ToolStatus.SUCCESS:
        return result.output
    else:
        raise SandboxError(result.error_message or "Code execution failed")

