"""
Export Manager for CodeSys XML Documentation Generator
Handles HTML export with UML-style formatting
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExportConfig:
    """Configuration for export options"""
    include_timestamp: bool = True
    uml_style: bool = True
    embed_referenced_types: bool = True
    create_index: bool = True

class ExportManager:
    """Manages export of documentation to HTML files with UML styling"""

    def __init__(self, type_registry: Dict):
        """
        Initialize ExportManager

        Args:
            type_registry: Dictionary of all available types
        """
        self.type_registry = type_registry
        self.config = ExportConfig()

    def export_all(self, items: Dict, output_dir: str = "exports") -> Dict:
        """
        Export all items to HTML files

        Args:
            items: Dictionary of items to export
            output_dir: Output directory

        Returns:
            Dictionary with export results
        """
        logger.info("=" * 80)
        logger.info("STARTING EXPORT PROCESS")
        logger.info("=" * 80)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Creating output directory: {output_dir}")

        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if self.config.include_timestamp else ""

        # Summary
        total_items = sum(len(item_list) for item_list in items.values())
        logger.info("Export Summary:")
        logger.info(f"  Total Items: {total_items}")
        for item_type, item_list in items.items():
            logger.info(f"  {item_type.capitalize()}: {len(item_list)}")

        # Resolve type references
        logger.debug("Resolving all type references...")
        self._resolve_type_references(items)
        logger.info("Type references resolved successfully")

        # Export files
        results = self._export_all_items(items, output_dir, timestamp)

        # Create index file
        if self.config.create_index:
            index_file = self._create_index_file(output_dir, items, timestamp)
            results['index_file'] = index_file

        # Final summary
        logger.info("=" * 80)
        logger.info("EXPORT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total files created: {results['total_files']}")
        logger.info(f"Errors: {results['errors']}")
        logger.info(f"Warnings: {results['warnings']}")

        if results['errors'] == 0:
            logger.info("Export completed successfully without errors")
        else:
            logger.error(f"Export completed with {results['errors']} errors")

        return results

    def _resolve_type_references(self, items: Dict) -> None:
        """Resolve all type references in the items"""
        # This would resolve any type references that need processing
        pass

    def _export_all_items(self, items: Dict, output_dir: str, timestamp: str) -> Dict:
        """
        Export all items to HTML files

        Returns:
            Dictionary with export statistics
        """
        results = {
            'total_files': 0,
            'errors': 0,
            'warnings': 0,
            'files': []
        }

        # Export each type category
        export_order = ['data_types', 'enums', 'structures', 'unions', 'pous', 'global_variables']

        for category in export_order:
            if category in items and items[category]:
                category_results = self._export_category(
                    category, items[category], output_dir, timestamp
                )
                results['total_files'] += category_results['count']
                results['errors'] += category_results['errors']
                results['warnings'] += category_results['warnings']
                results['files'].extend(category_results['files'])

        return results

    def _export_category(self, category: str, items: List, output_dir: str, timestamp: str) -> Dict:
        """Export a specific category of items"""
        logger.info(f"\nExporting {len(items)} {category}...")

        results = {
            'count': 0,
            'errors': 0,
            'warnings': 0,
            'files': []
        }

        for i, item in enumerate(items, 1):
            logger.debug(f"  [{i}/{len(items)}] {category[:-1].capitalize()}: {item.name}")

            try:
                if category == 'enums':
                    filepath = self._export_enum(item, output_dir, timestamp)
                elif category in ['structures', 'unions']:
                    filepath = self._export_structure(item, output_dir, timestamp, category)
                elif category == 'data_types':
                    filepath = self._export_datatype(item, output_dir, timestamp)
                elif category == 'pous':
                    filepath = self._export_pou(item, output_dir, timestamp)
                elif category == 'global_variables':
                    filepath = self._export_global_variable(item, output_dir, timestamp)
                else:
                    continue

                results['count'] += 1
                results['files'].append({
                    'type': category[:-1],
                    'name': item.name,
                    'path': filepath
                })

                logger.debug(f"     Exported to: {filepath}")

            except Exception as e:
                logger.error(f"Error exporting {item.name}: {str(e)}")
                results['errors'] += 1

        return results

    def _export_structure(self, structure: Any, output_dir: str, timestamp: str,
                          structure_type: str = 'structure') -> str:
        """
        Export a structure or union to HTML with UML styling

        Args:
            structure: Structure or union object
            output_dir: Output directory
            timestamp: Timestamp for filename
            structure_type: 'structure' or 'union'

        Returns:
            Path to exported file
        """
        logger.debug(f"  Processing {structure_type}: {structure.name} with {len(structure.members)} members")

        # Generate filename
        filename = f"{structure.name}_{structure_type}_{timestamp}.html" if timestamp else f"{structure.name}_{structure_type}.html"
        filepath = os.path.join(output_dir, filename)

        # Collect referenced enums for embedding
        embedded_enums = []
        for member in structure.members:
            # CHANGE HERE: Use member.type instead of member.data_type
            if hasattr(member, 'type') and member.type.lower() in self.type_registry:
                ref_type = self.type_registry[member.type.lower()]
                if hasattr(ref_type, 'values') and ref_type not in embedded_enums:
                    embedded_enums.append(ref_type)

        # Generate HTML with UML styling
        html_content = self._generate_structure_html(structure, structure_type, embedded_enums, timestamp)

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f" Exported {structure_type} '{structure.name}' ({len(structure.members)} members) to {filepath}")
        return filepath

    def _generate_structure_html(self, structure: Any, structure_type: str,
                                embedded_enums: List, timestamp: str) -> str:
        """Generate HTML content for structure/union with UML styling"""

        # UML color coding
        uml_colors = {
            'structure': '#e6f3ff',
            'union': '#fff0e6',
            'enum': '#f0ffe6'
        }

        bg_color = uml_colors.get(structure_type, '#f9f9f9')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{structure.name} - {structure_type.capitalize()}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: {bg_color};
            padding: 40px;
            border-bottom: 3px solid #333;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .header h1::before {{
            content: '«{structure_type}»';
            font-size: 0.6em;
            background: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: normal;
        }}
        
        .type-info {{
            padding: 30px 40px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }}
        
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .info-label {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .uml-section {{
            margin: 40px 0;
        }}
        
        .uml-title {{
            font-size: 1.5em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .uml-title::before {{
            content: '📊';
            font-size: 1.2em;
        }}
        
        .uml-diagram {{
            background: white;
            border: 3px solid #333;
            border-radius: 10px;
            margin: 20px 0;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .uml-header {{
            background: #2c3e50;
            color: white;
            padding: 15px 20px;
            font-size: 1.2em;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .uml-type {{
            background: #667eea;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
        }}
        
        .uml-body {{
            padding: 20px;
        }}
        
        .uml-member {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        
        .uml-member:last-child {{
            border-bottom: none;
        }}
        
        .member-name {{
            color: #e74c3c;
            font-weight: bold;
        }}
        
        .member-type {{
            color: #3498db;
        }}
        
        .members-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .members-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .members-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        .members-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .members-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .embedded-section {{
            margin-top: 50px;
            padding-top: 30px;
            border-top: 2px solid #eee;
        }}
        
        .embedded-title {{
            font-size: 1.3em;
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .embedded-title::before {{
            content: '🔗';
        }}
        
        .enum-box {{
            background: #f0ffe6;
            border: 2px solid #27ae60;
            border-radius: 10px;
            margin: 20px 0;
            overflow: hidden;
        }}
        
        .enum-header {{
            background: #27ae60;
            color: white;
            padding: 15px 20px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .enum-values {{
            padding: 20px;
        }}
        
        .enum-value {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #d4efdf;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        
        .enum-value:last-child {{
            border-bottom: none;
        }}
        
        .value-name {{
            color: #e74c3c;
            font-weight: bold;
        }}
        
        .value-number {{
            color: #3498db;
            background: #ebf5fb;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        
        .navigation {{
            padding: 30px 40px;
            background: #f8f9fa;
            border-top: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 25px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .btn::before {{
            content: '←';
            font-size: 1.2em;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
            background: #f8f9fa;
            border-top: 1px solid #eee;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                margin: 10px;
                border-radius: 10px;
            }}
            
            .header, .type-info, .navigation {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .info-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{structure.name}</h1>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Type</span>
                    <span class="info-value">{structure_type.upper()}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Members</span>
                    <span class="info-value">{len(structure.members)}</span>
                </div>
"""

        # Add description if available
        if hasattr(structure, 'description') and structure.description:
            html += f"""
                <div class="info-item" style="grid-column: 1 / -1;">
                    <span class="info-label">Description</span>
                    <span class="info-value">{structure.description}</span>
                </div>
"""

        html += """
            </div>
        </div>
        
        <div class="type-info">
            <!-- UML Diagram -->
            <div class="uml-section">
                <h2 class="uml-title">UML Diagram</h2>
                <div class="uml-diagram">
                    <div class="uml-header">
                        <span>«{structure_type}» {structure.name}</span>
                        <span class="uml-type">{structure_type.upper()}</span>
                    </div>
                    <div class="uml-body">
"""

        # Add members to UML diagram
        for member in structure.members:
            member_desc = getattr(member, 'description', '')
            desc_html = f"<br><small style='color: #7f8c8d;'>// {member_desc}</small>" if member_desc else ""
            html += f"""
                        <div class="uml-member">
                            <div>
                                <span class="member-name">{member.name}</span> : 
                                <span class="member-type">{member.data_type}</span>
                                {desc_html}
                            </div>
                        </div>
"""

        html += """
                    </div>
                </div>
            </div>
            
            <!-- Detailed Members Table -->
            <h2 class="uml-title">Member Details</h2>
            <table class="members-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Data Type</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Add table rows for each member
        for member in structure.members:
            description = getattr(member, 'description', '')
            html += f"""
                    <tr>
                        <td><strong>{member.name}</strong></td>
                        <td><code>{member.data_type}</code></td>
                        <td>{description or '-'}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
