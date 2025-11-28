#!/usr/bin/env python3
"""
Matplotlib-based static visualization exporter
"""

import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path
from typing import Dict
from export_networkx import NetworkXExporter


class MatplotlibExporter:
    def __init__(self):
        self.format_name = "PNG (Matplotlib)"

    def export(self, parsed_data: Dict, output_dir: Path) -> None:
        """Generate static PNG visualization"""
        # Build graph using NetworkX exporter
        nx_exporter = NetworkXExporter()
        graph = nx_exporter.build_relationship_graph(parsed_data)

        # Create visualization
        self.create_static_visualization(graph, output_dir / "codesys_structures.png")

    def create_static_visualization(self, graph: nx.DiGraph, output_path: Path) -> None:
        """Create static visualization using matplotlib"""
        plt.figure(figsize=(20, 15))

        # Use spring layout for better node distribution
        pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)

        # Prepare node colors and sizes based on type
        node_colors, node_sizes, node_labels = self._prepare_node_attributes(graph)

        # Draw the graph
        nx.draw_networkx_nodes(graph, pos,
                               node_color=node_colors,
                               node_size=node_sizes,
                               alpha=0.9)

        nx.draw_networkx_edges(graph, pos,
                               edge_color='gray',
                               arrows=True,
                               arrowsize=20,
                               arrowstyle='->',
                               alpha=0.6)

        nx.draw_networkx_labels(graph, pos,
                                labels=node_labels,
                                font_size=8,
                                font_weight='bold')

        # Create legend
        self._create_legend()

        plt.title("CODESYS Structure Relationships", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close()

    def _prepare_node_attributes(self, graph: nx.DiGraph):
        """Prepare node attributes for visualization"""
        node_colors = []
        node_sizes = []
        node_labels = {}

        color_map = {
            'structure': '#1f78b4',  # Blue
            'enum': '#33a02c',  # Green
            'union': '#e31a1c'  # Red
        }

        size_map = {
            'structure': 800,
            'enum': 600,
            'union': 700
        }

        for node in graph.nodes():
            node_type = graph.nodes[node].get('type', 'unknown')

            # Color and size
            node_colors.append(color_map.get(node_type, '#969696'))
            node_sizes.append(size_map.get(node_type, 500))

            # Label (truncate if too long)
            label = node if len(node) <= 20 else node[:17] + '...'
            node_labels[node] = label

        return node_colors, node_sizes, node_labels

    def _create_legend(self):
        """Create a custom legend for the graph"""
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w',
                       markerfacecolor='#1f78b4', markersize=10, label='Structure'),
            plt.Line2D([0], [0], marker='o', color='w',
                       markerfacecolor='#33a02c', markersize=10, label='Enum'),
            plt.Line2D([0], [0], marker='o', color='w',
                       markerfacecolor='#e31a1c', markersize=10, label='Union')
        ]

        plt.legend(handles=legend_elements,
                   loc='upper left',
                   bbox_to_anchor=(0, 1),
                   frameon=True,
                   fancybox=True,
                   shadow=True)