#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成后端功能点思维导图
版本：适配 XMind 2021/2023/2024 (严格 JSON 结构)
修复：metadata 用户字段、节点结构、主题格式
"""

import zipfile
import json
import os
import uuid
import time

# 后端功能点数据（保持不变）
backend_features = {
    "项目管理": {
        "项目操作": [
            "创建项目: POST /api/projects",
            "列出项目: GET /api/projects",
            "获取项目详情: GET /api/projects/{project_id}",
            "获取项目统计信息: GET /api/projects/{project_id}/stats",
            "更新项目: PATCH /api/projects/{project_id}",
            "删除项目: DELETE /api/projects/{project_id}"
        ]
    },
    "文档管理": {
        "文档操作": [
            "上传文档: POST /api/documents/upload/{project_id}",
            "列出文档: GET /api/documents",
            "获取文档详情: GET /api/documents/{document_id}",
            "下载文档: GET /api/documents/{document_id}/download",
            "删除文档: DELETE /api/documents/{document_id}"
        ],
        "文档解析": [
            "解析文档: POST /api/documents/{document_id}/parse",
            "获取解析状态: GET /api/documents/{document_id}/parse-status",
            "获取文档内容: GET /api/documents/{document_id}/content"
        ]
    },
    "任务管理": {
        "任务操作": [
            "创建任务: POST /api/tasks",
            "列出任务: GET /api/tasks",
            "获取任务详情: GET /api/tasks/{task_id}",
            "更新任务: PATCH /api/tasks/{task_id}",
            "删除任务: DELETE /api/tasks/{task_id}"
        ],
        "任务关联": [
            "关联文档到任务: POST /api/tasks/{task_id}/documents",
            "关联功能点到任务: POST /api/tasks/{task_id}/function-points",
            "关联测试用例到任务: POST /api/tasks/{task_id}/test-cases",
            "关联测试脚本到任务: POST /api/tasks/{task_id}/test-scripts"
        ]
    },
    "功能点管理": {
        "功能点操作": [
            "人工创建功能点: POST /api/function-points (不需要审批，一次性创建一个)",
            "AI生成功能点: POST /api/generator/function-points (需要审批，支持批量创建)",
            "列出功能点: GET /api/function-points",
            "获取功能点详情: GET /api/function-points/{fp_id}",
            "更新功能点: PATCH /api/function-points/{fp_id}",
            "删除功能点: DELETE /api/function-points/{fp_id}",
            "导出功能点: GET /api/function-points/export"
        ],
        "功能点审批": [
            "批准功能点: POST /api/function-points/{fp_id}/approve (仅AI生成的需要)",
            "拒绝功能点: POST /api/function-points/{fp_id}/reject (仅AI生成的需要)"
        ]
    },
    "测试用例管理": {
        "测试用例操作": [
            "人工创建测试用例: POST /api/test-cases (不需要审批，一次性创建一个)",
            "AI生成测试用例: POST /api/generator/test-cases (需要审批，支持批量生成)",
            "列出测试用例: GET /api/test-cases",
            "获取测试用例详情: GET /api/test-cases/{tc_id}",
            "更新测试用例: PATCH /api/test-cases/{tc_id}",
            "删除测试用例: DELETE /api/test-cases/{tc_id}",
            "导出测试用例: GET /api/test-cases/export"
        ],
        "测试用例审批": [
            "批准测试用例: POST /api/test-cases/{tc_id}/approve (仅AI生成的需要)",
            "拒绝测试用例: POST /api/test-cases/{tc_id}/reject (仅AI生成的需要)"
        ]
    },
    "测试脚本管理": {
        "测试脚本操作": [
            "人工创建测试脚本: POST /api/test-scripts (不需要审批，一次性创建一个)",
            "AI生成测试脚本: POST /api/generator/scripts (需要审批，支持批量生成)",
            "列出测试脚本: GET /api/test-scripts",
            "获取测试脚本详情: GET /api/test-scripts/{script_id}",
            "更新测试脚本: PATCH /api/test-scripts/{script_id}",
            "删除测试脚本: DELETE /api/test-scripts/{script_id}",
            "下载测试脚本: GET /api/test-scripts/{script_id}/download"
        ],
        "测试脚本审批": [
            "批准测试脚本: POST /api/test-scripts/{script_id}/approve (仅AI生成的需要)",
            "拒绝测试脚本: POST /api/test-scripts/{script_id}/reject (仅AI生成的需要)"
        ],
        "测试数据生成": [
            "生成测试数据: POST /api/test-data/generate",
            "批量生成测试数据: POST /api/test-data/batch-generate",
            "获取测试数据: GET /api/test-data/{data_id}",
            "删除测试数据: DELETE /api/test-data/{data_id}"
        ]
    },
    "思维导图管理": {
        "思维导图操作": [
            "获取思维导图结构: GET /api/mind-map/{project_id}/structure",
            "拖拽节点: 支持拖动、放大、缩小",
            "折叠/展开节点: 支持层级管理",
            "导出思维导图: GET /api/mind-map/{project_id}/export"
        ]
    },
    "生成器": {
        "需求理解": [
            "理解需求: POST /api/generator/understand-requirements"
        ],
        "功能点生成": [
            "生成功能点: POST /api/generator/function-points",
            "保存功能点: POST /api/generator/function-points/save",
            "优化功能点: POST /api/generator/function-points/refine"
        ],
        "测试用例生成": [
            "生成测试用例: POST /api/generator/test-cases",
            "保存测试用例: POST /api/generator/test-cases/save",
            "优化测试用例: POST /api/generator/test-cases/refine"
        ],
        "测试脚本生成": [
            "生成测试脚本: POST /api/generator/scripts",
            "保存测试脚本: POST /api/generator/scripts/save",
            "优化测试脚本: POST /api/generator/scripts/refine"
        ],
        "向量统计": [
            "获取向量统计信息: GET /api/generator/vector-stats/{project_id}"
        ]
    },
    "核心服务": {
        "LLM服务": [
            "理解需求",
            "生成功能点",
            "优化功能点",
            "生成测试用例",
            "生成测试脚本",
            "文本嵌入"
        ],
        "文档解析服务": [
            "解析文档",
            "存储文档内容"
        ],
        "Milvus服务": [
            "向量存储",
            "向量检索",
            "集合管理"
        ],
        "RAG服务": [
            "检索相关上下文",
            "为功能点生成检索",
            "为测试用例生成检索",
            "为测试脚本生成检索"
        ],
        "存储服务": [
            "文件上传",
            "文件下载",
            "文件删除"
        ],
        "数据库服务": [
            "数据库初始化",
            "数据库连接管理",
            "Redis缓存服务",
            "Redis连接管理"
        ]
    },
    "数据库模型": {
        "核心模型": [
            "Project: 项目信息",
            "Task: 任务信息（区分不同批次操作）",
            "Document: 文档信息",
            "FunctionPoint: 功能点信息",
            "TestCase: 测试用例信息",
            "TestScript: 测试脚本信息",
            "MindMapNode: 思维导图节点信息"
        ],
        "枚举类型": [
            "DocType: 文档类型",
            "DocStatus: 文档状态",
            "TestType: 测试类型",
            "Priority: 优先级",
            "FPStatus: 功能点状态",
            "TCStatus: 测试用例状态",
            "TaskStatus: 任务状态",
            "ProjectStatus: 项目状态",
            "ScriptLanguage: 脚本语言",
            "ScriptStatus: 脚本状态",
            "NodeType: 节点类型"
        ]
    },
    "系统管理": {
        "健康检查": [
            "健康状态: GET /health"
        ],
        "根路径": [
            "系统信息: GET /"
        ]
    },
    "技术特性": {
        "API设计": [
            "RESTful API",
            "异步处理",
            "错误处理",
            "数据验证"
        ],
        "存储": [
            "MinIO对象存储",
            "Milvus向量数据库",
            "PostgreSQL关系数据库",
            "Redis缓存数据库"
        ],
        "安全": [
            "CORS配置",
            "日志记录",
            "错误处理"
        ],
        "性能": [
            "后台任务",
            "并行处理",
            "向量检索优化"
        ]
    }
}

def generate_strict_xmind(features, output_file):
    """
    生成严格符合 XMind 2021+ 标准的文件
    修复：
    1. metadata creator/modifiedBy 改为对象格式
    2. 标准化节点结构
    3. 兼容最新版XMind解析规则
    """
    
    # 生成基础 ID 和时间戳
    sheet_id = str(uuid.uuid4())
    root_id = str(uuid.uuid4())
    timestamp = int(time.time() * 1000)

    # 递归构建树形结构（标准化children格式）
    def build_tree(data):
        if isinstance(data, dict):
            children = []
            for key, value in data.items():
                node = {
                    "id": str(uuid.uuid4()),
                    "title": str(key),
                    "children": {
                        "attached": build_tree(value)
                    }
                }
                children.append(node)
            return children
        elif isinstance(data, list):
            return [{"id": str(uuid.uuid4()), "title": str(item)} for item in data]
        else:
            return []

    # 根节点
    root_topic = {
        "id": root_id,
        "title": "后端功能点",
        "children": {
            "attached": build_tree(features)
        }
    }

    # content.json（标准结构）
    content_json = [
        {
            "id": sheet_id,
            "type": "sheet",
            "title": "后端功能点思维导图",
            "rootTopic": root_topic,
            "theme": {"id": "snowbrush"}
        }
    ]

    # metadata.json（核心修复：用户字段必须是对象！）
    metadata_json = {
        "creator": {
            "name": "Python Script",
            "version": "1.0"
        },
        "modifiedBy": {
            "name": "Python Script",
            "version": "1.0"
        },
        "modified": timestamp,
        "created": timestamp,
        "version": "1.0.0",
        "theme": "snowbrush",
        "sheets": [
            {
                "id": sheet_id,
                "title": "后端功能点思维导图",
                "rootTopicId": root_id
            }
        ]
    }

    # manifest.json（保持标准）
    manifest_json = {
        "file-entries": [
            {"path": "content.json", "media-type": "application/vnd.xmind.content+json"},
            {"path": "metadata.json", "media-type": "application/vnd.xmind.metadata+json"}
        ]
    }

    # 写入文件
    if os.path.exists(output_file):
        os.remove(output_file)

    try:
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('content.json', json.dumps(content_json, ensure_ascii=False, indent=2))
            zf.writestr('metadata.json', json.dumps(metadata_json, ensure_ascii=False, indent=2))
            zf.writestr('manifest.json', json.dumps(manifest_json, ensure_ascii=False, indent=2))
        
        print(f"✅ 成功生成 XMind 文件: {output_file}")
        print(f"文件大小: {os.path.getsize(output_file)} 字节")
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            print(f"包含文件: {zf.namelist()}")
                
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    output_file = "backend_features_final.xmind"
    generate_strict_xmind(backend_features, output_file)
    print("\n🚀 生成完成！可直接用 XMind 2024 打开")