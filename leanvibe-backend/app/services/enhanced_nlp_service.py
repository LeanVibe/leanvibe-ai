"""
Enhanced Natural Language Processing Service for LeanVibe

Provides intelligent voice command interpretation with context awareness,
intent recognition, parameter extraction, and fuzzy matching capabilities
beyond simple string matching.

This service enhances the natural language processing capabilities for:
- Voice command interpretation
- Intent recognition from natural speech
- Parameter extraction from commands
- Context-aware command processing
- Flexible command vocabulary with fuzzy matching
"""

import re
import difflib
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


class CommandIntent(Enum):
    """Available command intents for voice command processing"""
    SYSTEM_STATUS = "system_status"
    FILE_OPERATIONS = "file_operations"
    PROJECT_NAVIGATION = "project_navigation"
    CODE_ANALYSIS = "code_analysis"
    TASK_MANAGEMENT = "task_management"
    HELP = "help"
    VOICE_CONTROL = "voice_control"
    UNKNOWN = "unknown"


@dataclass
class CommandParameter:
    """Extracted parameter from natural language command"""
    name: str
    value: str
    type: str  # 'file', 'directory', 'text', 'number', 'boolean'
    confidence: float
    original_text: str = ""


@dataclass
class NLPCommand:
    """Processed natural language command with structured information"""
    intent: CommandIntent
    action: str
    parameters: List[CommandParameter]
    confidence: float
    original_text: str
    canonical_form: str
    processing_time: float = 0.0
    context_used: bool = False


