"""
图片识别和翻译工具
"""

import os
import base64
from typing import Dict, Any
from pathlib import Path
from .base import Tool


class ScreenshotTool(Tool):
    """截图工具"""

    @property
    def name(self) -> str:
        return "screenshot"

    @property
    def description(self) -> str:
        return "截取屏幕并保存为图片文件"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "save_path": {
                    "type": "string",
                    "description": "保存路径（可选，默认保存到临时目录）"
                },
                "region": {
                    "type": "string",
                    "description": "截图区域，格式为 x,y,width,height（可选，默认全屏）"
                }
            }
        }

    async def execute(self, save_path: str = None, region: str = None) -> str:
        try:
            try:
                from PIL import ImageGrab
            except ImportError:
                return "错误: 需要安装 Pillow 库\npip install Pillow"

            # 确定保存路径
            if save_path:
                save_dir = os.path.dirname(save_path)
                if save_dir and not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
            else:
                # 保存到临时目录
                import tempfile
                from datetime import datetime
                temp_dir = tempfile.gettempdir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(temp_dir, f"screenshot_{timestamp}.png")

            # 截图
            if region:
                try:
                    # 解析区域: x,y,width,height
                    coords = [int(x.strip()) for x in region.split(',')]
                    if len(coords) == 4:
                        x, y, w, h = coords
                        screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                    else:
                        screenshot = ImageGrab.grab()
                except:
                    screenshot = ImageGrab.grab()
            else:
                screenshot = ImageGrab.grab()

            # 保存图片
            screenshot.save(save_path, 'PNG')

            return f"截图已保存: {save_path}"
        except Exception as e:
            return f"截图错误: {str(e)}"


class ImageVisionTool(Tool):
    """图片视觉识别工具（使用大模型多模态能力）"""

    def __init__(self, llm_provider):
        self.llm_provider = llm_provider

    @property
    def name(self) -> str:
        return "image_vision"

    @property
    def description(self) -> str:
        return "使用大模型识别图片内容，描述图片中的场景、物体等"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片文件路径"
                },
                "prompt": {
                    "type": "string",
                    "description": "识别提示（可选，例如：描述这张图片、这张图片里有什么）"
                }
            },
            "required": ["image_path"]
        }

    async def execute(self, image_path: str, prompt: str = None) -> str:
        try:
            if not os.path.exists(image_path):
                return f"错误: 图片文件不存在: {image_path}"

            # 检查图片格式
            if not image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')):
                return "错误: 不支持的图片格式，请使用 PNG, JPG, GIF, WEBP 或 BMP 格式"

            # 检查文件大小（限制10MB）
            if os.path.getsize(image_path) > 10 * 1024 * 1024:
                return "错误: 图片文件过大，请使用小于10MB的图片"

            # 编码图片为base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # 准备提示词
            user_prompt = prompt or "请详细描述这张图片中的内容，包括场景、物体、人物、文字等信息。"

            # 调用多模态LLM
            if self.llm_provider:
                try:
                    result = await self.llm_provider.chat_with_image(
                        image_base64=image_data,
                        prompt=user_prompt
                    )
                    return f"--- 图片识别结果 ---\n{result}"
                except Exception as e:
                    return f"图片识别错误: {str(e)}\n\n(提示: 请确保使用的模型支持多模态能力，如 qwen-vl-max 或 qwen-vl-plus)"
            else:
                return f"图片已准备好进行识别。\n图片路径: {image_path}\n提示词: {user_prompt}\n\n(注意: LLM提供者未配置，无法进行实际图片识别)"

        except Exception as e:
            return f"图片识别错误: {str(e)}"


class ImageOCRTool(Tool):
    """图片OCR识别工具"""

    @property
    def name(self) -> str:
        return "image_ocr"

    @property
    def description(self) -> str:
        return "识别图片中的文字内容"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片文件路径"
                },
                "language": {
                    "type": "string",
                    "description": "语言代码（可选，例如 chi_sim+eng）"
                }
            },
            "required": ["image_path"]
        }

    async def execute(self, image_path: str, language: str = None) -> str:
        try:
            if not os.path.exists(image_path):
                return f"错误: 图片文件不存在: {image_path}"

            try:
                from PIL import Image
                import pytesseract
            except ImportError:
                return "错误: 需要安装 Pillow 和 pytesseract 库\npip install Pillow pytesseract\n注意: 还需要安装 Tesseract OCR 引擎"

            # 打开图片
            img = Image.open(image_path)

            # 设置语言
            lang = language or 'chi_sim+eng'

            # 进行OCR识别
            text = pytesseract.image_to_string(img, lang=lang)

            if text.strip():
                return f"--- 图片文字识别结果 ---\n{text}"
            else:
                return "未识别到文字"
        except Exception as e:
            return f"图片识别错误: {str(e)}"


class TranslateTool(Tool):
    """翻译工具"""

    @property
    def name(self) -> str:
        return "translate"

    @property
    def description(self) -> str:
        return "翻译文本（支持多种语言）"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要翻译的文本"
                },
                "target_lang": {
                    "type": "string",
                    "description": "目标语言（例如 zh=中文, en=英文, ja=日文），默认zh"
                },
                "source_lang": {
                    "type": "string",
                    "description": "源语言（可选，自动检测）"
                }
            },
            "required": ["text"]
        }

    async def execute(
        self,
        text: str,
        target_lang: str = "zh",
        source_lang: str = None
    ) -> str:
        try:
            try:
                from deep_translator import GoogleTranslator
            except ImportError:
                return "错误: 需要安装 deep-translator 库\npip install deep-translator"

            translator = GoogleTranslator(
                source=source_lang or 'auto',
                target=target_lang
            )

            result = translator.translate(text)

            return f"原文: {text}\n翻译: {result}"
        except Exception as e:
            return f"翻译错误: {str(e)}"


class ImageCaptionTool(Tool):
    """图片描述工具"""

    @property
    def name(self) -> str:
        return "image_caption"

    @property
    def description(self) -> str:
        return "描述图片内容（简单的颜色和形状分析）"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片文件路径"
                }
            },
            "required": ["image_path"]
        }

    async def execute(self, image_path: str) -> str:
        try:
            if not os.path.exists(image_path):
                return f"错误: 图片文件不存在: {image_path}"

            try:
                from PIL import Image
                import numpy as np
            except ImportError:
                return "错误: 需要安装 Pillow 和 numpy 库\npip install Pillow numpy"

            # 打开图片
            img = Image.open(image_path)

            # 获取基本信息
            width, height = img.size
            format_info = img.format
            mode = img.mode

            # 转换为RGB
            if mode != 'RGB':
                img = img.convert('RGB')

            # 计算主色调
            img_array = np.array(img)
            avg_color = np.mean(img_array, axis=(0, 1))
            avg_color = avg_color.astype(int)

            # 计算颜色分布
            pixels = img_array.reshape(-1, 3)
            unique_colors = np.unique(pixels, axis=0)
            color_count = len(unique_colors)

            result = [f"--- 图片分析 ---"]
            result.append(f"尺寸: {width} x {height}")
            result.append(f"格式: {format_info}")
            result.append(f"模式: {mode}")
            result.append(f"平均颜色: RGB{tuple(avg_color)}")
            result.append(f"颜色数量: {color_count}")

            return "\n".join(result)
        except Exception as e:
            return f"图片分析错误: {str(e)}"
