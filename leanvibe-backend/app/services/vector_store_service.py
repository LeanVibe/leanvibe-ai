import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import ChromaDB, gracefully handle if not available
try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None

# Try to import sentence transformers for production embeddings
try:
    from sentence_transformers import SentenceTransformer
    import torch
    
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    torch = None

logger = logging.getLogger(__name__)


@dataclass
class CodeEmbedding:
    """Represents a code embedding with metadata"""

    id: str
    content: str
    file_path: str
    language: str
    symbol_type: str  # 'function', 'class', 'file', etc.
    symbol_name: str
    start_line: int
    end_line: int
    embedding_version: str = "1.0"
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class SearchResult:
    """Represents a search result from vector database"""

    content: str
    file_path: str
    symbol_name: str
    symbol_type: str
    similarity_score: float
    metadata: Dict[str, Any]


class VectorStoreService:
    """Service for managing code embeddings with ChromaDB"""

    def __init__(self, 
                 db_path: str = ".leanvibe_cache/chroma_db",
                 use_http: bool = False,
                 host: str = "localhost", 
                 port: int = 8000):
        self.db_path = Path(db_path)
        self.use_http = use_http
        self.host = host
        self.port = port
        self.client = None
        self.collection = None
        self.is_initialized = False
        self.chromadb_available = CHROMADB_AVAILABLE
        self.sentence_transformers_available = SENTENCE_TRANSFORMERS_AVAILABLE
        self.collection_name = "code_embeddings"
        
        # Initialize embedding model
        self.embedding_model_name = "all-MiniLM-L6-v2"  # Production model
        self.embedding_model = None
        self.embedding_type = "hash"  # Will be "sentence_transformer" if available

        # Create database directory (only for local mode)
        if not use_http:
            self.db_path.mkdir(parents=True, exist_ok=True)

        # Mock storage for when ChromaDB is not available
        self.mock_embeddings = {}

    async def initialize(self) -> bool:
        """Initialize ChromaDB client and collection"""
        try:
            logger.info(f"Initializing vector store at {self.db_path}")

            # Initialize embedding model first
            await self._initialize_embedding_model()

            if not self.chromadb_available:
                logger.warning("ChromaDB not available - using mock vector store")
                self.is_initialized = True
                return True

            # Initialize ChromaDB client (HTTP or persistent)
            if self.use_http:
                logger.info(f"Connecting to ChromaDB HTTP server at {self.host}:{self.port}")
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                logger.info(f"Using local ChromaDB at {self.db_path}")
                self.client = chromadb.PersistentClient(
                    path=str(self.db_path),
                    settings=Settings(anonymized_telemetry=False, allow_reset=True),
                )

            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Code embeddings for LeanVibe L3 agent"},
                )
                logger.info(f"Created new collection: {self.collection_name}")

            self.is_initialized = True
            logger.info("Vector store initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            # Fall back to mock mode
            self.is_initialized = True
            return True

    async def _initialize_embedding_model(self) -> None:
        """Initialize the embedding model (sentence transformers or fallback to hash)"""
        try:
            if self.sentence_transformers_available:
                logger.info(f"Loading sentence transformer model: {self.embedding_model_name}")
                
                # Check if GPU is available
                device = "cuda" if torch and torch.cuda.is_available() else "cpu"
                logger.info(f"Using device: {device}")
                
                # Load the sentence transformer model
                self.embedding_model = SentenceTransformer(
                    self.embedding_model_name,
                    device=device
                )
                
                self.embedding_type = "sentence_transformer"
                logger.info(f"✅ Sentence transformer model loaded successfully")
                
            else:
                logger.warning("⚠️ Sentence transformers not available - falling back to hash embeddings")
                self.embedding_type = "hash"
                
        except Exception as e:
            logger.error(f"❌ Failed to load sentence transformer model: {e}")
            logger.info("Falling back to hash embeddings")
            self.embedding_type = "hash"
            self.embedding_model = None

    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content to use as embedding ID"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _create_embedding(self, content: str) -> List[float]:
        """Create an embedding using the best available method"""
        try:
            if self.embedding_type == "sentence_transformer" and self.embedding_model:
                # Use sentence transformer for high-quality embeddings
                return self._create_sentence_transformer_embedding(content)
            else:
                # Fall back to hash-based embeddings
                return self._create_hash_embedding(content)
                
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            # Always fall back to hash embeddings if something fails
            return self._create_hash_embedding(content)

    def _create_sentence_transformer_embedding(self, content: str) -> List[float]:
        """Create high-quality embedding using sentence transformers"""
        try:
            # Preprocess content for better code understanding
            processed_content = self._preprocess_code_for_embedding(content)
            
            # Generate embedding
            embedding = self.embedding_model.encode(processed_content, convert_to_tensor=False)
            
            # Convert to list and ensure proper format
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error in sentence transformer embedding: {e}")
            # Fall back to hash embedding
            return self._create_hash_embedding(content)

    def _preprocess_code_for_embedding(self, content: str) -> str:
        """Preprocess code content to improve embedding quality"""
        # Remove excessive whitespace
        content = ' '.join(content.split())
        
        # Limit content length to avoid model limits
        max_length = 512  # Most sentence transformers have ~512 token limits
        if len(content) > max_length:
            content = content[:max_length]
        
        return content

    def _create_hash_embedding(self, content: str) -> List[float]:
        """Create a basic embedding using simple hashing (fallback method)"""
        # Convert content to a simple feature vector
        content_lower = content.lower()

        # Create a basic 384-dimensional vector (common embedding size)
        embedding = [0.0] * 384

        # Fill embedding with simple features
        for i, char in enumerate(content_lower[:384]):
            embedding[i] = (ord(char) / 128.0) - 1.0  # Normalize to [-1, 1]

        # Add some content-based features
        keywords = [
            "function", "class", "import", "def", "const", "let", "var", "struct",
            "async", "await", "return", "if", "else", "for", "while", "try", "catch"
        ]
        for i, keyword in enumerate(keywords):
            if i < len(embedding):
                embedding[i] += (content_lower.count(keyword) / max(len(content), 1)) * 0.5

        # Normalize the vector
        magnitude = sum(x * x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    async def add_code_embedding(self, embedding: CodeEmbedding) -> bool:
        """Add a code embedding to the vector store"""
        if not self.is_initialized:
            logger.error("Vector store not initialized")
            return False

        try:
            # Generate embedding vector
            embedding_vector = self._create_embedding(embedding.content)

            # Prepare metadata
            metadata = {
                "file_path": embedding.file_path,
                "language": embedding.language,
                "symbol_type": embedding.symbol_type,
                "symbol_name": embedding.symbol_name,
                "start_line": embedding.start_line,
                "end_line": embedding.end_line,
                "embedding_version": embedding.embedding_version,
                "created_at": embedding.created_at,
            }

            if self.chromadb_available and self.collection:
                # Add to ChromaDB collection
                self.collection.add(
                    embeddings=[embedding_vector],
                    documents=[embedding.content],
                    metadatas=[metadata],
                    ids=[embedding.id],
                )
            else:
                # Store in mock storage
                self.mock_embeddings[embedding.id] = {
                    "content": embedding.content,
                    "metadata": metadata,
                    "embedding": embedding_vector,
                }

            logger.debug(
                f"Added embedding for {embedding.symbol_name} in {embedding.file_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to add embedding: {e}")
            return False

    async def add_code_embeddings_batch(self, embeddings: List[CodeEmbedding]) -> int:
        """Add multiple code embeddings in batch for better performance"""
        if not self.is_initialized:
            logger.error("Vector store not initialized")
            return 0

        if not embeddings:
            return 0

        try:
            # Generate all embeddings
            embedding_vectors = []
            documents = []
            metadatas = []
            ids = []

            for embedding in embeddings:
                # Generate embedding vector
                embedding_vector = self._create_embedding(embedding.content)
                embedding_vectors.append(embedding_vector)
                documents.append(embedding.content)
                ids.append(embedding.id)

                # Prepare metadata
                metadata = {
                    "file_path": embedding.file_path,
                    "language": embedding.language,
                    "symbol_type": embedding.symbol_type,
                    "symbol_name": embedding.symbol_name,
                    "start_line": embedding.start_line,
                    "end_line": embedding.end_line,
                    "embedding_version": embedding.embedding_version,
                    "created_at": embedding.created_at,
                }
                metadatas.append(metadata)

            if self.chromadb_available and self.collection:
                # Batch add to ChromaDB collection
                self.collection.add(
                    embeddings=embedding_vectors,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )
            else:
                # Store in mock storage
                for i, embedding in enumerate(embeddings):
                    self.mock_embeddings[embedding.id] = {
                        "content": documents[i],
                        "metadata": metadatas[i],
                        "embedding": embedding_vectors[i],
                    }

            logger.info(f"Added {len(embeddings)} embeddings in batch")
            return len(embeddings)

        except Exception as e:
            logger.error(f"Failed to add batch embeddings: {e}")
            return 0

    async def add_file_embeddings(self, file_path: str, code_structure) -> int:
        """Add embeddings for all symbols in a file"""
        if not code_structure:
            return 0

        added_count = 0

        try:
            # Add embedding for the entire file
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            file_embedding = CodeEmbedding(
                id=self._generate_content_hash(f"file:{file_path}"),
                content=file_content[:1000],  # Limit content size
                file_path=file_path,
                language=code_structure.language,
                symbol_type="file",
                symbol_name=Path(file_path).name,
                start_line=1,
                end_line=code_structure.lines_of_code,
            )

            if await self.add_code_embedding(file_embedding):
                added_count += 1

            # Add embeddings for individual symbols
            for symbol in code_structure.symbols:
                # Extract symbol content (simplified - would use actual line ranges)
                symbol_content = f"{symbol.type} {symbol.name}"
                if symbol.parameters:
                    symbol_content += f"({', '.join(symbol.parameters)})"

                symbol_embedding = CodeEmbedding(
                    id=self._generate_content_hash(
                        f"{file_path}:{symbol.name}:{symbol.start_line}"
                    ),
                    content=symbol_content,
                    file_path=file_path,
                    language=code_structure.language,
                    symbol_type=symbol.type,
                    symbol_name=symbol.name,
                    start_line=symbol.start_line,
                    end_line=symbol.end_line,
                )

                if await self.add_code_embedding(symbol_embedding):
                    added_count += 1

            logger.info(f"Added {added_count} embeddings for {file_path}")
            return added_count

        except Exception as e:
            logger.error(f"Error adding file embeddings for {file_path}: {e}")
            return added_count

    async def search_similar_code(
        self,
        query: str,
        n_results: int = 5,
        file_filter: Optional[str] = None,
        symbol_type_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """Search for similar code using vector similarity"""
        if not self.is_initialized:
            logger.error("Vector store not initialized")
            return []

        try:
            # Generate query embedding
            query_embedding = self._create_embedding(query)

            if self.chromadb_available and self.collection:
                # Use ChromaDB search
                return await self._search_chromadb(
                    query_embedding, n_results, file_filter, symbol_type_filter
                )
            else:
                # Use mock search
                return await self._search_mock(
                    query, n_results, file_filter, symbol_type_filter
                )

        except Exception as e:
            logger.error(f"Error searching similar code: {e}")
            return []

    async def _search_chromadb(
        self,
        query_embedding: List[float],
        n_results: int,
        file_filter: Optional[str],
        symbol_type_filter: Optional[str],
    ) -> List[SearchResult]:
        """Search using ChromaDB"""
        # Prepare filters
        where_clause = {}
        if file_filter:
            where_clause["file_path"] = {"$contains": file_filter}
        if symbol_type_filter:
            where_clause["symbol_type"] = symbol_type_filter

        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None,
        )

        # Convert results to SearchResult objects
        search_results = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0

                # Convert distance to similarity score (0-1, higher is more similar)
                similarity_score = max(0.0, 1.0 - distance)

                search_results.append(
                    SearchResult(
                        content=doc,
                        file_path=metadata.get("file_path", ""),
                        symbol_name=metadata.get("symbol_name", ""),
                        symbol_type=metadata.get("symbol_type", ""),
                        similarity_score=similarity_score,
                        metadata=metadata,
                    )
                )

        return search_results

    async def _search_mock(
        self,
        query: str,
        n_results: int,
        file_filter: Optional[str],
        symbol_type_filter: Optional[str],
    ) -> List[SearchResult]:
        """Mock search for when ChromaDB is not available"""
        search_results = []
        query_lower = query.lower()

        # Simple text-based matching in mock storage
        for embedding_id, data in self.mock_embeddings.items():
            content = data["content"].lower()
            metadata = data["metadata"]

            # Apply filters
            if file_filter and file_filter not in metadata.get("file_path", ""):
                continue
            if symbol_type_filter and symbol_type_filter != metadata.get("symbol_type"):
                continue

            # Simple similarity based on text matching
            similarity_score = 0.0
            for word in query_lower.split():
                if word in content:
                    similarity_score += 0.2

            if similarity_score > 0:
                search_results.append(
                    SearchResult(
                        content=data["content"],
                        file_path=metadata.get("file_path", ""),
                        symbol_name=metadata.get("symbol_name", ""),
                        symbol_type=metadata.get("symbol_type", ""),
                        similarity_score=min(1.0, similarity_score),
                        metadata=metadata,
                    )
                )

        # Sort by similarity and limit results
        search_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return search_results[:n_results]

    async def remove_file_embeddings(self, file_path: str) -> int:
        """Remove all embeddings for a specific file"""
        if not self.is_initialized:
            return 0

        try:
            # Query for all embeddings from this file
            results = self.collection.get(where={"file_path": file_path})

            if results and results["ids"]:
                # Delete all found embeddings
                self.collection.delete(ids=results["ids"])
                count = len(results["ids"])
                logger.info(f"Removed {count} embeddings for {file_path}")
                return count

            return 0

        except Exception as e:
            logger.error(f"Error removing embeddings for {file_path}: {e}")
            return 0

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if not self.is_initialized:
            return {"error": "Vector store not initialized"}

        try:
            # Get collection count
            count = self.collection.count()

            # Get sample of metadata to understand content
            sample_results = self.collection.get(limit=100)

            stats = {
                "total_embeddings": count,
                "collection_name": self.collection_name,
                "embedding_model": f"{self.embedding_type}:{self.embedding_model_name}",
                "db_path": str(self.db_path),
            }

            if sample_results and sample_results["metadatas"]:
                # Analyze metadata
                languages = {}
                symbol_types = {}
                files = set()

                for metadata in sample_results["metadatas"]:
                    lang = metadata.get("language", "unknown")
                    languages[lang] = languages.get(lang, 0) + 1

                    sym_type = metadata.get("symbol_type", "unknown")
                    symbol_types[sym_type] = symbol_types.get(sym_type, 0) + 1

                    file_path = metadata.get("file_path")
                    if file_path:
                        files.add(file_path)

                stats.update(
                    {
                        "languages": languages,
                        "symbol_types": symbol_types,
                        "unique_files": len(files),
                        "sample_size": len(sample_results["metadatas"]),
                    }
                )

            return stats

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}

    async def clear_all_embeddings(self) -> bool:
        """Clear all embeddings from the vector store"""
        if not self.is_initialized:
            return False

        try:
            # Delete the collection and recreate it
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Code embeddings for LeanVibe L3 agent"},
            )

            logger.info("Cleared all embeddings from vector store")
            return True

        except Exception as e:
            logger.error(f"Error clearing embeddings: {e}")
            return False

    async def validate_semantic_search_accuracy(self) -> Dict[str, Any]:
        """Validate semantic search accuracy with test cases"""
        if not self.is_initialized:
            return {"error": "Vector store not initialized"}

        try:
            # Define test cases for semantic search validation
            test_cases = [
                {
                    "code": "def calculate_sum(a, b): return a + b",
                    "queries": ["sum function", "add numbers", "arithmetic"],
                    "symbol_name": "calculate_sum",
                    "symbol_type": "function"
                },
                {
                    "code": "class DatabaseConnection: def __init__(self): self.conn = None",
                    "queries": ["database class", "connection object", "db"],
                    "symbol_name": "DatabaseConnection", 
                    "symbol_type": "class"
                },
                {
                    "code": "async def fetch_data(url): return await http_client.get(url)",
                    "queries": ["async request", "fetch data", "http get"],
                    "symbol_name": "fetch_data",
                    "symbol_type": "function"
                }
            ]

            # Add test embeddings
            test_embeddings = []
            for i, test_case in enumerate(test_cases):
                embedding = CodeEmbedding(
                    id=f"validation_test_{i}",
                    content=test_case["code"],
                    file_path=f"/validation/test_{i}.py",
                    language="python",
                    symbol_type=test_case["symbol_type"],
                    symbol_name=test_case["symbol_name"],
                    start_line=1,
                    end_line=1
                )
                test_embeddings.append(embedding)

            # Add embeddings in batch
            added_count = await self.add_code_embeddings_batch(test_embeddings)
            
            if added_count != len(test_embeddings):
                return {"error": f"Failed to add all test embeddings: {added_count}/{len(test_embeddings)}"}

            # Test semantic search accuracy
            total_queries = 0
            successful_queries = 0
            results = []

            for test_case in test_cases:
                for query in test_case["queries"]:
                    total_queries += 1
                    
                    # Search for the query
                    search_results = await self.search_similar_code(query, n_results=3)
                    
                    # Check if expected symbol is in top results
                    found_symbols = [r.symbol_name for r in search_results]
                    expected_symbol = test_case["symbol_name"]
                    
                    if expected_symbol in found_symbols:
                        successful_queries += 1
                        rank = found_symbols.index(expected_symbol) + 1
                        similarity = next(r.similarity_score for r in search_results if r.symbol_name == expected_symbol)
                    else:
                        rank = None
                        similarity = 0.0
                    
                    results.append({
                        "query": query,
                        "expected_symbol": expected_symbol,
                        "found": expected_symbol in found_symbols,
                        "rank": rank,
                        "similarity_score": similarity,
                        "top_results": found_symbols[:3]
                    })

            # Calculate accuracy metrics
            accuracy = successful_queries / total_queries if total_queries > 0 else 0.0
            
            # Clean up test embeddings
            for embedding in test_embeddings:
                try:
                    if self.chromadb_available and self.collection:
                        self.collection.delete(ids=[embedding.id])
                    else:
                        self.mock_embeddings.pop(embedding.id, None)
                except Exception:
                    pass  # Ignore cleanup errors

            return {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "accuracy": accuracy,
                "embedding_type": self.embedding_type,
                "model_name": self.embedding_model_name,
                "results": results,
                "performance_grade": "excellent" if accuracy >= 0.9 else "good" if accuracy >= 0.7 else "needs_improvement"
            }

        except Exception as e:
            logger.error(f"Error validating semantic search accuracy: {e}")
            return {"error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get vector store service status"""
        return {
            "initialized": self.is_initialized,
            "chromadb_available": self.chromadb_available,
            "sentence_transformers_available": self.sentence_transformers_available,
            "db_path": str(self.db_path),
            "collection_name": self.collection_name,
            "embedding_model": f"{self.embedding_type}:{self.embedding_model_name}",
            "client_available": self.client is not None,
            "collection_available": self.collection is not None,
            "storage_mode": "chromadb" if self.chromadb_available else "mock",
        }
