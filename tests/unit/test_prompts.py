"""
提示模板单元测试
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from geomind.prompts.base import (
    PromptTemplate,
    PromptTemplateLoader,
    get_loader,
    load_template,
    render_template,
)


class TestPromptTemplate:
    """测试 PromptTemplate"""

    def test_create_template(self):
        """测试创建模板"""
        template = PromptTemplate(
            name="test",
            version="1.0.0",
            description="Test template",
            template="Hello, $name!",
            variables=["name"],
        )

        assert template.name == "test"
        assert template.version == "1.0.0"
        assert template.template == "Hello, $name!"
        assert "name" in template.variables

    def test_render_template(self):
        """测试渲染模板"""
        template = PromptTemplate(
            name="test",
            template="Hello, $name! You are $age years old.",
            variables=["name", "age"],
        )

        result = template.render(name="Alice", age=30)
        assert result == "Hello, Alice! You are 30 years old."

    def test_render_missing_variable(self):
        """测试缺少变量"""
        template = PromptTemplate(
            name="test",
            template="Hello, $name!",
            variables=["name"],
        )

        with pytest.raises(KeyError):
            template.render()

    def test_safe_render(self):
        """测试安全渲染"""
        template = PromptTemplate(
            name="test",
            template="Hello, $name! Your city is $city.",
            variables=["name", "city"],
        )

        result = template.safe_render(name="Alice")
        assert "Alice" in result
        assert "$city" in result  # 未提供的变量保留

    def test_validate_variables(self):
        """测试验证变量"""
        template = PromptTemplate(
            name="test",
            template="Hello, $name!",
            variables=["name"],
        )

        assert template.validate_variables(name="Alice") is True
        assert template.validate_variables() is False

    def test_get_missing_variables(self):
        """测试获取缺失变量"""
        template = PromptTemplate(
            name="test",
            template="Hello, $name! You are $age years old.",
            variables=["name", "age"],
        )

        missing = template.get_missing_variables(name="Alice")
        assert "age" in missing
        assert "name" not in missing

    def test_render_multiline_template(self):
        """测试多行模板"""
        template = PromptTemplate(
            name="test",
            template="""
            Name: $name
            Age: $age
            City: $city
            """,
            variables=["name", "age", "city"],
        )

        result = template.render(name="Alice", age=30, city="Tokyo")
        assert "Alice" in result
        assert "30" in result
        assert "Tokyo" in result


class TestPromptTemplateLoader:
    """测试 PromptTemplateLoader"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_yaml_template(self, temp_dir):
        """创建示例 YAML 模板"""
        template_data = {
            "name": "test_yaml",
            "version": "1.0.0",
            "description": "Test YAML template",
            "template": "Hello, $name!",
            "variables": ["name"],
        }

        file_path = temp_dir / "test_yaml.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(template_data, f)

        return file_path

    @pytest.fixture
    def sample_json_template(self, temp_dir):
        """创建示例 JSON 模板"""
        template_data = {
            "name": "test_json",
            "version": "1.0.0",
            "description": "Test JSON template",
            "template": "Hello, $name!",
            "variables": ["name"],
        }

        file_path = temp_dir / "test_json.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(template_data, f)

        return file_path

    def test_load_from_yaml_file(self, sample_yaml_template):
        """测试从 YAML 文件加载"""
        loader = PromptTemplateLoader()
        template = loader.load_from_file(sample_yaml_template)

        assert template.name == "test_yaml"
        assert template.version == "1.0.0"
        assert "name" in template.variables

    def test_load_from_json_file(self, sample_json_template):
        """测试从 JSON 文件加载"""
        loader = PromptTemplateLoader()
        template = loader.load_from_file(sample_json_template)

        assert template.name == "test_json"
        assert template.version == "1.0.0"
        assert "name" in template.variables

    def test_load_from_dict(self):
        """测试从字典加载"""
        loader = PromptTemplateLoader()
        template_data = {
            "name": "test_dict",
            "version": "1.0.0",
            "template": "Hello, $name!",
            "variables": ["name"],
        }

        template = loader.load_from_dict(template_data)

        assert template.name == "test_dict"
        assert template.version == "1.0.0"

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        loader = PromptTemplateLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_from_file("nonexistent.yaml")

    def test_load_unsupported_format(self, temp_dir):
        """测试加载不支持的格式"""
        file_path = temp_dir / "test.txt"
        file_path.write_text("test")

        loader = PromptTemplateLoader()

        with pytest.raises(ValueError, match="Unsupported file format"):
            loader.load_from_file(file_path)

    def test_load_with_cache(self, temp_dir, sample_yaml_template):
        """测试缓存功能"""
        loader = PromptTemplateLoader(template_dir=temp_dir)

        # 第一次加载
        template1 = loader.load("test_yaml", use_cache=True)
        # 第二次加载（应该从缓存）
        template2 = loader.load("test_yaml", use_cache=True)

        assert template1 is template2  # 应该是同一个对象

    def test_load_without_cache(self, temp_dir, sample_yaml_template):
        """测试不使用缓存"""
        loader = PromptTemplateLoader(template_dir=temp_dir)

        # 第一次加载
        template1 = loader.load("test_yaml", use_cache=False)
        # 第二次加载（不使用缓存）
        template2 = loader.load("test_yaml", use_cache=False)

        assert template1 is not template2  # 应该是不同的对象

    def test_list_templates(self, temp_dir, sample_yaml_template, sample_json_template):
        """测试列出模板"""
        loader = PromptTemplateLoader(template_dir=temp_dir)
        templates = loader.list_templates()

        assert "test_yaml" in templates
        assert "test_json" in templates

    def test_clear_cache(self, temp_dir, sample_yaml_template):
        """测试清空缓存"""
        loader = PromptTemplateLoader(template_dir=temp_dir)

        # 加载并缓存
        template1 = loader.load("test_yaml", use_cache=True)

        # 清空缓存
        loader.clear_cache()

        # 再次加载
        template2 = loader.load("test_yaml", use_cache=True)

        assert template1 is not template2  # 应该是不同的对象


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_loader(self):
        """测试获取全局加载器"""
        loader1 = get_loader()
        loader2 = get_loader()

        assert loader1 is loader2  # 应该是同一个实例

    def test_load_template_example(self):
        """测试加载示例模板"""
        # 加载内置的示例模板
        template = load_template("example")

        assert template.name == "example"
        assert template.version == "1.0.0"

    def test_render_template_example(self):
        """测试渲染示例模板"""
        result = render_template(
            "example",
            name="Alice",
            feature1="Feature A",
            feature2="Feature B",
            context="Test context",
        )

        assert "Alice" in result
        assert "Feature A" in result
        assert "Feature B" in result
        assert "Test context" in result


