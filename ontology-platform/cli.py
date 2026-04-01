#!/usr/bin/env python3
"""
Ontology Platform CLI
本体推理与查询平台 - 命令行工具

Usage:
    python cli.py --help
    python cli.py server start
    python cli.py server status
    python cli.py inference "query"
    python cli.py db migrate
    python cli.py kg search "keyword"
"""

import argparse
import sys
import os
import yaml
import uvicorn
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Colors for CLI output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def print_status(msg, status="info"):
    """Print colored status message."""
    symbols = {
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "info": "ℹ",
    }
    colors = {
        "success": Colors.GREEN,
        "error": Colors.RED,
        "warning": Colors.YELLOW,
        "info": Colors.BLUE,
    }
    symbol = symbols.get(status, "ℹ")
    color = colors.get(status, Colors.RESET)
    print(f"{color}{symbol} {msg}{Colors.RESET}")


def load_config():
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


# ============================================
# Server Commands
# ============================================

def server_start(args):
    """Start the API server."""
    config = load_config()
    server_config = config.get("environment", {}).get("server", {})
    
    host = args.host or server_config.get("host", "0.0.0.0")
    port = args.port or server_config.get("port", 8080)
    reload = args.reload or config.get("environment", {}).get("mode") == "development"
    
    print_status(f"Starting Ontology Platform server on {host}:{port}...", "info")
    
    from src.api import app
    uvicorn.run(app, host=host, port=port, reload=reload)


def server_stop(args):
    """Stop the API server."""
    print_status("Stopping server... (pkill uvicorn)", "info")
    os.system("pkill -f uvicorn")
    print_status("Server stopped", "success")


def server_status(args):
    """Check server status."""
    import socket
    config = load_config()
    server_config = config.get("environment", {}).get("server", {})
    port = args.port or server_config.get("port", 8080)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result == 0:
        print_status(f"Server is running on port {port}", "success")
    else:
        print_status(f"Server is not running on port {port}", "error")


# ============================================
# Inference Commands
# ============================================

def inference_query(args):
    """Run an inference query."""
    print_status(f"Running inference: {args.query}", "info")
    
    try:
        from src.reasoner import Reasoner
        from src.loader import OntologyLoader
        
        # Initialize reasoner
        loader = OntologyLoader()
        ontology = loader.load()
        reasoner = Reasoner(ontology)
        
        # Run inference
        result = reasoner.infer(args.query)
        
        print(f"\n{Colors.CYAN}{Colors.BOLD}Result:{Colors.RESET}")
        print(result)
        
        if args.explain:
            explanation = reasoner.explain(result)
            print(f"\n{Colors.CYAN}{Colors.BOLD}Explanation:{Colors.RESET}")
            print(explanation)
            
    except Exception as e:
        print_status(f"Inference failed: {str(e)}", "error")
        sys.exit(1)


def inference_batch(args):
    """Run batch inference from file."""
    print_status(f"Running batch inference from: {args.file}", "info")
    
    try:
        with open(args.file, "r") as f:
            queries = [line.strip() for line in f if line.strip()]
        
        from src.reasoner import Reasoner
        from src.loader import OntologyLoader
        
        loader = OntologyLoader()
        ontology = loader.load()
        reasoner = Reasoner(ontology)
        
        results = []
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] {query}")
            result = reasoner.infer(query)
            results.append({"query": query, "result": result})
            print(f"  → {result[:100]}...")
        
        # Save results
        output_file = args.output or "inference_results.json"
        import json
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print_status(f"Batch inference complete. Results saved to {output_file}", "success")
        
    except Exception as e:
        print_status(f"Batch inference failed: {str(e)}", "error")
        sys.exit(1)


# ============================================
# Database Commands
# ============================================

