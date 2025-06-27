"""
Session Manager for L3 Coding Agent

Manages multiple agent sessions, state persistence, and session lifecycle.
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any, List
from pathlib import Path
import json
from dataclasses import asdict

from .enhanced_l3_agent import EnhancedL3CodingAgent as L3CodingAgent, AgentDependencies
from ..services.cache_warming_service import cache_warming_service

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages multiple L3 coding agent sessions
    
    Handles session creation, retrieval, persistence, and cleanup.
    """
    
    def __init__(self, session_storage_path: str = "./.sessions"):
        self.sessions: Dict[str, L3CodingAgent] = {}
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
        self.storage_path = Path(session_storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Session configuration
        self.max_sessions = 10
        self.session_timeout = 3600  # 1 hour
        self.auto_save_interval = 300  # 5 minutes
        
        # Start background tasks
        self._cleanup_task = None
        self._autosave_task = None
    
    async def start(self):
        """Start the session manager"""
        try:
            # Load existing sessions
            await self._load_sessions()
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            self._autosave_task = asyncio.create_task(self._periodic_autosave())
            
            logger.info(f"Session manager started with {len(self.sessions)} sessions")
            
        except Exception as e:
            logger.error(f"Failed to start session manager: {e}")
            raise
    
    async def stop(self):
        """Stop the session manager and save all sessions"""
        try:
            # Cancel background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._autosave_task:
                self._autosave_task.cancel()
            
            # Save all sessions
            await self._save_all_sessions()
            
            logger.info("Session manager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping session manager: {e}")
    
    async def create_session(
        self, 
        client_id: str, 
        workspace_path: str = ".",
        force_new: bool = False
    ) -> L3CodingAgent:
        """Create a new agent session"""
        try:
            # Check if session already exists
            if client_id in self.sessions and not force_new:
                logger.info(f"Returning existing session for client: {client_id}")
                return self.sessions[client_id]
            
            # Check session limits
            if len(self.sessions) >= self.max_sessions:
                await self._cleanup_oldest_session()
            
            # Create dependencies
            dependencies = AgentDependencies(
                workspace_path=workspace_path,
                client_id=client_id,
                session_data={}
            )
            
            # Create new agent
            agent = L3CodingAgent(dependencies)
            success = await agent.initialize()
            
            if not success:
                raise Exception("Failed to initialize agent")
            
            # Store session
            self.sessions[client_id] = agent
            self.session_metadata[client_id] = {
                "created_at": time.time(),
                "last_accessed": time.time(),
                "workspace_path": workspace_path,
                "interaction_count": 0
            }
            
            # Track project access for cache warming
            cache_warming_service.track_project_access(workspace_path, client_id)
            
            logger.info(f"Created new session for client: {client_id}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create session for {client_id}: {e}")
            raise
    
    async def get_session(self, client_id: str) -> Optional[L3CodingAgent]:
        """Get an existing session"""
        try:
            if client_id not in self.sessions:
                logger.warning(f"Session not found for client: {client_id}")
                return None
            
            # Update last accessed time
            self.session_metadata[client_id]["last_accessed"] = time.time()
            
            return self.sessions[client_id]
            
        except Exception as e:
            logger.error(f"Error getting session for {client_id}: {e}")
            return None
    
    async def get_or_create_session(
        self, 
        client_id: str, 
        workspace_path: str = "."
    ) -> L3CodingAgent:
        """Get existing session or create new one"""
        session = await self.get_session(client_id)
        if session is None:
            session = await self.create_session(client_id, workspace_path)
        return session
    
    async def delete_session(self, client_id: str) -> bool:
        """Delete a session"""
        try:
            if client_id not in self.sessions:
                return False
            
            # Track session end for cache warming
            workspace_path = self.session_metadata[client_id].get("workspace_path", ".")
            cache_warming_service.track_session_end(client_id, workspace_path)
            
            # Save session before deletion (for recovery)
            await self._save_session(client_id)
            
            # Remove from memory
            del self.sessions[client_id]
            del self.session_metadata[client_id]
            
            # Remove from disk
            session_file = self.storage_path / f"{client_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            logger.info(f"Deleted session for client: {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session for {client_id}: {e}")
            return False
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        try:
            sessions_info = []
            
            for client_id, metadata in self.session_metadata.items():
                agent = self.sessions.get(client_id)
                
                session_info = {
                    "client_id": client_id,
                    "created_at": metadata["created_at"],
                    "last_accessed": metadata["last_accessed"],
                    "workspace_path": metadata["workspace_path"],
                    "interaction_count": metadata["interaction_count"],
                    "active": agent is not None
                }
                
                if agent:
                    state_summary = agent.get_state_summary()
                    session_info.update({
                        "conversation_length": state_summary["conversation_length"],
                        "average_confidence": state_summary["average_confidence"],
                        "current_task": state_summary["current_task"],
                        "ai_status": state_summary["ai_service_status"]
                    })
                
                sessions_info.append(session_info)
            
            return sessions_info
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    async def process_message(
        self, 
        client_id: str, 
        message: str, 
        workspace_path: str = "."
    ) -> Dict[str, Any]:
        """Process a message through the appropriate agent session"""
        try:
            # Get or create session
            agent = await self.get_or_create_session(client_id, workspace_path)
            
            # Update interaction count
            if client_id in self.session_metadata:
                self.session_metadata[client_id]["interaction_count"] += 1
                self.session_metadata[client_id]["last_accessed"] = time.time()
            
            # Process message
            result = await agent.run(message)
            
            # Add session metadata to response
            result["session_info"] = {
                "client_id": client_id,
                "session_active": True,
                "interaction_count": self.session_metadata[client_id]["interaction_count"]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message for {client_id}: {e}")
            return {
                "status": "error",
                "message": f"Session processing failed: {str(e)}",
                "confidence": 0.0,
                "session_info": {
                    "client_id": client_id,
                    "session_active": False,
                    "error": str(e)
                }
            }
    
    async def _cleanup_oldest_session(self):
        """Remove the oldest inactive session"""
        try:
            if not self.session_metadata:
                return
            
            # Find oldest session by last access time
            oldest_client = min(
                self.session_metadata.keys(),
                key=lambda x: self.session_metadata[x]["last_accessed"]
            )
            
            logger.info(f"Cleaning up oldest session: {oldest_client}")
            await self.delete_session(oldest_client)
            
        except Exception as e:
            logger.error(f"Error cleaning up oldest session: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = time.time()
                expired_sessions = []
                
                for client_id, metadata in self.session_metadata.items():
                    if current_time - metadata["last_accessed"] > self.session_timeout:
                        expired_sessions.append(client_id)
                
                for client_id in expired_sessions:
                    logger.info(f"Cleaning up expired session: {client_id}")
                    await self.delete_session(client_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _periodic_autosave(self):
        """Periodic auto-save of all sessions"""
        while True:
            try:
                await asyncio.sleep(self.auto_save_interval)
                await self._save_all_sessions()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic autosave: {e}")
    
    async def _save_session(self, client_id: str):
        """Save a single session to disk"""
        try:
            if client_id not in self.sessions or client_id not in self.session_metadata:
                return
            
            agent = self.sessions[client_id]
            metadata = self.session_metadata[client_id]
            
            # Prepare session data for serialization
            session_data = {
                "metadata": metadata,
                "state": {
                    "conversation_history": agent.state.conversation_history,
                    "project_context": agent.state.project_context,
                    "confidence_scores": agent.state.confidence_scores,
                    "current_task": agent.state.current_task,
                    "workspace_path": agent.state.workspace_path,
                    "session_id": agent.state.session_id
                },
                "dependencies": asdict(agent.dependencies),
                "saved_at": time.time()
            }
            
            # Write to file
            session_file = self.storage_path / f"{client_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error saving session {client_id}: {e}")
    
    async def _save_all_sessions(self):
        """Save all active sessions to disk"""
        try:
            save_tasks = [
                self._save_session(client_id) 
                for client_id in self.sessions.keys()
            ]
            
            if save_tasks:
                await asyncio.gather(*save_tasks, return_exceptions=True)
                logger.debug(f"Saved {len(save_tasks)} sessions")
            
        except Exception as e:
            logger.error(f"Error saving all sessions: {e}")
    
    async def _load_sessions(self):
        """Load sessions from disk"""
        try:
            if not self.storage_path.exists():
                return
            
            session_files = list(self.storage_path.glob("*.json"))
            
            for session_file in session_files:
                try:
                    client_id = session_file.stem
                    
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    # Check if session is not too old
                    saved_at = session_data.get("saved_at", 0)
                    if time.time() - saved_at > self.session_timeout * 2:
                        logger.info(f"Skipping old session: {client_id}")
                        session_file.unlink()  # Remove old session file
                        continue
                    
                    # Restore metadata
                    self.session_metadata[client_id] = session_data["metadata"]
                    
                    # Note: We don't restore the full agent state immediately
                    # Instead, we'll create it on-demand when the client reconnects
                    logger.info(f"Loaded session metadata for: {client_id}")
                    
                except Exception as e:
                    logger.error(f"Error loading session from {session_file}: {e}")
            
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics"""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() if s]),
            "max_sessions": self.max_sessions,
            "session_timeout": self.session_timeout,
            "storage_path": str(self.storage_path),
            "total_interactions": sum(
                metadata["interaction_count"] 
                for metadata in self.session_metadata.values()
            )
        }