"""Core graph engine — generic operations, module-agnostic."""

import networkx as nx


class GraphEngine:
    """通用图引擎 — 不关心任何具体实体类型，只处理节点和边。"""

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_entity(self, name: str, type: str, **attrs) -> None:
        """添加实体节点。"""
        self.graph.add_node(name, type=type, **attrs)

    def add_relationship(self, source: str, target: str, type: str, **attrs) -> None:
        """添加关系边。"""
        self.graph.add_edge(source, target, type=type, **attrs)

    def shortest_path(self, source: str, target: str) -> list[str] | None:
        """查找两个实体之间的最短路径。"""
        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return None

    def community_detection(self) -> list[set]:
        """社区检测（Greedy Modularity）。"""
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(self.graph.to_undirected())
            communities = {}
            for node, comm in partition.items():
                communities.setdefault(comm, set()).add(node)
            return list(communities.values())
        except ImportError:
            # Fallback: connected components
            return list(nx.connected_components(self.graph.to_undirected()))

    def centrality(self, method: str = "degree") -> dict[str, float]:
        """计算节点中心性。"""
        if method == "degree":
            return dict(nx.degree_centrality(self.graph))
        elif method == "betweenness":
            return dict(nx.betweenness_centrality(self.graph))
        elif method == "pagerank":
            return dict(nx.pagerank(self.graph))
        else:
            raise ValueError(f"Unknown centrality method: {method}")

    def get_entity(self, name: str) -> dict | None:
        """获取实体信息。"""
        return self.graph.nodes.get(name)

    def get_neighbors(self, name: str) -> list[tuple]:
        """获取实体的所有关系。"""
        return list(self.graph.edges(name, data=True))

    def stats(self) -> dict:
        """图统计信息。"""
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "entity_types": set(nx.get_node_attributes(self.graph, "type").values()),
            "relationship_types": set(d["type"] for _, _, d in self.graph.edges(data=True)),
        }
