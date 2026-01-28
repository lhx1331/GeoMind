"""提示模板管理"""

from geomind.prompts.base import (
    PromptTemplate,
    PromptTemplateLoader,
    get_loader,
    load_template,
    render_template,
)

__all__ = [
    "PromptTemplate",
    "PromptTemplateLoader",
    "get_loader",
    "load_template",
    "render_template",
]

# 将在后续任务中实现
# from geomind.prompts.perception import PerceptionPrompt
# from geomind.prompts.hypothesis import HypothesisPrompt
# from geomind.prompts.verification import VerificationPrompt

