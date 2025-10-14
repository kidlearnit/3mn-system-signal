"""
Workflow Repository Implementations

This module implements concrete workflow repositories for accessing
workflow configurations and data.
"""

from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from .base_repository import WorkflowRepository, RepositoryConfig
from app.db import SessionLocal, init_db
from sqlalchemy import text
from app.services.debug import debug_helper


class DatabaseWorkflowRepository(WorkflowRepository):
    """
    Database implementation of workflow repository.
    
    This repository accesses workflow configurations from the MySQL database.
    """
    
    def __init__(self, config: RepositoryConfig):
        """
        Initialize database workflow repository.
        
        Args:
            config: Repository configuration with connection string
        """
        super().__init__(config)
        
        # Initialize database connection
        if config.connection_string:
            init_db(config.connection_string)
    
    def is_available(self) -> bool:
        """
        Check if database is available.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with SessionLocal() as s:
                s.execute(text("SELECT 1")).fetchone()
            return True
        except Exception as e:
            debug_helper.log_step("Workflow repository database availability check failed", error=e)
            return False
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """
        Get list of active workflows from database.
        
        Returns:
            List of workflow dictionaries
        """
        try:
            with SessionLocal() as s:
                rows = s.execute(text("""
                    SELECT id, name, description, nodes, properties, status, created_at, updated_at
                    FROM workflows
                    WHERE status = 'active'
                    ORDER BY name
                """)).fetchall()
                
                workflows = []
                for row in rows:
                    try:
                        workflows.append({
                            'id': row[0],
                            'name': row[1],
                            'description': row[2],
                            'nodes': json.loads(row[3]) if row[3] else [],
                            'properties': json.loads(row[4]) if row[4] else {},
                            'status': row[5],
                            'created_at': row[6],
                            'updated_at': row[7]
                        })
                    except json.JSONDecodeError as e:
                        debug_helper.log_step(f"Error parsing workflow {row[1]}: {e}")
                        continue
                
                debug_helper.log_step(f"Retrieved {len(workflows)} active workflows from database")
                return workflows
                
        except Exception as e:
            debug_helper.log_step("Error getting active workflows", error=e)
            return []
    
    def get_workflow_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow by name from database.
        
        Args:
            name: Workflow name
            
        Returns:
            Workflow dictionary or None if not found
        """
        try:
            with SessionLocal() as s:
                row = s.execute(text("""
                    SELECT id, name, description, nodes, properties, status, created_at, updated_at
                    FROM workflows
                    WHERE name = :name
                    LIMIT 1
                """), {'name': name}).fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'nodes': json.loads(row[3]) if row[3] else [],
                        'properties': json.loads(row[4]) if row[4] else {},
                        'status': row[5],
                        'created_at': row[6],
                        'updated_at': row[7]
                    }
                else:
                    return None
                    
        except Exception as e:
            debug_helper.log_step(f"Error getting workflow by name: {name}", error=e)
            return None
    
    def get_macd_config_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get MACD configuration for a symbol from workflows.
        
        Args:
            symbol: Symbol ticker
            
        Returns:
            MACD configuration dictionary or None if not found
        """
        try:
            with SessionLocal() as s:
                # Get active workflows with MACD Multi-TF nodes
                rows = s.execute(text("""
                    SELECT name, nodes, properties
                    FROM workflows 
                    WHERE status = 'active'
                    AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
                    ORDER BY name = '25symbols' DESC, name ASC
                """)).fetchall()
                
                # Prioritize '25symbols' workflow
                for name, nodes_json, properties_json in rows:
                    try:
                        nodes = json.loads(nodes_json) if nodes_json else []
                        properties = json.loads(properties_json) if properties_json else {}
                        
                        # Find MACD Multi-TF nodes
                        macd_multi_nodes = [node for node in nodes if node.get('type') == 'macd-multi']
                        
                        for node in macd_multi_nodes:
                            node_id = node['id']
                            node_config = properties.get(node_id, {})
                            
                            # Check if this symbol is in the configuration
                            symbol_thresholds = node_config.get('symbolThresholds', [])
                            for symbol_config in symbol_thresholds:
                                if isinstance(symbol_config, dict) and symbol_config.get('symbol', '').upper() == symbol.upper():
                                    # Merge node config with symbol-specific config
                                    config = dict(node_config)
                                    config.update(symbol_config)
                                    config['__workflow_name'] = name
                                    
                                    debug_helper.log_step(f"Found MACD config for {symbol} in workflow {name}")
                                    return config
                                    
                    except json.JSONDecodeError as e:
                        debug_helper.log_step(f"Error parsing workflow {name}: {e}")
                        continue
                
                debug_helper.log_step(f"No MACD config found for {symbol}")
                return None
                
        except Exception as e:
            debug_helper.log_step(f"Error getting MACD config for {symbol}", error=e)
            return None
    
    def update_workflow(self, workflow_id: int, data: Dict[str, Any]) -> bool:
        """
        Update workflow data in database.
        
        Args:
            workflow_id: Workflow ID
            data: Data to update
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            with SessionLocal() as s:
                # Build update query dynamically
                update_fields = []
                params = {'workflow_id': workflow_id}
                
                if 'name' in data:
                    update_fields.append("name = :name")
                    params['name'] = data['name']
                
                if 'description' in data:
                    update_fields.append("description = :description")
                    params['description'] = data['description']
                
                if 'nodes' in data:
                    update_fields.append("nodes = :nodes")
                    params['nodes'] = json.dumps(data['nodes'])
                
                if 'properties' in data:
                    update_fields.append("properties = :properties")
                    params['properties'] = json.dumps(data['properties'])
                
                if 'status' in data:
                    update_fields.append("status = :status")
                    params['status'] = data['status']
                
                if not update_fields:
                    debug_helper.log_step("No fields to update in workflow")
                    return True
                
                update_fields.append("updated_at = :updated_at")
                params['updated_at'] = datetime.now()
                
                query = f"""
                    UPDATE workflows 
                    SET {', '.join(update_fields)}
                    WHERE id = :workflow_id
                """
                
                result = s.execute(text(query), params)
                s.commit()
                
                if result.rowcount > 0:
                    debug_helper.log_step(f"Updated workflow {workflow_id}")
                    return True
                else:
                    debug_helper.log_step(f"Workflow {workflow_id} not found for update")
                    return False
                    
        except Exception as e:
            debug_helper.log_step(f"Error updating workflow {workflow_id}", error=e)
            return False
    
    def get_workflow_symbols(self, workflow_name: str) -> List[Dict[str, Any]]:
        """
        Get symbols configured in a specific workflow.
        
        Args:
            workflow_name: Workflow name
            
        Returns:
            List of symbol configurations
        """
        try:
            workflow = self.get_workflow_by_name(workflow_name)
            if not workflow:
                return []
            
            symbols = []
            nodes = workflow.get('nodes', [])
            properties = workflow.get('properties', {})
            
            # Find MACD Multi-TF nodes
            macd_multi_nodes = [node for node in nodes if node.get('type') == 'macd-multi']
            
            for node in macd_multi_nodes:
                node_id = node['id']
                node_config = properties.get(node_id, {})
                symbol_thresholds = node_config.get('symbolThresholds', [])
                
                for symbol_config in symbol_thresholds:
                    if isinstance(symbol_config, dict) and symbol_config.get('symbol'):
                        symbols.append({
                            'symbol': symbol_config['symbol'],
                            'exchange': symbol_config.get('exchange', 'NASDAQ'),
                            'sector': symbol_config.get('sector', ''),
                            'active': symbol_config.get('active', True),
                            'thresholds': {k: v for k, v in symbol_config.items() 
                                         if k not in ['symbol', 'exchange', 'sector', 'active']}
                        })
            
            debug_helper.log_step(f"Retrieved {len(symbols)} symbols from workflow {workflow_name}")
            return symbols
            
        except Exception as e:
            debug_helper.log_step(f"Error getting symbols from workflow {workflow_name}", error=e)
            return []
    
    def sync_workflow_symbols_to_database(self, workflow_name: str) -> int:
        """
        Sync symbols from workflow to database.
        
        Args:
            workflow_name: Workflow name
            
        Returns:
            Number of symbols processed
        """
        try:
            symbols = self.get_workflow_symbols(workflow_name)
            if not symbols:
                return 0
            
            processed_count = 0
            
            with SessionLocal() as s:
                for symbol_config in symbols:
                    try:
                        ticker = symbol_config['symbol'].upper()
                        exchange = symbol_config['exchange'].upper()
                        active = 1 if symbol_config.get('active', True) else 0
                        
                        # Check if symbol exists
                        existing = s.execute(text("""
                            SELECT id, active FROM symbols
                            WHERE ticker = :ticker AND exchange = :exchange
                        """), {'ticker': ticker, 'exchange': exchange}).fetchone()
                        
                        if existing:
                            # Update active status
                            s.execute(text("""
                                UPDATE symbols SET active = :active WHERE id = :id
                            """), {'active': active, 'id': existing[0]})
                        else:
                            # Insert new symbol
                            s.execute(text("""
                                INSERT INTO symbols (ticker, exchange, active)
                                VALUES (:ticker, :exchange, :active)
                            """), {'ticker': ticker, 'exchange': exchange, 'active': active})
                        
                        processed_count += 1
                        
                    except Exception as e:
                        debug_helper.log_step(f"Error processing symbol {symbol_config.get('symbol')}: {e}")
                        continue
                
                s.commit()
            
            debug_helper.log_step(f"Synced {processed_count} symbols from workflow {workflow_name}")
            return processed_count
            
        except Exception as e:
            debug_helper.log_step(f"Error syncing symbols from workflow {workflow_name}", error=e)
            return 0
