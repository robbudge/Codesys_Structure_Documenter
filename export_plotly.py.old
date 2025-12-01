#!/usr/bin/env python3
"""
Plotly-based interactive visualization exporter
"""

import plotly.graph_objects as go
import networkx as nx
from pathlib import Path
from typing import Dict
from export_networkx import NetworkXExporter


class PlotlyExporter:
    def __init__(self):
        self.format_name = "HTML (Plotly)"

    def export(self, parsed_data: Dict, output_dir: Path) -> None:
        """Generate interactive HTML visualization"""
        # Build graph using NetworkX exporter
        nx_exporter = NetworkXExporter()
        graph = nx_exporter.build_relationship_graph(parsed_data)

        # Create interactive visualization
        self.create_interactive_visualization(graph, output_dir / "codesys_structures.html")

    def create_interactive_visualization(self, graph: nx.DiGraph, output_path: Path) -> None:
        """Create interactive visualization using Plotly"""
        pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)

        # Create edge traces
        edge_traces = self._create_edge_traces(graph, pos)

        # Create node trace
        node_trace = self._create_node_trace(graph, pos)

        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace],
                        layout=self._create_layout())

        # Add annotations for node types
        self._add_legend_annotations(fig)

        # Save as interactive HTML
        fig.write_html(output_path,
                       config={'responsive': True},
                       include_plotlyjs=True)

    def _create_edge_traces(self, graph: nx.DiGraph, pos: Dict) -> list:
        """Create traces for edges"""
        edge_traces = []

        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]

            edge_trace = go.Scatter(
                x=[x0, x1, None], y=[y0, y1, None],
                line=dict(width=2, color='#888'),
                hoverinfo='none',
                mode='lines',
                showlegend=False
            )
            edge_traces.append(edge_trace)

        return edge_traces

    def _create_node_trace(self, graph: nx.DiGraph, pos: Dict) -> go.Scatter:
        """Create trace for nodes"""
        node_x, node_y, node_text, node_color, node_size = [], [], [], [], []

        color_map = {
            'structure': '#1f78b4',
            'enum': '#33a02c',
            'union': '#e31a1c'
        }

        size_map = {
            'structure': 20,
            'enum': 15,
            'union': 18
        }

        for node in graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            node_data = graph.nodes[node]
            node_type = node_data.get('type', 'unknown')

            # Create detailed hover text
            hover_text = self._create_hover_text(node, node_data, graph)
            node_text.append(hover_text)

            node_color.append(color_map.get(node_type, '#969696'))
            node_size.append(size_map.get(node_type, 12))

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[self._truncate_label(node) for node in graph.nodes()],
            textposition="middle center",
            textfont=dict(color='white', size=10, family="Arial Black"),
            marker=dict(
                color=node_color,
                size=node_size,
                line=dict(width=2, color='darkblue')
            ),
            hovertext=node_text,
            showlegend=False
        )

        return node_trace

    def _create_hover_text(self, node: str, node_data: Dict, graph: nx.DiGraph) -> str:
        """Create detailed hover text for nodes"""
        node_type = node_data.get('type', 'unknown')
        hover_text = f"<b>{node}</b><br>Type: {node_type}"

        if node_type == 'structure':
            members = node_data.get('members', [])
            hover_text += f"<br>Members: {len(members)}"
            if members:
                hover_text += "<br>---"
                for member in members[:5]:  # Show first 5 members
                    hover_text += f"<br>{member['name']} : {member['type']}"
                if len(members) > 5:
                    hover_text += f"<br>... and {len(members) - 5} more"

        elif node_type == 'enum':
            values = node_data.get('values', [])
            hover_text += f"<br>Values: {len(values)}"
            if values:
                hover_text += "<br>---"
                for value in values[:5]:  # Show first 5 values
                    hover_text += f"<br>{value['name']} = {value.get('value', '')}"
                if len(values) > 5:
                    hover_text += f"<br>... and {len(values) - 5} more"

        elif node_type == 'union':
            members = node_data.get('members', [])
            hover_text += f"<br>Members: {len(members)}"

        # Show connections
        in_edges = list(graph.in_edges(node))
        out_edges = list(graph.out_edges(node))
        hover_text += f"<br>---<br>Connections:"
        hover_text += f"<br>← In: {len(in_edges)}"
        hover_text += f"<br>→ Out: {len(out_edges)}"

        return hover_text

    def _truncate_label(self, label: str) -> str:
        """Truncate long labels for display"""
        return label if len(label) <= 15 else label[:12] + '...'

    def _create_layout(self) -> go.Layout:
        """Create layout for the plot"""
        return go.Layout(
            title=dict(
                text='CODESYS Structure Relationships',
                x=0.5,
                xanchor='center',
                font=dict(size=20, family="Arial")
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

    def _add_legend_annotations(self, fig: go.Figure) -> None:
        """Add legend annotations to the plot"""
        annotations = [
            dict(x=0.01, y=0.99, xref='paper', yref='paper',
                 text="<b>Legend:</b>", showarrow=False,
                 font=dict(size=12), align='left'),
            dict(x=0.01, y=0.96, xref='paper', yref='paper',
                 text="● Structure", showarrow=False,
                 font=dict(color='#1f78b4', size=10), align='left'),
            dict(x=0.01, y=0.93, xref='paper', yref='paper',
                 text="● Enum", showarrow=False,
                 font=dict(color='#33a02c', size=10), align='left'),
            dict(x=0.01, y=0.90, xref='paper', yref='paper',
                 text="● Union", showarrow=False,
                 font=dict(color='#e31a1c', size=10), align='left'),
        ]

        fig.update_layout(annotations=annotations)