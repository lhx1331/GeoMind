"""
GeoMind 命令行接口

提供命令行工具来使用 GeoMind Agent。

使用示例:
    # 基础使用
    geomind locate photo.jpg
    
    # 指定输出格式
    geomind locate photo.jpg --format json
    
    # 启用迭代优化
    geomind locate photo.jpg --iterations
    
    # 批量处理
    geomind locate photo1.jpg photo2.jpg photo3.jpg
    
    # 输出到文件
    geomind locate photo.jpg --output result.json
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

import click

from geomind import GeoMindAgent
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


def format_prediction_text(prediction, verbose: bool = False) -> str:
    """
    格式化预测结果为文本
    
    Args:
        prediction: 预测结果
        verbose: 是否详细输出
    
    Returns:
        格式化的文本
    """
    lines = []
    lines.append("=" * 60)
    lines.append("📍 地理位置预测结果")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"纬度: {prediction.lat:.6f}")
    lines.append(f"经度: {prediction.lon:.6f}")
    lines.append(f"置信度: {prediction.confidence:.2%}")
    
    if verbose:
        lines.append("")
        lines.append("推理过程:")
        lines.append(f"  {prediction.reasoning}")
        
        if prediction.supporting_evidence:
            lines.append("")
            lines.append("支持证据:")
            for evidence in prediction.supporting_evidence:
                lines.append(f"  • {evidence}")
        
        if prediction.alternative_locations:
            lines.append("")
            lines.append(f"备选位置: {len(prediction.alternative_locations)} 个")
            for i, alt in enumerate(prediction.alternative_locations[:3], 1):
                lines.append(f"  {i}. {alt.get('name', 'Unknown')}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def format_prediction_json(prediction) -> str:
    """
    格式化预测结果为 JSON
    
    Args:
        prediction: 预测结果
    
    Returns:
        JSON 字符串
    """
    data = {
        "lat": prediction.lat,
        "lon": prediction.lon,
        "confidence": prediction.confidence,
        "reasoning": prediction.reasoning,
        "supporting_evidence": prediction.supporting_evidence or [],
        "alternative_locations": prediction.alternative_locations or [],
    }
    
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_prediction_csv(prediction) -> str:
    """
    格式化预测结果为 CSV
    
    Args:
        prediction: 预测结果
    
    Returns:
        CSV 字符串
    """
    return f"{prediction.lat},{prediction.lon},{prediction.confidence}"


@click.group()
@click.version_option(version="0.1.0", prog_name="geomind")
def cli():
    """
    GeoMind - 通用地理推理 Agent
    
    基于 PHRV 框架的多模态地理位置推理系统。
    """
    pass


@cli.command()
@click.argument('images', nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    '--format', '-f',
    type=click.Choice(['text', 'json', 'csv'], case_sensitive=False),
    default='text',
    help='输出格式'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='输出文件路径（默认输出到标准输出）'
)
@click.option(
    '--iterations', '-i',
    is_flag=True,
    help='启用迭代优化'
)
@click.option(
    '--max-iterations',
    type=int,
    default=2,
    help='最大迭代次数（默认: 2）'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='详细输出'
)
@click.option(
    '--config', '-c',
    type=click.Path(exists=True),
    help='配置文件路径'
)
def locate(
    images: List[str],
    format: str,
    output: Optional[str],
    iterations: bool,
    max_iterations: int,
    verbose: bool,
    config: Optional[str],
):
    """
    预测图像的地理位置
    
    示例:
        geomind locate photo.jpg
        
        geomind locate photo.jpg --format json --output result.json
        
        geomind locate photo1.jpg photo2.jpg --iterations
    """
    try:
        # 运行异步任务
        asyncio.run(_locate_async(
            images=images,
            format=format,
            output=output,
            iterations=iterations,
            max_iterations=max_iterations,
            verbose=verbose,
            config=config,
        ))
    except KeyboardInterrupt:
        click.echo("\n\n❌ 操作已取消", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n❌ 错误: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


async def _locate_async(
    images: List[str],
    format: str,
    output: Optional[str],
    iterations: bool,
    max_iterations: int,
    verbose: bool,
    config: Optional[str],
):
    """
    异步定位函数
    """
    # 创建 Agent
    if verbose:
        click.echo("🚀 初始化 GeoMind Agent...")
    
    agent = GeoMindAgent(
        config_path=config,
        enable_iterations=iterations,
        max_iterations=max_iterations,
    )
    
    if verbose:
        click.echo(f"   Agent: {agent}")
        click.echo("")
    
    # 处理单个或多个图像
    results = []
    
    with click.progressbar(
        images,
        label='处理图像',
        show_pos=True,
    ) as bar:
        for image_path in bar:
            if verbose:
                click.echo(f"\n📷 处理: {image_path}")
            
            try:
                prediction = await agent.geolocate(image_path)
                results.append({
                    'image': image_path,
                    'prediction': prediction,
                    'success': True,
                })
                
                if verbose:
                    click.echo(f"   ✓ 完成: ({prediction.lat:.4f}, {prediction.lon:.4f})")
            
            except Exception as e:
                results.append({
                    'image': image_path,
                    'error': str(e),
                    'success': False,
                })
                
                if verbose:
                    click.echo(f"   ✗ 失败: {e}")
    
    # 格式化输出
    if format == 'text':
        output_text = _format_results_text(results, verbose)
    elif format == 'json':
        output_text = _format_results_json(results)
    elif format == 'csv':
        output_text = _format_results_csv(results)
    else:
        output_text = _format_results_text(results, verbose)
    
    # 输出结果
    if output:
        # 输出到文件
        Path(output).write_text(output_text, encoding='utf-8')
        click.echo(f"\n✅ 结果已保存到: {output}")
    else:
        # 输出到标准输出
        click.echo("\n" + output_text)


def _format_results_text(results: List[dict], verbose: bool) -> str:
    """格式化多个结果为文本"""
    lines = []
    
    for i, result in enumerate(results, 1):
        if i > 1:
            lines.append("\n")
        
        lines.append(f"图像 {i}: {result['image']}")
        lines.append("-" * 60)
        
        if result['success']:
            lines.append(format_prediction_text(result['prediction'], verbose))
        else:
            lines.append(f"❌ 错误: {result['error']}")
    
    # 添加摘要
    if len(results) > 1:
        success_count = sum(1 for r in results if r['success'])
        lines.append("\n")
        lines.append("=" * 60)
        lines.append(f"处理完成: {success_count}/{len(results)} 成功")
        lines.append("=" * 60)
    
    return "\n".join(lines)


def _format_results_json(results: List[dict]) -> str:
    """格式化多个结果为 JSON"""
    data = []
    
    for result in results:
        if result['success']:
            pred = result['prediction']
            data.append({
                'image': result['image'],
                'success': True,
                'lat': pred.lat,
                'lon': pred.lon,
                'confidence': pred.confidence,
                'reasoning': pred.reasoning,
                'supporting_evidence': pred.supporting_evidence or [],
                'alternative_locations': pred.alternative_locations or [],
            })
        else:
            data.append({
                'image': result['image'],
                'success': False,
                'error': result['error'],
            })
    
    return json.dumps(data, indent=2, ensure_ascii=False)


def _format_results_csv(results: List[dict]) -> str:
    """格式化多个结果为 CSV"""
    lines = ['image,lat,lon,confidence,success']
    
    for result in results:
        if result['success']:
            pred = result['prediction']
            lines.append(f"{result['image']},{pred.lat},{pred.lon},{pred.confidence},true")
        else:
            lines.append(f"{result['image']},,,false")
    
    return "\n".join(lines)


@cli.command()
def version():
    """显示版本信息"""
    click.echo("GeoMind v0.1.0")
    click.echo("通用地理推理 Agent")


@cli.command()
def info():
    """显示系统信息"""
    from geomind.config.settings import get_settings
    
    click.echo("=" * 60)
    click.echo("GeoMind 系统信息")
    click.echo("=" * 60)
    
    try:
        settings = get_settings()
        
        click.echo(f"\nLLM:")
        click.echo(f"  提供商: {settings.llm.provider.value}")
        click.echo(f"  模型: {settings.llm.model}")
        
        click.echo(f"\nVLM:")
        click.echo(f"  提供商: {settings.vlm.provider.value}")
        click.echo(f"  模型: {settings.vlm.model}")
        
        click.echo(f"\nGeoCLIP:")
        click.echo(f"  设备: {settings.geoclip.device}")
        click.echo(f"  模型路径: {settings.geoclip.model_path or '默认'}")
        
        click.echo(f"\n日志:")
        click.echo(f"  级别: {settings.logging.level}")
        click.echo(f"  输出: {settings.logging.output}")
        
        click.echo("=" * 60)
    
    except Exception as e:
        click.echo(f"\n❌ 错误: {e}", err=True)


def main():
    """主入口"""
    cli()


if __name__ == '__main__':
    main()