class TestTemplateVersioning:
    """测试模板版本管理"""

    def test_version_field(self):
        """测试版本字段"""
        template = PromptTemplate(
            name="test",
            version="2.1.0",
            template="Test",
            variables=[],
        )

        assert template.version == "2.1.0"

    def test_default_version(self):
        """测试默认版本"""
        template = PromptTemplate(
            name="test",
            template="Test",
            variables=[],
        )

        assert template.version == "1.0.0"


class TestTemplateMetadata:
    """测试模板元数据"""

    def test_metadata_field(self):
        """测试元数据字段"""
        template = PromptTemplate(
            name="test",
            template="Test",
            variables=[],
            metadata={"author": "Test Author", "tags": ["test", "example"]},
        )

        assert template.metadata["author"] == "Test Author"
        assert "test" in template.metadata["tags"]

    def test_empty_metadata(self):
        """测试空元数据"""
        template = PromptTemplate(
            name="test",
            template="Test",
            variables=[],
        )

        assert template.metadata == {}


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_template(self):
        """测试空模板"""
        template = PromptTemplate(
            name="empty",
            template="",
            variables=[],
        )

        result = template.render()
        assert result == ""

    def test_no_variables(self):
        """测试无变量模板"""
        template = PromptTemplate(
            name="static",
            template="This is a static template.",
            variables=[],
        )

        result = template.render()
        assert result == "This is a static template."

    def test_extra_variables(self):
        """测试额外的变量"""
        template = PromptTemplate(
            name="test",
            template="Hello, $name!",
            variables=["name"],
        )

        # 提供额外的变量不应该导致错误
        result = template.render(name="Alice", extra="value")
        assert result == "Hello, Alice!"

    def test_special_characters_in_template(self):
        """测试模板中的特殊字符"""
        template = PromptTemplate(
            name="special",
            template="Price: $$100, Name: $name",
            variables=["name"],
        )

        result = template.render(name="Alice")
        # $$ 会被解释为单个 $
        assert "$100" in result or "$$100" in result
        assert "Alice" in result

