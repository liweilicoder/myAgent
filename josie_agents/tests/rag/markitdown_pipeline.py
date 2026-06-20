import os
import time
import tempfile
from josie_agents.tools.builtin.rag_tool import RAGTool
import josie_agents.utils.log as log


class MarkitdownPipelineDemo:
    """MarkItDown处理管道演示类"""

    def __init__(self):
        self.rag_tool = RAGTool(
            knowledge_base_path="./demo_rag_kb",
            rag_namespace="markitdown_demo"
        )
        self.temp_dir = tempfile.mkdtemp()

    def create_sample_documents(self):
        """创建多格式示例文档"""
        log.delimiter("📄 创建多格式示例文档")
        log.delimiter("=" * 50)

        # 创建Markdown文档
        # 创建Markdown文档
        markdown_content = """# Python编程指南

        ## 基础语法
        Python是一种解释型、高级编程语言。

        ### 变量和数据类型
        - 整数：`42`
        - 字符串：`"Hello World"`
        - 列表：`[1, 2, 3]`

        ### 函数定义
        ```python
        def greet(name):
            return f"Hello, {name}!"
        ```

        ## 面向对象编程
        Python支持面向对象编程范式。

        ### 类定义
        ```python
        class Person:
            def __init__(self, name):
                self.name = name

            def say_hello(self):
                return f"Hello, I'm {self.name}"
        ```
        """

        # 创建HTML文档
        html_content = """<!DOCTYPE html>
        <html>
        <head>
            <title>Web开发基础</title>
        </head>
        <body>
            <h1>HTML基础</h1>
            <p>HTML是超文本标记语言，用于创建网页结构。</p>

            <h2>常用标签</h2>
            <ul>
                <li>h1-h6: 标题标签</li>
                <li>p: 段落标签</li>
                <li>div: 容器标签</li>
                <li>span: 行内标签</li>
            </ul>

            <h2>CSS样式</h2>
            <p>CSS用于控制网页的样式和布局。</p>
            <code>
                body { font-family: Arial, sans-serif; }
                .container { max-width: 1200px; margin: 0 auto; }
            </code>
        </body>
        </html>"""

        # 创建JSON文档
        json_content = """{
            "project": "HelloAgents",
            "version": "1.0.0",
            "description": "AI Agent开发框架",
            "features": [
                "记忆系统",
                "RAG检索",
                "工具集成",
                "多模态支持"
            ],
            "components": {
                "memory": {
                    "types": ["working", "episodic", "semantic", "perceptual"],
                    "storage": ["SQLite", "Qdrant", "Neo4j"]
                },
                "rag": {
                    "formats": ["PDF", "Word", "Excel", "HTML", "Markdown"],
                    "pipeline": ["MarkItDown", "Chunking", "Embedding", "Storage"]
                }
            }
        }"""

        # 创建CSV文档
        csv_content = """名称,类型,重要性,描述
        工作记忆,临时存储,0.7,存储当前会话的临时信息
        情景记忆,事件记录,0.8,记录具体的事件和经历
        语义记忆,知识存储,0.9,存储概念性知识和规则
        感知记忆,多模态,0.6,处理图像音频等感知数据
        向量检索,技术组件,0.8,基于语义相似度的检索
        知识图谱,技术组件,0.9,实体关系的结构化表示"""

        # 保存文档到临时目录
        documents = {
            "python_guide.md": markdown_content,
            "web_basics.html": html_content,
            "project_info.json": json_content,
            "memory_types.csv": csv_content
        }

        file_paths = {}
        for filename, content in documents.items():
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            file_paths[filename] = file_path
            log.test(f"✅ 创建文档: {filename}")

        return file_paths