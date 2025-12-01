"""
HTML Templates - Reusable HTML templates for diagram output
"""

from datetime import datetime
from typing import Dict, Any, List, Optional


class HTMLTemplates:
    """Collection of HTML templates for diagram output"""

    @staticmethod
    def create_base_page(title: str, mermaid_code: str, diagram_type: str = "Diagram",
                         extra_css: str = "", extra_js: str = "",
                         content_before: str = "", content_after: str = "") -> str:
        """
        Create a base HTML page with Mermaid diagram.

        Args:
            title: Page title
            mermaid_code: Mermaid diagram code
            diagram_type: Type of diagram (for display)
            extra_css: Additional CSS styles
            extra_js: Additional JavaScript
            content_before: HTML content to add before the diagram
            content_after: HTML content to add after the diagram

        Returns:
            Complete HTML page as string
        """

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>

    <!-- Mermaid.js -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>

    <!-- Bootstrap 5 for better styling -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
        /* Base styles */
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 95%;
            margin: 0 auto;
        }}

        .card {{
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            border: none;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.95);
        }}

        .card-header {{
            background: linear-gradient(90deg, #4A90E2, #5C6BC0);
            color: white;
            border-bottom: none;
            padding: 20px 30px;
        }}

        .card-body {{
            padding: 30px;
        }}

        .mermaid-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid #e0e0e0;
            min-height: 500px;
            overflow-x: auto;
        }}

        .mermaid-container .mermaid {{
            min-width: 100%;
            min-height: 500px;
        }}

        .code-container {{
            background: #2c3e50;
            color: #ecf0f1;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }}

        .legend {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #4A90E2;
        }}

        .legend-item {{
            display: inline-flex;
            align-items: center;
            margin-right: 20px;
            margin-bottom: 8px;
        }}

        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 8px;
            border: 1px solid #ddd;
        }}

        /* Responsive design */
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}

            .card-body {{
                padding: 15px;
            }}

            .mermaid-container {{
                padding: 10px;
                min-height: 300px;
            }}
        }}

        /* Additional custom styles */
        {extra_css}
    </style>

    <script>
        // Mermaid configuration
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }},
            er: {{
                useMaxWidth: true,
                diagramPadding: 20
            }},
            class: {{
                useMaxWidth: true
            }}
        }});

        // Auto-resize diagrams on window resize
        let resizeTimer;
        window.addEventListener('resize', function() {{
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {{
                mermaid.init();
            }}, 250);
        }});

        // Copy Mermaid code to clipboard
        function copyMermaidCode() {{
            const codeElement = document.getElementById('mermaid-code');
            const textArea = document.createElement('textarea');
            textArea.value = codeElement.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);

            const button = document.getElementById('copy-button');
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="bi bi-check"></i> Copied!';
            button.classList.add('btn-success');
            button.classList.remove('btn-primary');

            setTimeout(function() {{
                button.innerHTML = originalText;
                button.classList.remove('btn-success');
                button.classList.add('btn-primary');
            }}, 2000);
        }}

        // Toggle code visibility
        function toggleCode() {{
            const codeContainer = document.getElementById('code-container');
            const toggleButton = document.getElementById('toggle-code-button');

            if (codeContainer.style.display === 'none') {{
                codeContainer.style.display = 'block';
                toggleButton.innerHTML = '<i class="bi bi-eye-slash"></i> Hide Code';
            }} else {{
                codeContainer.style.display = 'none';
                toggleButton.innerHTML = '<i class="bi bi-eye"></i> Show Code';
            }}
        }}

        // Additional JavaScript
        {extra_js}
    </script>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="card-header">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h1 class="h3 mb-0">{title}</h1>
                        <p class="mb-0 opacity-75">{diagram_type} • Generated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    </div>
                    <div class="btn-group">
                        <button id="toggle-code-button" class="btn btn-outline-light btn-sm" onclick="toggleCode()">
                            <i class="bi bi-eye"></i> Show Code
                        </button>
                        <button id="copy-button" class="btn btn-outline-light btn-sm" onclick="copyMermaidCode()">
                            <i class="bi bi-clipboard"></i> Copy Code
                        </button>
                    </div>
                </div>
            </div>

            <div class="card-body">
                {content_before}

                <div class="mermaid-container">
                    <div class="mermaid">
{mermaid_code}
                    </div>
                </div>

                <div id="code-container" class="code-container" style="display: none;">
                    <pre id="mermaid-code"><code>{mermaid_code}</code></pre>
                </div>

                {content_after}

                <div class="mt-4 pt-3 border-top text-center text-muted small">
                    <p class="mb-1">Generated by Codesys XML Documentation Generator • Using Mermaid v10.6.1</p>
                    <p class="mb-0">
                        <a href="https://mermaid.js.org/" target="_blank" class="text-decoration-none">Mermaid.js Documentation</a> • 
                        <a href="https://github.com/mermaid-js/mermaid" target="_blank" class="text-decoration-none">GitHub</a>
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">

    <!-- Bootstrap JS (optional) -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

        return html

    @staticmethod
    def create_flowchart_legend() -> str:
        """Create a legend for flowchart diagrams"""
        return """
        <div class="legend">
            <h6 class="mb-2"><i class="bi bi-info-circle"></i> Diagram Legend</h6>
            <div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #e1f5fe; border-color: #01579b;"></div>
                    <span>Structure</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f3e5f5; border-color: #4a148c;"></div>
                    <span>Union</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #e8f5e8; border-color: #1b5e20;"></div>
                    <span>Enumeration</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffffff; border-color: #90a4ae;"></div>
                    <span>Member</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f5f5f5; border-color: #616161;"></div>
                    <span>Basic/Unknown Type</span>
                </div>
            </div>
            <p class="mt-2 mb-0 small text-muted">
                <strong>Layout Rules:</strong> Members step down ↓ • Types branch across →
            </p>
        </div>
        """

    @staticmethod
    def create_type_details_table(item, title: str = "Type Details") -> str:
        """Create a table showing type details"""
        if not hasattr(item, 'members') or not item.members:
            return ""

        rows = ""
        for member in item.members:
            desc = getattr(member, 'description', '') or ''
            initial = getattr(member, 'initial_value', '')
            initial_text = f" = {initial}" if initial not in [None, ''] else ""

            rows += f"""
            <tr>
                <td><code>{member.name}</code></td>
                <td><span class="badge bg-secondary">{member.type}</span>{initial_text}</td>
                <td>{desc}</td>
            </tr>"""

        return f"""
        <div class="mt-4">
            <h5><i class="bi bi-table"></i> {title}</h5>
            <div class="table-responsive">
                <table class="table table-sm table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Member</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    @staticmethod
    def create_enum_table(enum, title: str = "Enumeration Values") -> str:
        """Create a table showing enum values"""
        if not hasattr(enum, 'values') or not enum.values:
            return ""

        rows = ""
        for i, value in enumerate(enum.values, 1):
            desc = getattr(value, 'description', '') or ''

            rows += f"""
            <tr>
                <td class="text-center">{i}</td>
                <td><code>{value.name}</code></td>
                <td><span class="badge bg-info">{value.value}</span></td>
                <td>{desc}</td>
            </tr>"""

        return f"""
        <div class="mt-4">
            <h5><i class="bi bi-list-ol"></i> {title} ({len(enum.values)} values)</h5>
            <div class="table-responsive">
                <table class="table table-sm table-striped table-hover">
                    <thead>
                        <tr>
                            <th class="text-center">#</th>
                            <th>Constant Name</th>
                            <th>Value</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
        """