class EnhancedNLPService:
    """
    Enhanced Natural Language Processing service for intelligent voice command processing
    
    Features:
    - Intent recognition with fuzzy matching
    - Parameter extraction with type inference
    - Context awareness and command history
    - Flexible vocabulary handling
    - Performance optimization with caching
    """

    def __init__(self):
        self.intent_patterns = self._build_intent_patterns()
        self.action_mappings = self._build_action_mappings()
        self.parameter_extractors = self._build_parameter_extractors()
        self.context_history: List[NLPCommand] = []
        self.command_cache: Dict[str, NLPCommand] = {}
        self.is_initialized = True
        self._performance_stats = {
            "total_processed": 0,
            "cache_hits": 0,
            "avg_processing_time": 0.0
        }

    def process_command(self, text: str, context: Optional[Dict] = None) -> NLPCommand:
        """
        Process natural language command into structured format with enhanced capabilities
        
        Args:
            text: Natural language command text
            context: Optional context information (current directory, project, etc.)
            
        Returns:
            NLPCommand with intent, action, parameters, and confidence
        """
        start_time = time.time()
        request_id = f"nlp_{int(time.time())}_{hash(text) % 10000:04d}"
        
        try:
            # Check cache first for performance optimization
            cache_key = self._generate_cache_key(text, context)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self._performance_stats["cache_hits"] += 1
                cached_result.processing_time = time.time() - start_time
                return cached_result

            logger.debug(f"[{request_id}] Processing command: '{text[:50]}...'")
            
            # Normalize input text for better processing
            normalized_text = self._normalize_text(text)
            
            # Recognize intent with confidence scoring
            intent, intent_confidence = self._recognize_intent(normalized_text, context)
            
            # Extract specific action within the recognized intent
            action, action_confidence = self._extract_action(normalized_text, intent)
            
            # Extract parameters from the command text
            parameters = self._extract_parameters(normalized_text, intent, action, context)
            
            # Calculate overall confidence based on components
            overall_confidence = self._calculate_overall_confidence(
                intent_confidence, action_confidence, parameters
            )
            
            # Create canonical form for the command
            canonical_form = self._create_canonical_form(intent, action, parameters)
            
            # Build the processed command
            processing_time = time.time() - start_time
            command = NLPCommand(
                intent=intent,
                action=action,
                parameters=parameters,
                confidence=overall_confidence,
                original_text=text,
                canonical_form=canonical_form,
                processing_time=processing_time,
                context_used=context is not None
            )
            
            # Update context history and cache results
            self._update_context_history(command)
            self._cache_result(cache_key, command)
            
            # Update performance statistics
            self._update_performance_stats(processing_time)
            
            logger.info(
                f"[{request_id}] NLP processing complete | "
                f"intent={intent.value} | action={action} | "
                f"confidence={overall_confidence:.2f} | "
                f"params={len(parameters)} | time={processing_time:.3f}s"
            )
            
            return command
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"[{request_id}] NLP processing failed: {e}")
            
            # Return fallback command
            return NLPCommand(
                intent=CommandIntent.UNKNOWN,
                action="unknown",
                parameters=[],
                confidence=0.0,
                original_text=text,
                canonical_form="unknown.unknown",
                processing_time=processing_time,
                context_used=False
            )

    def _normalize_text(self, text: str) -> str:
        """Normalize input text for better processing"""
        # Convert to lowercase and strip whitespace
        text = text.lower().strip()
        
        # Remove common filler words that don't add meaning
        filler_words = {
            'please', 'could', 'you', 'can', 'would', 'like', 'to', 
            'the', 'a', 'an', 'and', 'or', 'but', 'so'
        }
        words = text.split()
        words = [w for w in words if w not in filler_words]
        
        # Handle common speech-to-text substitutions
        substitutions = {
            'show me': 'show',
            'give me': 'show',
            'tell me': 'show',
            'let me see': 'show',
            'what is': 'show',
            'what are': 'list',
            'how many': 'count',
            'go to': 'navigate',
            'move to': 'navigate',
            'switch to': 'change',
            'open up': 'open',
            'look at': 'analyze',
            'check out': 'analyze',
        }
        
        text = ' '.join(words)
        for old, new in substitutions.items():
            text = text.replace(old, new)
            
        return text.strip()

    def _recognize_intent(self, text: str, context: Optional[Dict] = None) -> Tuple[CommandIntent, float]:
        """Recognize intent from normalized text with context awareness"""
        best_intent = CommandIntent.UNKNOWN
        best_confidence = 0.0
        intent_scores = {}
        
        # Define intent priority order (more specific intents first)
        intent_priority = [
            CommandIntent.VOICE_CONTROL,
            CommandIntent.TASK_MANAGEMENT,
            CommandIntent.CODE_ANALYSIS,
            CommandIntent.PROJECT_NAVIGATION,
            CommandIntent.FILE_OPERATIONS,
            CommandIntent.SYSTEM_STATUS,
            CommandIntent.HELP,
        ]
        
        # Check each intent pattern and accumulate scores
        for intent in intent_priority:
            patterns = self.intent_patterns[intent]
            intent_confidence = 0.0
            pattern_matches = 0
            specific_matches = 0
            
            for pattern in patterns:
                if isinstance(pattern, str):
                    # Exact substring match - prefer specific keywords
                    if pattern in text:
                        # Multi-word patterns are more specific
                        word_count = len(pattern.split())
                        if word_count >= 2:
                            # Multi-word patterns get high confidence
                            intent_confidence = max(intent_confidence, 0.85 + (word_count * 0.05))
                            specific_matches += 1
                        else:
                            # Single word patterns get lower confidence
                            intent_confidence = max(intent_confidence, 0.6)
                        pattern_matches += 1
                elif hasattr(pattern, 'search'):
                    # Regex pattern match
                    match = pattern.search(text)
                    if match:
                        intent_confidence = max(intent_confidence, 0.8)
                        specific_matches += 1
                        pattern_matches += 1
            
            # Boost confidence for multiple specific pattern matches
            if specific_matches > 1:
                intent_confidence = min(1.0, intent_confidence + (specific_matches - 1) * 0.1)
            
            intent_scores[intent] = (intent_confidence, pattern_matches, specific_matches)
        
        # Find best intent prioritizing specific matches and higher confidence
        for intent in intent_priority:  # Check in priority order
            if intent in intent_scores:
                confidence, matches, specific = intent_scores[intent]
                
                # Prioritize intents with specific multi-word matches
                if specific > 0 and confidence > 0.8:
                    best_intent = intent
                    best_confidence = confidence
                    break
                elif confidence > best_confidence:
                    best_intent = intent
                    best_confidence = confidence
        
        # Apply context boost if available
        if context and self._intent_matches_context(best_intent, context):
            best_confidence = min(1.0, best_confidence * 1.15)  # 15% boost for context relevance

        # Fuzzy matching fallback for better coverage
        if best_confidence < 0.5:
            fuzzy_intent, fuzzy_confidence = self._fuzzy_intent_match(text)
            if fuzzy_confidence > best_confidence:
                best_intent = fuzzy_intent
                best_confidence = fuzzy_confidence
                
        return best_intent, best_confidence

    def _extract_action(self, text: str, intent: CommandIntent) -> Tuple[str, float]:
        """Extract specific action within intent category"""
        if intent not in self.action_mappings:
            return "unknown", 0.0
            
        actions = self.action_mappings[intent]
        best_action = "unknown"
        best_confidence = 0.0
        
        for action, keywords in actions.items():
            action_confidence = 0.0
            
            for keyword in keywords:
                if keyword in text:
                    # Calculate confidence based on keyword specificity
                    keyword_confidence = min(1.0, len(keyword) / 10.0)  # Longer keywords = higher confidence
                    action_confidence = max(action_confidence, keyword_confidence)
            
            if action_confidence > best_confidence:
                best_action = action
                best_confidence = action_confidence
                
        # Minimum confidence threshold
        if best_confidence < 0.3:
            best_action = "default"
            best_confidence = 0.5
                
        return best_action, best_confidence

    def _extract_parameters(
        self, text: str, intent: CommandIntent, action: str, context: Optional[Dict] = None
    ) -> List[CommandParameter]:
        """Extract parameters from command text with type inference"""
        parameters = []
        
        if intent in self.parameter_extractors:
            extractors = self.parameter_extractors[intent]
            
            for param_name, extractor in extractors.items():
                try:
                    extracted = extractor(text, context)
                    if extracted:
                        parameters.extend(extracted)
                except Exception as e:
                    logger.warning(f"Parameter extraction failed for {param_name}: {e}")
        
        # Enhance parameters with context information
        for param in parameters:
            param.confidence = min(1.0, param.confidence)
            
        return parameters

    def _calculate_overall_confidence(
        self, intent_confidence: float, action_confidence: float, parameters: List[CommandParameter]
    ) -> float:
        """Calculate overall command confidence from component scores"""
        # Base confidence from intent and action
        base_confidence = (intent_confidence * 0.6) + (action_confidence * 0.4)
        
        # Parameter confidence boost
        if parameters:
            param_confidence = sum(p.confidence for p in parameters) / len(parameters)
            parameter_boost = param_confidence * 0.2
            base_confidence = min(1.0, base_confidence + parameter_boost)
        
        # Context history boost for consistent patterns
        if self.context_history:
            recent_commands = self.context_history[-3:]  # Last 3 commands
            pattern_consistency = self._calculate_pattern_consistency(recent_commands)
            base_confidence = min(1.0, base_confidence + (pattern_consistency * 0.1))
        
        return round(base_confidence, 2)

    def _build_intent_patterns(self) -> Dict[CommandIntent, List]:
        """Build patterns for intent recognition with comprehensive coverage"""
        return {
            CommandIntent.SYSTEM_STATUS: [
                'status', 'health', 'running', 'working', 'alive',
                'up', 'operational', 'available',
                re.compile(r'how.*doing'),
                re.compile(r'what.*status'),
                re.compile(r'is.*running'),
                re.compile(r'are.*you.*working'),
                re.compile(r'system.*check'),
            ],
            CommandIntent.FILE_OPERATIONS: [
                'file', 'files', 'directory', 'folder', 'document',
                'list files', 'show files', 'open file', 'read file',
                'create file', 'make file', 'new file', 'delete file', 'remove file',
                re.compile(r'show.*files?'),
                re.compile(r'list.*files?'),
                re.compile(r'what.*files?'),
                re.compile(r'open.*file'),
                re.compile(r'read.*file'),
                re.compile(r'create.*file'),
                re.compile(r'new.*file'),
                re.compile(r'delete.*file'),
            ],
            CommandIntent.PROJECT_NAVIGATION: [
                'navigate', 'go to directory', 'switch directory', 'change directory',
                'current directory', 'working directory', 'location', 'path',
                'go to project', 'navigate to project', 'navigate to folder',
                re.compile(r'where.*am.*i'),
                re.compile(r'current.*directory'),
                re.compile(r'change.*directory'),
                re.compile(r'navigate.*to'),
                re.compile(r'go.*to.*(?:directory|folder|project)'),
                re.compile(r'switch.*directory'),
                re.compile(r'show.*current.*location'),
            ],
            CommandIntent.CODE_ANALYSIS: [
                'analyze code', 'code analysis', 'review code', 'check code', 'examine code',
                'analyze function', 'review function', 'explain function',
                'find bug', 'find error', 'find issue', 'code problem',
                re.compile(r'analyze.*code'),
                re.compile(r'analyze.*file'),
                re.compile(r'review.*code'),
                re.compile(r'review.*function'),
                re.compile(r'what.*does.*function'),
                re.compile(r'explain.*code'),
                re.compile(r'find.*bug'),
                re.compile(r'check.*for.*bugs'),
            ],
            CommandIntent.TASK_MANAGEMENT: [
                'task', 'tasks', 'todo', 'work item',
                'create task', 'add task', 'new task', 
                'update task', 'modify task',
                'complete', 'done', 'finish', 'mark',
                re.compile(r'add.*task'),
                re.compile(r'create.*task'),
                re.compile(r'new.*task'),
                re.compile(r'mark.*complete'),
                re.compile(r'update.*task'),
                re.compile(r'finish.*task'),
                re.compile(r'task.*\w+'),  # Any task-related command
            ],
            CommandIntent.VOICE_CONTROL: [
                'voice control', 'speech recognition', 'voice command',
                'volume', 'change volume', 'set volume', 'mute voice', 'unmute voice',
                'activate voice', 'deactivate voice', 'voice feedback',
                re.compile(r'voice.*control'),
                re.compile(r'speech.*recognition'),
                re.compile(r'change.*volume'),
                re.compile(r'set.*volume'),
                re.compile(r'volume.*\d+'),
                re.compile(r'mute.*voice'),
                re.compile(r'activate.*voice'),
                re.compile(r'listen.*to.*me'),
            ],
            CommandIntent.HELP: [
                'help', 'help me', 'need help', 'assistance', 
                'what can you do', 'show commands', 'available commands',
                'how do i use', 'how to use', 'usage', 'instructions',
                re.compile(r'what.*can.*do'),
                re.compile(r'what.*can.*you.*do'),
                re.compile(r'help.*me'),
                re.compile(r'need.*help'),
                re.compile(r'need.*assistance'),
                re.compile(r'show.*commands'),
                re.compile(r'available.*commands'),
                re.compile(r'how.*do.*i.*use'),
            ]
        }

    def _build_action_mappings(self) -> Dict[CommandIntent, Dict[str, List[str]]]:
        """Build action mappings for each intent with comprehensive actions"""
        return {
            CommandIntent.SYSTEM_STATUS: {
                'health': ['health', 'status', 'running', 'operational', 'alive'],
                'version': ['version', 'build', 'release'],
                'uptime': ['uptime', 'how long', 'running time'],
                'performance': ['performance', 'speed', 'fast', 'slow'],
                'memory': ['memory', 'ram', 'usage'],
                'default': ['check', 'show', 'display']
            },
            CommandIntent.FILE_OPERATIONS: {
                'list': ['list', 'show', 'display', 'directory'],
                'open': ['open', 'read', 'view', 'access'],
                'create': ['create', 'new', 'make', 'generate'],
                'delete': ['delete', 'remove', 'rm', 'trash'],
                'copy': ['copy', 'duplicate', 'clone'],
                'move': ['move', 'relocate', 'transfer'],
                'search': ['search', 'find', 'locate'],
                'default': ['file', 'files']
            },
            CommandIntent.PROJECT_NAVIGATION: {
                'current': ['current', 'where', 'pwd', 'location'],
                'change': ['change', 'go to', 'cd', 'navigate', 'switch'],
                'up': ['up', 'parent', 'back', 'previous'],
                'home': ['home', 'root', 'base', 'main'],
                'list': ['list', 'show', 'contents'],
                'default': ['navigate', 'directory']
            },
            CommandIntent.CODE_ANALYSIS: {
                'analyze_file': ['analyze', 'review', 'check', 'examine'],
                'explain_function': ['explain', 'what does', 'describe'],
                'find_issues': ['issues', 'problems', 'bugs', 'errors'],
                'suggestions': ['suggest', 'improve', 'optimize', 'enhance'],
                'complexity': ['complexity', 'metrics', 'quality'],
                'dependencies': ['dependencies', 'imports', 'requires'],
                'default': ['code', 'analysis']
            },
            CommandIntent.TASK_MANAGEMENT: {
                'list': ['list', 'show', 'display', 'view'],
                'create': ['create', 'add', 'new', 'make'],
                'update': ['update', 'modify', 'change', 'edit'],
                'complete': ['complete', 'done', 'finish', 'mark'],
                'delete': ['delete', 'remove', 'cancel'],
                'assign': ['assign', 'delegate', 'give'],
                'priority': ['priority', 'urgent', 'important'],
                'default': ['task', 'tasks']
            },
            CommandIntent.VOICE_CONTROL: {
                'activate': ['activate', 'start', 'begin', 'turn on'],
                'deactivate': ['deactivate', 'stop', 'end', 'turn off'],
                'volume': ['volume', 'loud', 'quiet', 'mute'],
                'recognition': ['recognition', 'listen', 'hear'],
                'commands': ['commands', 'available', 'what can'],
                'default': ['voice', 'speech']
            },
            CommandIntent.HELP: {
                'commands': ['commands', 'available', 'options'],
                'usage': ['usage', 'how to', 'instructions'],
                'guide': ['guide', 'manual', 'tutorial'],
                'examples': ['examples', 'samples', 'demos'],
                'default': ['help', 'assistance']
            }
        }

    def _build_parameter_extractors(self) -> Dict[CommandIntent, Dict[str, callable]]:
        """Build parameter extractors for each intent category"""
        return {
            CommandIntent.FILE_OPERATIONS: {
                'filename': self._extract_filename,
                'directory': self._extract_directory,
                'extension': self._extract_file_extension,
            },
            CommandIntent.PROJECT_NAVIGATION: {
                'path': self._extract_path,
                'directory': self._extract_directory,
            },
            CommandIntent.CODE_ANALYSIS: {
                'filename': self._extract_filename,
                'function_name': self._extract_function_name,
                'class_name': self._extract_class_name,
                'language': self._extract_language,
            },
            CommandIntent.TASK_MANAGEMENT: {
                'task_text': self._extract_task_text,
                'task_id': self._extract_task_id,
                'priority': self._extract_priority,
                'assignee': self._extract_assignee,
            },
            CommandIntent.VOICE_CONTROL: {
                'volume_level': self._extract_volume_level,
                'command_name': self._extract_command_name,
            }
        }

    # Parameter extraction methods with enhanced capabilities
    def _extract_filename(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract filename parameters with enhanced pattern matching"""
        parameters = []
        
        # Multiple filename patterns
        patterns = [
            re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z]{1,4})'),  # filename.ext
            re.compile(r'"([^"]+\.[a-zA-Z]{1,4})"'),  # "filename.ext"
            re.compile(r"'([^']+\.[a-zA-Z]{1,4})'"),  # 'filename.ext'
            re.compile(r'file\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z]{1,4})'),  # file filename.ext
        ]
        
        for pattern in patterns:
            matches = pattern.findall(text)
            for match in matches:
                parameters.append(CommandParameter(
                    name='filename',
                    value=match,
                    type='file',
                    confidence=0.85,
                    original_text=match
                ))
        
        # Context-based filename extraction
        if context and 'current_file' in context:
            if 'this file' in text or 'current file' in text:
                parameters.append(CommandParameter(
                    name='filename',
                    value=context['current_file'],
                    type='file',
                    confidence=0.9,
                    original_text='current file'
                ))
        
        return parameters

    def _extract_directory(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract directory parameters with path validation"""
        parameters = []
        
        patterns = [
            re.compile(r'/[a-zA-Z0-9_/.-]+'),  # Unix paths
            re.compile(r'[a-zA-Z]:\\[a-zA-Z0-9_\\.-]+'),  # Windows paths
            re.compile(r'directory\s+([a-zA-Z0-9_/.\\-]+)'),  # directory path
            re.compile(r'folder\s+([a-zA-Z0-9_/.\\-]+)'),  # folder path
        ]
        
        for pattern in patterns:
            matches = pattern.findall(text)
            for match in matches:
                parameters.append(CommandParameter(
                    name='directory',
                    value=match,
                    type='directory',
                    confidence=0.75,
                    original_text=match
                ))
        
        return parameters

    def _extract_file_extension(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract file extension parameters"""
        parameters = []
        
        # Common file extensions
        extension_pattern = re.compile(r'\.([a-zA-Z]{1,4})\b')
        matches = extension_pattern.findall(text)
        
        for match in matches:
            parameters.append(CommandParameter(
                name='extension',
                value=f'.{match}',
                type='text',
                confidence=0.8,
                original_text=f'.{match}'
            ))
        
        return parameters

    def _extract_path(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract path parameters (reuse directory extraction)"""
        return self._extract_directory(text, context)

    def _extract_function_name(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract function name parameters"""
        parameters = []
        
        patterns = [
            re.compile(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)'),
            re.compile(r'method\s+([a-zA-Z_][a-zA-Z0-9_]*)'),
            re.compile(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'),
        ]
        
        for pattern in patterns:
            matches = pattern.findall(text)
            for match in matches:
                parameters.append(CommandParameter(
                    name='function_name',
                    value=match,
                    type='text',
                    confidence=0.9,
                    original_text=match
                ))
        
        return parameters

    def _extract_class_name(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract class name parameters"""
        parameters = []
        
        patterns = [
            re.compile(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'),
            re.compile(r'object\s+([a-zA-Z_][a-zA-Z0-9_]*)'),
        ]
        
        for pattern in patterns:
            matches = pattern.findall(text)
            for match in matches:
                parameters.append(CommandParameter(
                    name='class_name',
                    value=match,
                    type='text',
                    confidence=0.9,
                    original_text=match
                ))
        
        return parameters

    def _extract_language(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract programming language parameters"""
        parameters = []
        
        languages = {
            'python': ['python', 'py'],
            'javascript': ['javascript', 'js', 'node'],
            'typescript': ['typescript', 'ts'],
            'swift': ['swift', 'ios'],
            'java': ['java'],
            'go': ['go', 'golang'],
            'rust': ['rust', 'rs'],
            'c++': ['cpp', 'c++', 'cxx'],
            'c#': ['csharp', 'c#'],
        }
        
        for language, keywords in languages.items():
            for keyword in keywords:
                if keyword in text.lower():
                    parameters.append(CommandParameter(
                        name='language',
                        value=language,
                        type='text',
                        confidence=0.8,
                        original_text=keyword
                    ))
                    break
        
        return parameters

    def _extract_task_text(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract task description text with enhanced parsing"""
        parameters = []
        
        patterns = [
            re.compile(r'(?:create|add|new)\s+(?:task\s+)?["\']([^"\']+)["\']'),
            re.compile(r'(?:create|add|new)\s+(?:task\s+)?(?:called\s+)?(.+?)(?:\s+(?:with|for|in)|$)'),
            re.compile(r'task\s+["\']([^"\']+)["\']'),
        ]
        
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                task_text = match.group(1).strip()
                if len(task_text) > 3:  # Minimum meaningful task length
                    parameters.append(CommandParameter(
                        name='task_text',
                        value=task_text,
                        type='text',
                        confidence=0.85,
                        original_text=task_text
                    ))
                    break
        
        return parameters

    def _extract_task_id(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract task ID parameters"""
        parameters = []
        
        patterns = [
            re.compile(r'(?:task|id)\s+(\d+)'),
            re.compile(r'#(\d+)'),
            re.compile(r'task\s+number\s+(\d+)'),
        ]
        
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                parameters.append(CommandParameter(
                    name='task_id',
                    value=match.group(1),
                    type='number',
                    confidence=0.95,
                    original_text=match.group(0)
                ))
        
        return parameters

    def _extract_priority(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract priority parameters"""
        parameters = []
        
        priority_mappings = {
            'urgent': ['urgent', 'critical', 'asap', 'immediately'],
            'high': ['high', 'important', 'priority'],
            'medium': ['medium', 'normal', 'regular'],
            'low': ['low', 'minor', 'whenever', 'later'],
        }
        
        for priority, keywords in priority_mappings.items():
            for keyword in keywords:
                if keyword in text.lower():
                    parameters.append(CommandParameter(
                        name='priority',
                        value=priority,
                        type='text',
                        confidence=0.8,
                        original_text=keyword
                    ))
                    return parameters  # Return first match
        
        return parameters

    def _extract_assignee(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract assignee parameters"""
        parameters = []
        
        patterns = [
            re.compile(r'assign\s+to\s+([a-zA-Z_][a-zA-Z0-9_]*)'),
            re.compile(r'for\s+([a-zA-Z_][a-zA-Z0-9_]*)'),
            re.compile(r'@([a-zA-Z_][a-zA-Z0-9_]*)'),
        ]
        
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                parameters.append(CommandParameter(
                    name='assignee',
                    value=match.group(1),
                    type='text',
                    confidence=0.85,
                    original_text=match.group(0)
                ))
        
        return parameters

    def _extract_volume_level(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract volume level parameters"""
        parameters = []
        
        # Volume level patterns
        if 'mute' in text or 'silent' in text:
            parameters.append(CommandParameter(
                name='volume_level',
                value='0',
                type='number',
                confidence=0.9,
                original_text='mute'
            ))
        elif 'loud' in text or 'max' in text or 'maximum' in text:
            parameters.append(CommandParameter(
                name='volume_level',
                value='100',
                type='number',
                confidence=0.8,
                original_text='loud'
            ))
        elif 'quiet' in text or 'low' in text:
            parameters.append(CommandParameter(
                name='volume_level',
                value='25',
                type='number',
                confidence=0.8,
                original_text='quiet'
            ))
        
        # Numeric volume levels
        volume_pattern = re.compile(r'volume\s+(\d+)')
        match = volume_pattern.search(text)
        if match:
            volume = int(match.group(1))
            if 0 <= volume <= 100:
                parameters.append(CommandParameter(
                    name='volume_level',
                    value=str(volume),
                    type='number',
                    confidence=0.95,
                    original_text=match.group(0)
                ))
        
        return parameters

    def _extract_command_name(self, text: str, context: Optional[Dict] = None) -> List[CommandParameter]:
        """Extract command name parameters"""
        parameters = []
        
        # Look for command patterns
        command_pattern = re.compile(r'command\s+([a-zA-Z_][a-zA-Z0-9_]*)')
        match = command_pattern.search(text)
        if match:
            parameters.append(CommandParameter(
                name='command_name',
                value=match.group(1),
                type='text',
                confidence=0.9,
                original_text=match.group(0)
            ))
        
        return parameters

    def _fuzzy_intent_match(self, text: str) -> Tuple[CommandIntent, float]:
        """Fallback fuzzy matching for intent recognition"""
        intent_keywords = {
            CommandIntent.SYSTEM_STATUS: 'system status health running working operational alive',
            CommandIntent.FILE_OPERATIONS: 'file files directory folder document list show open create',
            CommandIntent.PROJECT_NAVIGATION: 'project navigate directory current location path switch',
            CommandIntent.CODE_ANALYSIS: 'analyze code review function class method bug error examine',
            CommandIntent.TASK_MANAGEMENT: 'task tasks todo create add complete done finish work',
            CommandIntent.VOICE_CONTROL: 'voice speech listen hear speak volume mute command activate',
            CommandIntent.HELP: 'help commands what can how to usage guide manual instructions',
        }
        
        best_intent = CommandIntent.UNKNOWN
        best_ratio = 0.0
        
        for intent, keywords in intent_keywords.items():
            # Calculate similarity ratio
            ratio = difflib.SequenceMatcher(None, text, keywords).ratio()
            
            # Also check individual keyword matches
            keyword_matches = sum(1 for keyword in keywords.split() if keyword in text)
            keyword_ratio = keyword_matches / len(keywords.split()) if keywords.split() else 0
            
            # Combined score with weighted importance
            combined_ratio = (ratio * 0.4) + (keyword_ratio * 0.6)
            
            if combined_ratio > best_ratio:
                best_intent = intent
                best_ratio = combined_ratio
        
        # Only return if confidence is reasonable
        confidence = best_ratio if best_ratio > 0.3 else 0.0
        return best_intent, confidence

    def _intent_matches_context(self, intent: CommandIntent, context: Dict[str, Any]) -> bool:
        """Check if intent matches provided context for confidence boosting"""
        if 'current_file' in context:
            if intent == CommandIntent.FILE_OPERATIONS:
                return True
                
        if 'current_directory' in context:
            if intent in [CommandIntent.PROJECT_NAVIGATION, CommandIntent.FILE_OPERATIONS]:
                return True
                
        if 'task_context' in context:
            if intent == CommandIntent.TASK_MANAGEMENT:
                return True
                
        if 'voice_active' in context and context['voice_active']:
            if intent == CommandIntent.VOICE_CONTROL:
                return True
        
        return False

    def _create_canonical_form(self, intent: CommandIntent, action: str, parameters: List[CommandParameter]) -> str:
        """Create canonical form of the command for consistency"""
        param_str = ""
        if parameters:
            param_values = [f"{p.name}={p.value}" for p in parameters]
            param_str = f"({', '.join(param_values)})"
            
        return f"{intent.value}.{action}{param_str}"

    def _update_context_history(self, command: NLPCommand):
        """Update context history for pattern learning"""
        self.context_history.append(command)
        
        # Keep only last 20 commands for memory efficiency
        if len(self.context_history) > 20:
            self.context_history = self.context_history[-20:]

    def _calculate_pattern_consistency(self, recent_commands: List[NLPCommand]) -> float:
        """Calculate pattern consistency from recent commands"""
        if len(recent_commands) < 2:
            return 0.0
            
        # Check for intent consistency
        intents = [cmd.intent for cmd in recent_commands]
        most_common_intent = max(set(intents), key=intents.count)
        intent_consistency = intents.count(most_common_intent) / len(intents)
        
        return intent_consistency * 0.5  # Moderate boost for consistency

    def _generate_cache_key(self, text: str, context: Optional[Dict] = None) -> str:
        """Generate cache key for performance optimization"""
        import hashlib
        
        # Create hash of text and relevant context
        key_components = [text.lower().strip()]
        
        if context:
            # Add relevant context elements
            for key in ['current_file', 'current_directory', 'task_context']:
                if key in context:
                    key_components.append(f"{key}:{context[key]}")
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[NLPCommand]:
        """Get cached result if available and fresh"""
        if cache_key in self.command_cache:
            cached_command = self.command_cache[cache_key]
            # Simple cache without expiration for now
            return cached_command
        return None

    def _cache_result(self, cache_key: str, command: NLPCommand):
        """Cache successful command processing results"""
        if command.confidence > 0.7:  # Only cache high-confidence results
            # Limit cache size
            if len(self.command_cache) >= 100:
                # Remove oldest entries (simple FIFO)
                oldest_key = next(iter(self.command_cache))
                del self.command_cache[oldest_key]
            
            self.command_cache[cache_key] = command

    def _update_performance_stats(self, processing_time: float):
        """Update performance statistics"""
        self._performance_stats["total_processed"] += 1
        
        # Update running average
        total = self._performance_stats["total_processed"]
        current_avg = self._performance_stats["avg_processing_time"]
        self._performance_stats["avg_processing_time"] = (
            (current_avg * (total - 1) + processing_time) / total
        )

    def get_command_suggestions(self, partial_text: str, limit: int = 5) -> List[str]:
        """Get command suggestions for partial input with enhanced matching"""
        suggestions = []
        
        # Common command patterns categorized by intent
        common_commands = {
            'system': [
                "show system status",
                "check health", 
                "what's the system status",
                "is everything running"
            ],
            'files': [
                "list files",
                "show current directory",
                "open file",
                "create new file",
                "read file"
            ],
            'navigation': [
                "go to directory",
                "navigate to project", 
                "change directory",
                "show current location"
            ],
            'code': [
                "analyze code",
                "review this file",
                "explain function",
                "find issues",
                "check code quality"
            ],
            'tasks': [
                "create task",
                "list tasks",
                "mark task complete",
                "add new task",
                "show my tasks"
            ],
            'voice': [
                "activate voice control",
                "change volume",
                "mute voice",
                "voice commands available"
            ],
            'help': [
                "help me",
                "what can you do",
                "show available commands",
                "how to use"
            ]
        }
        
        partial_lower = partial_text.lower()
        scored_suggestions = []
        
        # Score suggestions based on relevance
        for category, commands in common_commands.items():
            for command in commands:
                # Calculate relevance score
                if partial_lower in command.lower():
                    # Exact substring match gets highest score
                    score = 1.0
                elif any(word in command.lower() for word in partial_lower.split()):
                    # Word match gets medium score
                    score = 0.7
                else:
                    # Use fuzzy matching for partial matches
                    score = difflib.SequenceMatcher(None, partial_lower, command.lower()).ratio()
                
                if score > 0.3:  # Minimum relevance threshold
                    scored_suggestions.append((command, score))
        
        # Sort by score and return top suggestions
        scored_suggestions.sort(key=lambda x: x[1], reverse=True)
        suggestions = [cmd for cmd, score in scored_suggestions[:limit]]
        
        # If no good suggestions, provide category-based suggestions
        if not suggestions:
            suggestions = [
                "show status",
                "list files",
                "help me",
                "analyze code",
                "create task"
            ][:limit]
        
        return suggestions

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        cache_hit_ratio = 0.0
        if self._performance_stats["total_processed"] > 0:
            cache_hit_ratio = (
                self._performance_stats["cache_hits"] / 
                self._performance_stats["total_processed"]
            ) * 100
        
        return {
            "total_processed": self._performance_stats["total_processed"],
            "cache_hits": self._performance_stats["cache_hits"],
            "cache_hit_ratio": round(cache_hit_ratio, 1),
            "avg_processing_time": round(self._performance_stats["avg_processing_time"], 3),
            "cache_size": len(self.command_cache),
            "history_size": len(self.context_history),
            "supported_intents": len(self.intent_patterns),
            "supported_actions": sum(len(actions) for actions in self.action_mappings.values()),
            "is_initialized": self.is_initialized
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the NLP service"""
        return {
            "status": "healthy" if self.is_initialized else "unhealthy",
            "is_initialized": self.is_initialized,
            "capabilities": {
                "intent_recognition": True,
                "parameter_extraction": True,
                "fuzzy_matching": True,
                "context_awareness": True,
                "performance_caching": True,
                "command_suggestions": True
            },
            "metrics": self.get_performance_metrics()
        }