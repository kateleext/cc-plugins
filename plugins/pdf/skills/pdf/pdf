#!/usr/bin/env python3
"""
PDF Generator MCP Server
Converts markdown content to beautifully styled PDFs for Takuma OS documentation
"""

import os
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
import httpx
import markdown2
from weasyprint import HTML, CSS
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pdf-generator")

# Available built-in styles
BUILTIN_STYLES = {
    "minimal": "Clean, minimalist design focused on readability",
    "corporate": "Professional corporate design with formal structure", 
    "technical": "Developer-friendly documentation style",
    "shokuna": "Minimalist dark mode design",
    "newsletter": "Newsletter/blog style with clean typography"
}

def get_style_css(style_name: str) -> str:
    """Get CSS content for a built-in style"""
    
    if style_name == "minimal":
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
        }
        h1, h2, h3 { 
            margin-top: 24px; 
            margin-bottom: 16px;
            font-weight: 600;
        }
        h1 { font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 8px; }
        h2 { font-size: 1.5em; }
        h3 { font-size: 1.2em; }
        code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        pre {
            background: #f5f5f5;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }
        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 16px;
            color: #666;
            margin: 16px 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background: #f5f5f5;
            font-weight: 600;
        }
        """
    
    elif style_name == "corporate":
        return """
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.8;
            color: #2c3e50;
            max-width: 750px;
            margin: 0 auto;
            padding: 60px;
        }
        h1, h2, h3 {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            color: #1a472a;
            margin-top: 32px;
            margin-bottom: 16px;
        }
        h1 { 
            font-size: 2.4em; 
            border-bottom: 3px solid #1a472a;
            padding-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        h2 { font-size: 1.8em; }
        h3 { font-size: 1.3em; }
        p { text-align: justify; }
        table {
            border: 2px solid #1a472a;
            width: 100%;
            margin: 24px 0;
        }
        th {
            background: #1a472a;
            color: white;
            padding: 12px;
            text-align: left;
        }
        td {
            border: 1px solid #ddd;
            padding: 10px;
        }
        """
    
    elif style_name == "technical":
        return """
        body {
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
            line-height: 1.65;
            color: #24292e;
            max-width: 900px;
            margin: 0 auto;
            padding: 32px;
            background: white;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }
        h1 { 
            font-size: 2em; 
            border-bottom: 1px solid #eaecef;
            padding-bottom: 8px;
        }
        code {
            background-color: rgba(27,31,35,0.05);
            padding: 3px 6px;
            border-radius: 3px;
            font-size: 85%;
        }
        pre {
            background-color: #f6f8fa;
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            border-radius: 6px;
        }
        .note, .warning, .tip {
            padding: 12px;
            border-radius: 6px;
            margin: 16px 0;
        }
        .note {
            background: #d1ecf1;
            border-left: 4px solid #0c5460;
        }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #856404;
        }
        """
    
    elif style_name == "shokuna":
        return """
        @page {
            margin: 0;
            size: A4;
        }
        html, body {
            margin: 0;
            padding: 0;
            background-color: #000000;
            color: #ffffff;
            width: 100%;
            height: 100%;
        }
        body {
            font-family: 'IBM Plex Sans', -apple-system, sans-serif;
            line-height: 1.6;
            padding: 72px;
            box-sizing: border-box;
        }
        h1, h2, h3 {
            font-weight: 400;
            text-transform: lowercase;
            letter-spacing: 0.02em;
            margin-top: 48px;
            margin-bottom: 24px;
        }
        h1 {
            font-size: 2.5em;
            page-break-before: always;
        }
        h1:first-child {
            page-break-before: avoid;
        }
        h2 { font-size: 1.8em; }
        h3 { font-size: 1.3em; }
        p {
            margin-bottom: 16px;
            opacity: 0.9;
        }
        code {
            background: rgba(255,255,255,0.1);
            padding: 2px 6px;
            border-radius: 2px;
            font-family: 'IBM Plex Mono', monospace;
        }
        pre {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 16px;
            border-radius: 4px;
            overflow-x: auto;
        }
        blockquote {
            border-left: 2px solid rgba(255,255,255,0.3);
            padding-left: 16px;
            opacity: 0.8;
            font-style: italic;
        }
        a {
            color: #ffffff;
            text-decoration: underline;
            text-decoration-color: rgba(255,255,255,0.3);
        }
        """
    
    elif style_name == "newsletter":
        return """
        @page {
            margin: 0.75in;
            size: A4;
        }
        body {
            font-family: Georgia, 'Times New Roman', serif;
            font-size: 12pt;
            line-height: 1.8;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        h1 {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 36pt;
            font-weight: 900;
            color: #000000;
            margin-bottom: 10px;
            letter-spacing: -1px;
            line-height: 1.1;
        }
        h1::after {
            content: '';
            display: block;
            width: 80px;
            height: 4px;
            background: #000000;
            margin-top: 20px;
            margin-bottom: 30px;
        }
        h2 {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 24pt;
            font-weight: 700;
            color: #2d3436;
            margin-top: 48px;
            margin-bottom: 20px;
            position: relative;
        }
        h3 {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 16pt;
            font-weight: 600;
            color: #636e72;
            margin-top: 32px;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        p {
            margin-bottom: 24px;
            font-size: 13pt;
        }
        p:first-of-type {
            font-size: 16pt;
            line-height: 1.6;
            color: #636e72;
            font-style: italic;
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid #e0e0e0;
        }
        blockquote {
            border-left: 4px solid #000000;
            padding-left: 24px;
            margin: 32px 0;
            font-size: 15pt;
            font-style: italic;
            color: #636e72;
        }
        strong {
            color: #2d3436;
            background: linear-gradient(to bottom, transparent 60%, #FFE66D 60%);
            padding: 0 2px;
        }
        em {
            color: #000000;
            font-style: italic;
        }
        ul {
            margin: 24px 0;
            padding-left: 0;
            list-style: none;
        }
        ul li {
            position: relative;
            padding-left: 32px;
            margin-bottom: 12px;
            font-size: 13pt;
        }
        ul li::before {
            content: '→';
            position: absolute;
            left: 0;
            color: #000000;
            font-weight: bold;
            font-size: 16pt;
        }
        ol {
            margin: 24px 0;
            padding-left: 32px;
        }
        ol li {
            margin-bottom: 12px;
            font-size: 13pt;
        }
        code {
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            color: #e83e8c;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        pre {
            background: #2d3436;
            color: #dfe6e9;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 11pt;
            line-height: 1.5;
            overflow-x: auto;
            margin: 24px 0;
        }
        table {
            width: 100%;
            margin: 32px 0;
            font-size: 12pt;
        }
        th {
            background: #000000;
            color: white;
            padding: 12px;
            text-align: left;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 11pt;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        tr:nth-child(even) {
            background: #f8f9fa;
        }
        hr {
            border: none;
            height: 1px;
            background: #e0e0e0;
            margin: 40px 0;
        }
        a {
            color: #000000;
            text-decoration: none;
            border-bottom: 2px solid #e0e0e0;
        }
        .footer {
            margin-top: 60px;
            padding-top: 30px;
            border-top: 2px solid #e0e0e0;
            font-size: 11pt;
            color: #636e72;
            text-align: center;
        }
        """
    
    return ""


@mcp.tool()
async def generate_pdf(
    markdown_content: str,
    output_path: str,
    style: str = "minimal",
    custom_css: Optional[str] = None,
    options: Optional[Dict] = None
) -> Dict:
    """
    Generate a PDF from markdown content
    
    Args:
        markdown_content: The markdown text to convert
        output_path: Where to save the PDF file
        style: Built-in style name (minimal, corporate, technical, shokuna)
        custom_css: Optional custom CSS to override styles
        options: Additional PDF options (margins, page_size, orientation)
    
    Returns:
        Dict with success status and file path
    """
    
    try:
        # Convert markdown to HTML
        html_content = markdown2.markdown(
            markdown_content,
            extras=[
                "fenced-code-blocks",
                "tables", 
                "strike",
                "footnotes",
                "smarty-pants",
                "header-ids",
                "code-friendly"
            ]
        )
        
        # Get style CSS
        style_css = get_style_css(style)
        if custom_css:
            style_css += f"\n{custom_css}"
        
        # Build complete HTML document
        html_document = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                {style_css}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Ensure output directory exists
        output_path = Path(output_path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF using weasyprint
        html = HTML(string=html_document, base_url='.')
        
        # Apply CSS and generate PDF
        html.write_pdf(
            str(output_path),
            stylesheets=[CSS(string=style_css)] if style_css else None
        )
        
        return {
            "success": True,
            "message": f"PDF generated successfully",
            "output_path": str(output_path),
            "style_used": style
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate PDF"
        }


@mcp.tool()
async def generate_pdf_from_file(
    markdown_file_path: str,
    output_path: Optional[str] = None,
    style: str = "minimal",
    custom_css_path: Optional[str] = None,
    options: Optional[Dict] = None
) -> Dict:
    """
    Generate a PDF from a markdown file
    
    Args:
        markdown_file_path: Path to the markdown file
        output_path: Where to save the PDF (defaults to same location as .pdf)
        style: Built-in style name
        custom_css_path: Path to custom CSS file
        options: Additional PDF options
    
    Returns:
        Dict with success status and file path
    """
    
    try:
        # Read markdown file
        md_path = Path(markdown_file_path).expanduser().resolve()
        if not md_path.exists():
            return {
                "success": False,
                "error": f"Markdown file not found: {markdown_file_path}"
            }
        
        markdown_content = md_path.read_text(encoding='utf-8')
        
        # Determine output path
        if not output_path:
            output_path = md_path.with_suffix('.pdf')
        else:
            output_path = Path(output_path).expanduser().resolve()
        
        # Read custom CSS if provided
        custom_css = None
        if custom_css_path:
            css_path = Path(custom_css_path).expanduser().resolve()
            if css_path.exists():
                custom_css = css_path.read_text(encoding='utf-8')
        
        # Generate PDF
        result = await generate_pdf(
            markdown_content=markdown_content,
            output_path=str(output_path),
            style=style,
            custom_css=custom_css,
            options=options
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate PDF from file"
        }


@mcp.tool()
async def generate_pdf_from_folder(
    folder_path: str,
    output_path: str,
    style: str = "minimal",
    custom_css_path: Optional[str] = None,
    options: Optional[Dict] = None,
    pattern: str = "*.md"
) -> Dict:
    """
    Generate a single PDF from all markdown files in a folder
    
    Args:
        folder_path: Path to folder containing markdown files
        output_path: Where to save the combined PDF
        style: Built-in style name
        custom_css_path: Path to custom CSS file
        options: Additional PDF options
        pattern: File pattern to match (default: *.md)
    
    Returns:
        Dict with success status, file path, and files processed
    """
    
    try:
        folder = Path(folder_path).expanduser().resolve()
        if not folder.exists() or not folder.is_dir():
            return {
                "success": False,
                "error": f"Folder not found or not a directory: {folder_path}"
            }
        
        # Find all markdown files
        md_files = sorted(folder.glob(pattern))
        if not md_files:
            return {
                "success": False,
                "error": f"No markdown files found in {folder_path} matching {pattern}"
            }
        
        # Combine all markdown content
        combined_content = []
        files_processed = []
        
        for md_file in md_files:
            content = md_file.read_text(encoding='utf-8')
            # Add page break between files
            if combined_content:
                combined_content.append("\n\n<div style='page-break-before: always;'></div>\n\n")
            combined_content.append(content)
            files_processed.append(str(md_file.name))
        
        # Read custom CSS if provided
        custom_css = None
        if custom_css_path:
            css_path = Path(custom_css_path).expanduser().resolve()
            if css_path.exists():
                custom_css = css_path.read_text(encoding='utf-8')
        
        # Generate combined PDF
        result = await generate_pdf(
            markdown_content="\n".join(combined_content),
            output_path=output_path,
            style=style,
            custom_css=custom_css,
            options=options
        )
        
        if result["success"]:
            result["files_processed"] = files_processed
            result["file_count"] = len(files_processed)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate PDF from folder"
        }


@mcp.tool()
async def list_styles() -> Dict:
    """
    List all available built-in PDF styles
    
    Returns:
        Dict with available styles and their descriptions
    """
    
    return {
        "success": True,
        "styles": BUILTIN_STYLES,
        "default": "minimal",
        "message": "Use any of these style names with the generate_pdf tools"
    }


def cli_main():
    """CLI entry point for standalone PDF generation"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="Generate PDFs from markdown content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from inline markdown
  %(prog)s --markdown "# Hello World" --output hello.pdf

  # Generate from a file
  %(prog)s --input document.md --output document.pdf

  # Generate with a specific style
  %(prog)s --input document.md --output document.pdf --style shokuna

  # Process all markdown files in a folder
  %(prog)s --folder ./docs --output combined.pdf --style technical

Available styles:
  minimal    - Clean, minimalist design focused on readability
  corporate  - Professional corporate design with formal structure
  technical  - Developer-friendly documentation style
  shokuna    - Minimalist dark mode design
  newsletter - Newsletter/blog style with clean typography
"""
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--markdown", "-m",
        help="Inline markdown content to convert"
    )
    input_group.add_argument(
        "--input", "-i",
        help="Path to markdown file to convert"
    )
    input_group.add_argument(
        "--folder", "-f",
        help="Path to folder containing markdown files (combines all into one PDF)"
    )
    input_group.add_argument(
        "--list-styles",
        action="store_true",
        help="List available styles and exit"
    )

    # Output options
    parser.add_argument(
        "--output", "-o",
        help="Output PDF path (required unless --list-styles)"
    )

    # Style options
    parser.add_argument(
        "--style", "-s",
        choices=list(BUILTIN_STYLES.keys()),
        default="minimal",
        help="Built-in style to use (default: minimal)"
    )

    parser.add_argument(
        "--css",
        help="Path to custom CSS file for additional styling"
    )

    parser.add_argument(
        "--pattern",
        default="*.md",
        help="File pattern for folder mode (default: *.md)"
    )

    args = parser.parse_args()

    # Handle --list-styles
    if args.list_styles:
        print("Available PDF styles:")
        print("-" * 50)
        for name, description in BUILTIN_STYLES.items():
            print(f"  {name:12} - {description}")
        return 0

    # Require output for markdown and folder modes (input mode defaults to source location)
    if not args.output and (args.markdown or args.folder):
        parser.error("--output is required for --markdown and --folder modes")

    # Run the appropriate async function
    async def run():
        if args.markdown:
            result = await generate_pdf(
                markdown_content=args.markdown,
                output_path=args.output,
                style=args.style,
                custom_css=Path(args.css).read_text() if args.css else None
            )
        elif args.input:
            result = await generate_pdf_from_file(
                markdown_file_path=args.input,
                output_path=args.output,
                style=args.style,
                custom_css_path=args.css
            )
        elif args.folder:
            result = await generate_pdf_from_folder(
                folder_path=args.folder,
                output_path=args.output,
                style=args.style,
                custom_css_path=args.css,
                pattern=args.pattern
            )

        return result

    result = asyncio.run(run())

    if result["success"]:
        print(f"Success: {result['message']}")
        print(f"Output: {result['output_path']}")
        if "files_processed" in result:
            print(f"Files processed ({result['file_count']}):")
            for f in result["files_processed"]:
                print(f"  - {f}")
        return 0
    else:
        print(f"Error: {result.get('error', result.get('message', 'Unknown error'))}")
        return 1


if __name__ == "__main__":
    import sys

    # If called with arguments, run CLI mode
    # If called without arguments, run MCP server
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    else:
        mcp.run()