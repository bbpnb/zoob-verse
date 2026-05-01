"""可视化模块：将图谱 JSON 渲染为交互式 HTML"""

import json
from pathlib import Path

import networkx as nx
from pyvis.network import Network


def visualize_graph(json_path: str | Path, output_path: str | Path) -> None:
    """读取图谱 JSON，生成交互式 HTML 关系图。

    Args:
        json_path: 图谱 JSON 文件路径
        output_path: 输出 HTML 文件路径
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    G = nx.DiGraph()

    # 节点颜色映射
    color_map = {
        "人物": "#FF5733",
        "门派": "#33FF57",
        "武功": "#3357FF",
        "地点": "#F39C12",
        "兵器": "#8E44AD",
        "事件": "#1ABC9C",
    }

    # 添加节点
    for entity in data.get("entities", []):
        name = entity["name"]
        etype = entity.get("type", "未知")
        desc = entity.get("description", "")
        color = color_map.get(etype, "#95A5A6")
        # Include description in title (truncate for readability)
        title_text = f"{etype}: {name}"
        if desc:
            # Replace SEP with newline for better readability
            formatted_desc = desc.replace("<SEP>", "\n")
            if len(formatted_desc) > 300:
                formatted_desc = formatted_desc[:300] + "..."
            title_text += f"\n{formatted_desc}"
        G.add_node(name, label=name, title=title_text, color=color, size=20)

    # 添加边
    for rel in data.get("relationships", []):
        rel_type = rel.get("type", "关联")
        desc = rel.get("description", "")
        G.add_edge(
            rel["source"],
            rel["target"],
            label=rel_type,
            title=f"{rel_type}: {desc}",
            arrows="to",
        )

    # 配置 pyvis 网络
    net = Network(
        height="800px",
        width="100%",
        bgcolor="#1E1E1E",
        font_color="#E0E0E0",
        directed=True,
        notebook=False,
    )
    net.from_nx(G)

    # 物理引擎配置：让布局更自然
    net.force_atlas_2based(
        central_gravity=0.01,
        gravity=-50,
        spring_length=150,
        spring_strength=0.1,
        damping=0.4,
    )

    # 添加图例
    legend_items = []
    for etype, color in color_map.items():
        if any(e.get("type") == etype for e in data.get("entities", [])):
            legend_items.append(f'<span style="color:{color}">●</span> {etype}')

    legend_html = f"""
    <div style="position:fixed;top:10px;right:10px;background:rgba(30,30,30,0.9);padding:15px;border-radius:8px;border:1px solid #444;z-index:1000;">
        <h4 style="margin:0 0 10px 0;color:white;">图例</h4>
        {' '.join(legend_items)}
    </div>
    """
    net.set_options(f"""
    var options = {{
        "layout": {{
            "improvedLayout": true
        }},
        "interaction": {{
            "hover": true,
            "tooltipDelay": 200,
            "zoomView": true,
            "dragView": true
        }},
        "physics": {{
            "enabled": true,
            "forceAtlas2Based": {{
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 150,
                "springConstant": 0.1
            }},
            "maxVelocity": 146,
            "minVelocity": 0.1,
            "solver": "forceAtlas2Based"
        }}
    }}
    """)

    # 注入图例 HTML
    html_content = net.generate_html()
    html_content = html_content.replace("<body>", f"<body>{legend_html}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_content, encoding="utf-8")

    print(f"可视化完成: {output}")
    print(f"节点: {G.number_of_nodes()}, 边: {G.number_of_edges()}")
