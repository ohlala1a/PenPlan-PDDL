"""Knowledge graph abstraction tailored for PenPlan-PDDL."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .utils import HashingVectorizer, cosine_similarity


@dataclass
class GraphNode:
    node_id: str
    name: str
    kind: str
    tactic: str
    description: str
    relevance: float
    embedding: List[float]


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str


class KnowledgeGraph:
    """Lightweight graph that supports semantic retrieval."""

    def __init__(self, nodes: Iterable[GraphNode], edges: Iterable[GraphEdge]):
        self._nodes: Dict[str, GraphNode] = {node.node_id: node for node in nodes}
        self._outgoing: Dict[str, List[GraphEdge]] = {}
        self._incoming: Dict[str, List[GraphEdge]] = {}
        for edge in edges:
            self._outgoing.setdefault(edge.source, []).append(edge)
            self._incoming.setdefault(edge.target, []).append(edge)

    @classmethod
    def from_json(cls, path: Path, vectorizer: Optional[HashingVectorizer] = None) -> "KnowledgeGraph":
        vectorizer = vectorizer or HashingVectorizer()
        payload = json.loads(path.read_text(encoding="utf-8"))
        nodes: List[GraphNode] = []
        for raw in payload.get("nodes", []):
            embedding_text = raw.get("embedding_text") or raw.get("description") or raw["name"]
            nodes.append(
                GraphNode(
                    node_id=raw["id"],
                    name=raw["name"],
                    kind=raw.get("type", "technique"),
                    tactic=raw.get("tactic", "unknown"),
                    description=raw.get("description", ""),
                    relevance=float(raw.get("relevance", 0.5)),
                    embedding=vectorizer.encode(embedding_text),
                )
            )
        edges = [
            GraphEdge(edge["source"], edge["target"], edge.get("relation", "related"))
            for edge in payload.get("edges", [])
        ]
        return cls(nodes, edges)

    def node(self, node_id: str) -> GraphNode:
        return self._nodes[node_id]

    def nodes(self) -> Iterable[GraphNode]:
        return self._nodes.values()

    def outgoing(self, node_id: str) -> List[GraphEdge]:
        return list(self._outgoing.get(node_id, []))

    def incoming(self, node_id: str) -> List[GraphEdge]:
        return list(self._incoming.get(node_id, []))

    def retrieve(
        self,
        query: str,
        top_k: int,
        semantic_weight: float,
        structural_weight: float,
        similarity_threshold: float,
        vectorizer: Optional[HashingVectorizer] = None,
    ) -> List[Tuple[GraphNode, float]]:
        vectorizer = vectorizer or HashingVectorizer()
        query_embedding = vectorizer.encode(query)
        scored: List[Tuple[GraphNode, float]] = []
        for node in self._nodes.values():
            semantic = cosine_similarity(query_embedding, node.embedding)
            if semantic < similarity_threshold:
                continue
            structural = self._structural_signal(node)
            score = semantic_weight * semantic + structural_weight * structural
            scored.append((node, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def _structural_signal(self, node: GraphNode) -> float:
        parents = len(self._incoming.get(node.node_id, []))
        children = len(self._outgoing.get(node.node_id, []))
        coverage = min(node.relevance + 0.05 * (parents + children), 1.0)
        return coverage


__all__ = ["KnowledgeGraph", "GraphNode", "GraphEdge"]