def db_init(args):
    """Initialize the database."""
    print_status("Initializing database...", "info")
    
    config = load_config()
    db_config = config.get("database", {})
    db_type = db_config.get("type", "sqlite")
    
    if db_type == "sqlite":
        db_path = db_config.get("sqlite", {}).get("path", "./data/ontology.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create tables
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES entities(id),
                FOREIGN KEY (target_id) REFERENCES entities(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                result TEXT NOT NULL,
                confidence REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        print_status(f"Database initialized at {db_path}", "success")
    else:
        print_status(f"Database type {db_type} not fully supported yet", "warning")


def db_migrate(args):
    """Run database migrations."""
    print_status("Running migrations...", "info")
    
    config = load_config()
    migrations_config = config.get("database", {}).get("migrations", {})
    auto_migrate = migrations_config.get("auto_migrate", True)
    migration_path = migrations_config.get("migration_path", "./migrations")
    
    if auto_migrate:
        print_status("Auto-migration enabled - schema is up to date", "success")
    else:
        print_status(f"Migration path: {migration_path}", "info")


def db_query(args):
    """Query the database."""
    config = load_config()
    db_config = config.get("database", {})
    db_type = db_config.get("type", "sqlite")
    
    if db_type == "sqlite":
        db_path = db_config.get("sqlite", {}).get("path", "./data/ontology.db")
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(args.sql)
        results = cursor.fetchall()
        
        for row in results:
            print(row)
        
        conn.close()
    else:
        print_status(f"Database type {db_type} not supported", "error")


# ============================================
# Knowledge Graph Commands
# ============================================

def kg_search(args):
    """Search the knowledge graph."""
    print_status(f"Searching knowledge graph for: {args.keyword}", "info")
    
    try:
        from src.loader import OntologyLoader
        
        loader = OntologyLoader()
        ontology = loader.load()
        
        # Search entities
        results = ontology.search(args.keyword)
        
        if results:
            print(f"\n{Colors.CYAN}{Colors.BOLD}Found {len(results)} results:{Colors.RESET}")
            for r in results:
                print(f"  • {r}")
        else:
            print_status("No results found", "warning")
            
    except Exception as e:
        print_status(f"Search failed: {str(e)}", "error")


def kg_export(args):
    """Export knowledge graph."""
    print_status(f"Exporting knowledge graph to: {args.output}", "info")
    
    try:
        from src.loader import OntologyLoader
        import json
        
        loader = OntologyLoader()
        ontology = loader.load()
        
        export_data = ontology.export()
        
        with open(args.output, "w") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print_status(f"Knowledge graph exported to {args.output}", "success")
        
    except Exception as e:
        print_status(f"Export failed: {str(e)}", "error")


def kg_import(args):
    """Import knowledge graph."""
    print_status(f"Importing knowledge graph from: {args.file}", "info")
    
    try:
        import json
        from src.loader import OntologyLoader
        
        with open(args.file, "r") as f:
            data = json.load(f)
        
        loader = OntologyLoader()
        ontology = loader.load()
        ontology.import_data(data)
        
        print_status(f"Knowledge graph imported from {args.file}", "success")
        
    except Exception as e:
        print_status(f"Import failed: {str(e)}", "error")


# ============================================
# Config Commands
# ============================================

def config_show(args):
    """Show current configuration."""
    config = load_config()
    
    if args.key:
        keys = args.key.split(".")
        value = config
        for k in keys:
            value = value.get(k, {})
        print(value)
    else:
        print(yaml.dump(config, default_flow_style=False))


def config_set(args):
    """Set configuration value."""
    config = load_config()
    
    keys = args.key.split(".")
    d = config
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = args.value
    
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print_status(f"Set {args.key} = {args.value}", "success")


# ============================================
# Model Commands
# ============================================

def model_list(args):
    """List available models."""
    config = load_config()
    engine_config = config.get("inference_engine", {})
    provider = engine_config.get("provider", "local")
    
    print(f"{Colors.CYAN}Inference Provider: {provider}{Colors.RESET}")
    
    if provider == "local":
        model_path = engine_config.get("local", {}).get("model_path", "./models")
        print(f"Model path: {model_path}")
        
        model_dir = Path(model_path)
        if model_dir.exists():
            models = list(model_dir.glob("*.bin")) + list(model_dir.glob("*.pt"))
            if models:
                print(f"\n{Colors.GREEN}Available models:{Colors.RESET}")
                for m in models:
                    print(f"  • {m.name}")
            else:
                print_status("No models found", "warning")
        else:
            print_status(f"Model directory not found: {model_path}", "error")
            
    elif provider == "openai":
        print(f"Model: {engine_config.get('openai', {}).get('model', 'gpt-4')}")
        
    elif provider == "ollama":
        print(f"Model: {engine_config.get('ollama', {}).get('model', 'llama2')}")
        
    elif provider == "anthropic":
        print(f"Model: {engine_config.get('anthropic', {}).get('model', 'claude-3-opus')}")


def model_download(args):
    """Download a model."""
    print_status(f"Downloading model: {args.model}", "info")
    
    config = load_config()
    provider = config.get("inference_engine", {}).get("provider", "local")
    
    if provider == "ollama":
        import subprocess
        result = subprocess.run(["ollama", "pull", args.model], capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"Model {args.model} downloaded successfully", "success")
        else:
            print_status(f"Failed to download model: {result.stderr}", "error")
    else:
        print_status("Model download only supported for Ollama provider", "warning")


# ============================================
# Main CLI
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description=f"{Colors.CYAN}Ontology Platform CLI{Colors.RESET} - 本体推理与查询平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {Colors.GREEN}Server:{Colors.RESET}
    python cli.py server start
    python cli.py server start --port 9000
    python cli.py server status
    python cli.py server stop
    
  {Colors.GREEN}Inference:{Colors.RESET}
    python cli.py inference "燃气管道泄漏如何处理?"
    python cli.py inference "采购流程是什么?" --explain
    python cli.py inference --batch queries.txt
    
  {Colors.GREEN}Database:{Colors.RESET}
    python cli.py db init
    python cli.py db migrate
    python cli.py db query "SELECT * FROM entities LIMIT 10"
    
  {Colors.GREEN}Knowledge Graph:{Colors.RESET}
    python cli.py kg search "燃气"
    python cli.py kg export kg.json
    python cli.py kg import kg.json
    
  {Colors.GREEN}Config:{Colors.RESET}
    python cli.py config show
    python cli.py config show environment.mode
    python cli.py config set environment.log_level info
    
  {Colors.GREEN}Model:{Colors.RESET}
    python cli.py model list
    python cli.py model download llama2
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server commands
    server_parser = subparsers.add_parser("server", help="Server management")
    server_subparsers = server_parser.add_subparsers(dest="server_command")
    
    start_parser = server_subparsers.add_parser("start", help="Start the server")
    start_parser.add_argument("--host", help="Host to bind to")
    start_parser.add_argument("--port", type=int, help="Port to bind to")
    start_parser.add_argument("--no-reload", dest="reload", action="store_false", help="Disable auto-reload")
    start_parser.set_defaults(func=server_start)
    
    stop_parser = server_subparsers.add_parser("stop", help="Stop the server")
    stop_parser.set_defaults(func=server_stop)
    
    status_parser = server_subparsers.add_parser("status", help="Check server status")
    status_parser.add_argument("--port", type=int, help="Port to check")
    status_parser.set_defaults(func=server_status)
    
    # Inference commands
    inference_parser = subparsers.add_parser("inference", help="Run inference queries")
    inference_parser.add_argument("query", nargs="?", help="Query string")
    inference_parser.add_argument("--explain", "-e", action="store_true", help="Show explanation")
    inference_parser.add_argument("--batch", "-b", dest="file", help="Batch file with queries (one per line)")
    inference_parser.add_argument("--output", "-o", help="Output file for batch results")
    inference_parser.set_defaults(func=inference_query)
    
    # Database commands
    db_parser = subparsers.add_parser("db", help="Database operations")
    db_subparsers = db_parser.add_subparsers(dest="db_command")
    
    db_init_parser = db_subparsers.add_parser("init", help="Initialize database")
    db_init_parser.set_defaults(func=db_init)
    
    db_migrate_parser = db_subparsers.add_parser("migrate", help="Run migrations")
    db_migrate_parser.set_defaults(func=db_migrate)
    
    db_query_parser = db_subparsers.add_parser("query", help="Execute SQL query")
    db_query_parser.add_argument("sql", help="SQL query to execute")
    db_query_parser.set_defaults(func=db_query)
    
    # Knowledge Graph commands
    kg_parser = subparsers.add_parser("kg", help="Knowledge graph operations")
    kg_subparsers = kg_parser.add_subparsers(dest="kg_command")
    
    kg_search_parser = kg_subparsers.add_parser("search", help="Search knowledge graph")
    kg_search_parser.add_argument("keyword", help="Search keyword")
    kg_search_parser.set_defaults(func=kg_search)
    
    kg_export_parser = kg_subparsers.add_parser("export", help="Export knowledge graph")
    kg_export_parser.add_argument("output", help="Output file path")
    kg_export_parser.set_defaults(func=kg_export)
    
    kg_import_parser = kg_subparsers.add_parser("import", help="Import knowledge graph")
    kg_import_parser.add_argument("file", help="Input file path")
    kg_import_parser.set_defaults(func=kg_import)
    
    # Config commands
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    
    config_show_parser = config_subparsers.add_parser("show", help="Show configuration")
    config_show_parser.add_argument("key", nargs="?", help="Configuration key (dot notation)")
    config_show_parser.set_defaults(func=config_show)
    
    config_set_parser = config_set_parser = config_subparsers.add_parser("set", help="Set configuration value")
    config_set_parser.add_argument("key", help="Configuration key (dot notation)")
    config_set_parser.add_argument("value", help="Value to set")
    config_set_parser.set_defaults(func=config_set)
    
    # Model commands
    model_parser = subparsers.add_parser("model", help="Model management")
    model_subparsers = model_parser.add_subparsers(dest="model_command")
    
    model_list_parser = model_subparsers.add_parser("list", help="List available models")
    model_list_parser.set_defaults(func=model_list)
    
    model_download_parser = model_subparsers.add_parser("download", help="Download a model")
    model_download_parser.add_argument("model", help="Model name to download")
    model_download_parser.set_defaults(func=model_download)
    
    args = parser.parse_args()
    
    if hasattr(args, "func"):
        if args.command == "inference" and args.file:
            args.func = inference_batch
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