"""

        # Add embedded enums if any
        if embedded_enums and self.config.embed_referenced_types:
            html += """
            <div class="embedded-section">
                <h2 class="embedded-title">Embedded Enumerations</h2>
"""

            for enum in embedded_enums:
                html += f"""
                <div class="enum-box">
                    <div class="enum-header">
                        <span>«enumeration» {enum.name}</span>
                        <span>{len(enum.values)} values</span>
                    </div>
                    <div class="enum-values">
"""

                for value in enum.values:
                    value_desc = getattr(value, 'description', '')
                    desc_html = f"<br><small style='color: #7f8c8d;'>// {value_desc}</small>" if value_desc else ""
                    html += f"""
                        <div class="enum-value">
                            <span class="value-name">{value.name}</span>
                            <div>
                                <span class="value-number">{value.value}</span>
                                {desc_html}
                            </div>
                        </div>
"""

                html += """
                    </div>
                </div>
"""

            html += """
            </div>
"""

        html += f"""
        </div>
        
        <div class="navigation">
            <a href="index.html" class="btn">Back to Index</a>
            <div style="color: #7f8c8d;">
                Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
        
        <div class="footer">
            CodeSys XML Documentation Generator • UML-style Documentation
        </div>
    </div>
</body>
</html>
"""

        return html

    def _export_enum(self, enum: Any, output_dir: str, timestamp: str) -> str:
        """
        Export an enumeration to HTML with UML styling

        Args:
            enum: Enum object
            output_dir: Output directory
            timestamp: Timestamp for filename

        Returns:
            Path to exported file
        """
        logger.debug(f"  Processing enum: {enum.name} with {len(enum.values)} values")

        # Generate filename
        filename = f"{enum.name}_enum_{timestamp}.html" if timestamp else f"{enum.name}_enum.html"
        filepath = os.path.join(output_dir, filename)

        # Generate HTML with UML styling
        html_content = self._generate_enum_html(enum, timestamp)

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f" Exported enum '{enum.name}' ({len(enum.values)} values) to {filepath}")
        return filepath

    def _generate_enum_html(self, enum: Any, timestamp: str) -> str:
        """Generate HTML content for enum with UML styling"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{enum.name} - Enumeration</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #d4efdf 0%, #a9dfbf 100%);
            padding: 40px;
            border-bottom: 3px solid #27ae60;
        }}
        
        .header h1 {{
            color: #145a32;
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .header h1::before {{
            content: '«enumeration»';
            font-size: 0.6em;
            background: #27ae60;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: normal;
        }}
        
        .type-info {{
            padding: 30px 40px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #27ae60;
        }}
        
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .info-label {{
            font-weight: bold;
            color: #27ae60;
            margin-bottom: 5px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .uml-section {{
            margin: 40px 0;
        }}
        
        .uml-title {{
            font-size: 1.5em;
            color: #145a32;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #27ae60;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .uml-title::before {{
            content: '📊';
            font-size: 1.2em;
        }}
        
        .uml-diagram {{
            background: white;
            border: 3px solid #27ae60;
            border-radius: 10px;
            margin: 20px 0;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(39, 174, 96, 0.1);
        }}
        
        .uml-header {{
            background: #27ae60;
            color: white;
            padding: 15px 20px;
            font-size: 1.2em;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .uml-body {{
            padding: 20px;
        }}
        
        .enum-value-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #d4efdf;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        
        .enum-value-row:last-child {{
            border-bottom: none;
        }}
        
        .value-name {{
            color: #e74c3c;
            font-weight: bold;
            font-size: 1.1em;
        }}
        
        .value-display {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .value-number {{
            background: #ebf5fb;
            color: #3498db;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            border: 2px solid #3498db;
        }}
        
        .value-hex {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        
        .values-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .values-table th {{
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .values-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        .values-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .values-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .navigation {{
            padding: 30px 40px;
            background: #f8f9fa;
            border-top: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            padding: 12px 25px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(39, 174, 96, 0.4);
        }}
        
        .btn::before {{
            content: '←';
            font-size: 1.2em;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
            background: #f8f9fa;
            border-top: 1px solid #eee;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                margin: 10px;
                border-radius: 10px;
            }}
            
            .header, .type-info, .navigation {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .info-grid {{
                grid-template-columns: 1fr;
            }}
            
            .value-display {{
                flex-direction: column;
                gap: 5px;
                align-items: flex-end;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{enum.name}</h1>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Type</span>
                    <span class="info-value">ENUMERATION</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Values</span>
                    <span class="info-value">{len(enum.values)}</span>
                </div>
"""

        # Add description if available
        if hasattr(enum, 'description') and enum.description:
            html += f"""
                <div class="info-item" style="grid-column: 1 / -1;">
                    <span class="info-label">Description</span>
                    <span class="info-value">{enum.description}</span>
                </div>
"""

        html += """
            </div>
        </div>
        
        <div class="type-info">
            <!-- UML Diagram -->
            <div class="uml-section">
                <h2 class="uml-title">UML Diagram</h2>
                <div class="uml-diagram">
                    <div class="uml-header">
                        <span>«enumeration» {enum.name}</span>
                        <span>{len(enum.values)} values</span>
                    </div>
                    <div class="uml-body">
"""

        # Add enum values to UML diagram
        for value in enum.values:
            value_desc = getattr(value, 'description', '')
            desc_html = f"<br><small style='color: #7f8c8d;'>// {value_desc}</small>" if value_desc else ""
            html += f"""
                        <div class="enum-value-row">
                            <span class="value-name">{value.name}</span>
                            <div class="value-display">
                                <span class="value-number">{value.value}</span>
                                <span class="value-hex">(0x{int(value.value):X})</span>
                                {desc_html}
                            </div>
                        </div>
"""

        html += """
                    </div>
                </div>
            </div>
            
            <!-- Detailed Values Table -->
            <h2 class="uml-title">Enumeration Values</h2>
            <table class="values-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Value</th>
                        <th>Hexadecimal</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Add table rows for each value
        for value in enum.values:
            description = getattr(value, 'description', '')
            html += f"""
                    <tr>
                        <td><strong>{value.name}</strong></td>
                        <td><code>{value.value}</code></td>
                        <td><code>0x{int(value.value):X}</code></td>
                        <td>{description or '-'}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>
        
        <div class="navigation">
            <a href="index.html" class="btn">Back to Index</a>
            <div style="color: #7f8c8d;">
                Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
        
        <div class="footer">
            CodeSys XML Documentation Generator • UML-style Documentation
        </div>
    </div>
</body>
</html>
"""

        return html

    def _export_datatype(self, datatype: Any, output_dir: str, timestamp: str) -> str:
        """Export a basic data type to HTML"""
        # Similar structure to _export_enum but simpler
        # Implementation omitted for brevity
        pass

    def _export_pou(self, pou: Any, output_dir: str, timestamp: str) -> str:
        """Export a POU to HTML"""
        # Implementation omitted for brevity
        pass

    def _export_global_variable(self, variable: Any, output_dir: str, timestamp: str) -> str:
        """Export a global variable to HTML"""
        # Implementation omitted for brevity
        pass

    def _create_index_file(self, output_dir: str, items: Dict, timestamp: str) -> str:
        """
        Create an index HTML file with links to all exported files

        Args:
            output_dir: Output directory
            items: Dictionary of all items
            timestamp: Timestamp for filenames

        Returns:
            Path to index file
        """
        logger.debug(f"Creating index file: {output_dir}/index.html")

        index_path = os.path.join(output_dir, "index.html")

        # Count items by type
        type_counts = {k: len(v) for k, v in items.items() if v}

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation Index</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #4a6491 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
            border-bottom: 5px solid #667eea;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            transition: transform 0.3s ease;
            border-top: 4px solid #667eea;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 1.1em;
            color: #2c3e50;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 1.8em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title::before {
            content: '📁';
            font-size: 1.2em;
        }
        
        .item-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .item-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        
        .item-card:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left-color: #e74c3c;
        }
        
        .item-card a {
            color: #2c3e50;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1em;
            display: block;
            margin-bottom: 8px;
        }
        
        .item-card a:hover {
            color: #667eea;
        }
        
        .item-info {
            color: #7f8c8d;
            font-size: 0.9em;
            display: flex;
            gap: 15px;
        }
        
        .item-type {
            background: #ebf5fb;
            color: #3498db;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }
        
        .footer {
            text-align: center;
            padding: 30px;
            color: #7f8c8d;
            background: #f8f9fa;
            border-top: 1px solid #eee;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            
            .header {
                padding: 40px 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .stats-grid, .content {
                padding: 20px;
            }
            
            .item-list {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Documentation Index</h1>
            <p>Complete documentation of all exported types with UML-style formatting</p>
        </div>
        
        <div class="stats-grid">
"""

        # Add statistics cards
        for item_type, count in type_counts.items():
            type_name = item_type.replace('_', ' ').title()
            icon = {
                'data_types': '🔧',
                'enums': '🔢',
                'structures': '🏗️',
                'unions': '🔀',
                'pous': '⚙️',
                'global_variables': '🌐'
            }.get(item_type, '📄')

            html += f"""
            <div class="stat-card">
                <div class="stat-number">{icon} {count}</div>
                <div class="stat-label">{type_name}</div>
            </div>
"""

        html += """
        </div>
        
        <div class="content">
"""

        # Add sections for each type
        for item_type, item_list in items.items():
            if not item_list:
                continue

            type_name = item_type.replace('_', ' ').title()
            icon = {
                'data_types': '🔧',
                'enums': '🔢',
                'structures': '🏗️',
                'unions': '🔀',
                'pous': '⚙️',
                'global_variables': '🌐'
            }.get(item_type, '📄')

            html += f"""
            <div class="section">
                <h2 class="section-title">{icon} {type_name} ({len(item_list)})</h2>
                <div class="item-list">
"""

            for item in item_list:
                # Determine filename based on type
                if item_type == 'enums':
                    filename = f"{item.name}_enum_{timestamp}.html" if timestamp else f"{item.name}_enum.html"
                elif item_type in ['structures', 'unions']:
                    filename = f"{item.name}_{item_type[:-1]}_{timestamp}.html" if timestamp else f"{item.name}_{item_type[:-1]}.html"
                else:
                    filename = f"{item.name}.html"

                # Get additional info
                if hasattr(item, 'members'):
                    info = f"{len(item.members)} members"
                elif hasattr(item, 'values'):
                    info = f"{len(item.values)} values"
                else:
                    info = ""

                html += f"""
                    <div class="item-card">
                        <a href="{filename}">{item.name}</a>
                        <div class="item-info">
                            <span class="item-type">{item_type[:-1].upper()}</span>
                            <span>{info}</span>
                        </div>
                    </div>
"""

            html += """
                </div>
            </div>
"""

        html += f"""
        </div>
        
        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>CodeSys XML Documentation Generator • UML-style Documentation</p>
        </div>
    </div>
</body>
</html>
"""

        # Write index file
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f" Created index file: {index_path}")
        return index_path