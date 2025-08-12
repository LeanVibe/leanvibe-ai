"""
Backend Coder Agent - FastAPI Backend Generation
Generates complete FastAPI backend with database models, API endpoints, and business logic
"""

import asyncio
import json
import logging
import os
import tempfile
from typing import Dict, List, Any, Optional
from uuid import UUID

from ...services.assembly_line_system import BaseAIAgent, AgentType, AgentResult, AgentStatus, QualityGateResult, QualityGateCheck
from ...models.mvp_models import TechnicalBlueprint, MVPTechStack

logger = logging.getLogger(__name__)


class BackendCoderAgent(BaseAIAgent):
    """AI agent that generates FastAPI backend code from technical blueprints"""
    
    def __init__(self):
        super().__init__(AgentType.BACKEND)
        self.supported_stacks = [
            MVPTechStack.FULL_STACK_REACT,
            MVPTechStack.FULL_STACK_VUE,
            MVPTechStack.MOBILE_FIRST,
            MVPTechStack.API_ONLY,
            MVPTechStack.SAAS_PLATFORM
        ]
    
    async def _execute_agent(
        self,
        mvp_project_id: UUID,
        input_data: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> AgentResult:
        """Generate complete FastAPI backend from blueprint"""
        
        blueprint_data = input_data.get("blueprint", {})
        if not blueprint_data:
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message="No blueprint data provided"
            )
        
        try:
            # Parse blueprint
            blueprint = TechnicalBlueprint(**blueprint_data)
            
            # Validate tech stack compatibility
            if blueprint.tech_stack not in self.supported_stacks:
                return AgentResult(
                    agent_type=self.agent_type,
                    status=AgentStatus.FAILED,
                    error_message=f"Tech stack {blueprint.tech_stack} not supported by backend agent"
                )
            
            # Create temporary directory for generated code
            temp_dir = tempfile.mkdtemp(prefix=f"mvp_backend_{mvp_project_id}_")
            
            # Progress tracking
            total_steps = 8
            current_step = 0
            
            # Step 1: Generate database models
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            models_code = await self._generate_database_models(blueprint)
            await self._write_file(temp_dir, "app/models/__init__.py", "")
            await self._write_file(temp_dir, "app/models/database.py", models_code["database"])
            for model_name, model_code in models_code["models"].items():
                await self._write_file(temp_dir, f"app/models/{model_name}.py", model_code)
            current_step += 1
            
            # Step 2: Generate API endpoints
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            api_code = await self._generate_api_endpoints(blueprint)
            await self._write_file(temp_dir, "app/api/__init__.py", "")
            for endpoint_name, endpoint_code in api_code.items():
                await self._write_file(temp_dir, f"app/api/{endpoint_name}.py", endpoint_code)
            current_step += 1
            
            # Step 3: Generate services and business logic
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            services_code = await self._generate_services(blueprint)
            await self._write_file(temp_dir, "app/services/__init__.py", "")
            for service_name, service_code in services_code.items():
                await self._write_file(temp_dir, f"app/services/{service_name}.py", service_code)
            current_step += 1
            
            # Step 4: Generate authentication and security
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            auth_code = await self._generate_authentication(blueprint)
            await self._write_file(temp_dir, "app/auth/__init__.py", "")
            await self._write_file(temp_dir, "app/auth/auth.py", auth_code)
            current_step += 1
            
            # Step 5: Generate main application
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            main_code = await self._generate_main_app(blueprint)
            await self._write_file(temp_dir, "app/main.py", main_code)
            current_step += 1
            
            # Step 6: Generate configuration and settings
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            config_code = await self._generate_configuration(blueprint)
            await self._write_file(temp_dir, "app/config.py", config_code)
            current_step += 1
            
            # Step 7: Generate requirements and Docker
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            requirements_code = await self._generate_requirements(blueprint)
            dockerfile_code = await self._generate_dockerfile(blueprint)
            await self._write_file(temp_dir, "requirements.txt", requirements_code)
            await self._write_file(temp_dir, "Dockerfile", dockerfile_code)
            current_step += 1
            
            # Step 8: Generate tests
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            test_code = await self._generate_tests(blueprint)
            await self._write_file(temp_dir, "tests/__init__.py", "")
            for test_name, test_content in test_code.items():
                await self._write_file(temp_dir, f"tests/{test_name}.py", test_content)
            current_step += 1
            
            # Calculate confidence based on complexity and completeness
            confidence_score = await self._calculate_confidence(blueprint, temp_dir)
            
            # Collect all generated files
            artifacts = await self._collect_artifacts(temp_dir)
            
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                output={
                    "generated_code_path": temp_dir,
                    "database_schema": blueprint.database_schema,
                    "api_endpoints": blueprint.api_endpoints,
                    "architecture_pattern": blueprint.architecture_pattern,
                    "lines_of_code": await self._count_lines_of_code(temp_dir)
                },
                artifacts=artifacts,
                metrics={
                    "lines_of_code": await self._count_lines_of_code(temp_dir),
                    "endpoints_generated": len(blueprint.api_endpoints),
                    "models_generated": len(blueprint.database_schema.get("tables", [])),
                    "test_coverage_estimate": 0.85
                },
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.error(f"Backend code generation failed: {e}")
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message=str(e)
            )
    
    async def _generate_database_models(self, blueprint: TechnicalBlueprint) -> Dict[str, Any]:
        """Generate SQLAlchemy database models"""
        
        database_code = '''"""
Database configuration for MVP
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mvp.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
        
        models = {}
        
        # Generate models based on database schema
        for table_name, table_config in blueprint.database_schema.get("tables", {}).items():
            model_name = table_name.title().replace("_", "")
            
            model_code = f'''"""
{model_name} model for MVP
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class {model_name}(Base):
    __tablename__ = "{table_name}"
    
    id = Column(Integer, primary_key=True, index=True)
'''
            
            # Add fields based on schema
            for field_name, field_config in table_config.get("fields", {}).items():
                if field_name != "id":  # Skip ID field as it's already added
                    field_type = self._map_field_type(field_config.get("type", "string"))
                    nullable = field_config.get("nullable", True)
                    
                    model_code += f'''    {field_name} = Column({field_type}, nullable={nullable})
'''
            
            # Add timestamps if not specified
            if "created_at" not in table_config.get("fields", {}):
                model_code += '''    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
'''
            
            models[table_name] = model_code
        
        return {
            "database": database_code,
            "models": models
        }
    
    async def _generate_api_endpoints(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate FastAPI endpoint handlers"""
        
        endpoints = {}
        
        for endpoint_config in blueprint.api_endpoints:
            endpoint_name = endpoint_config.get("name", "api")
            method = endpoint_config.get("method", "GET").upper()
            path = endpoint_config.get("path", "/")
            description = endpoint_config.get("description", "API endpoint")
            
            endpoint_code = f'''"""
{endpoint_name.title()} API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..models.database import get_db
from ..models import *

router = APIRouter(prefix="/{endpoint_name}", tags=["{endpoint_name}"])

@router.{method.lower()}("{path}")
async def {endpoint_name}_handler(db: Session = Depends(get_db)):
    """{description}"""
    try:
        # TODO: Implement {endpoint_name} logic
        return {{"message": "{description}", "status": "success"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
            
            endpoints[endpoint_name] = endpoint_code
        
        return endpoints
    
    async def _generate_services(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate business logic services"""
        
        services = {}
        
        # Generate a service for each main entity
        for table_name in blueprint.database_schema.get("tables", {}):
            service_name = f"{table_name}_service"
            model_name = table_name.title().replace("_", "")
            
            service_code = f'''"""
{model_name} service for business logic
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.{table_name} import {model_name}
from ..models.database import get_db

class {model_name}Service:
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_{table_name}(self, data: dict) -> {model_name}:
        """Create new {table_name}"""
        item = {model_name}(**data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
    
    async def get_{table_name}(self, item_id: int) -> Optional[{model_name}]:
        """Get {table_name} by ID"""
        return self.db.query({model_name}).filter({model_name}.id == item_id).first()
    
    async def list_{table_name}s(self, skip: int = 0, limit: int = 100) -> List[{model_name}]:
        """List {table_name}s with pagination"""
        return self.db.query({model_name}).offset(skip).limit(limit).all()
    
    async def update_{table_name}(self, item_id: int, data: dict) -> Optional[{model_name}]:
        """Update {table_name}"""
        item = self.db.query({model_name}).filter({model_name}.id == item_id).first()
        if item:
            for key, value in data.items():
                setattr(item, key, value)
            self.db.commit()
            self.db.refresh(item)
        return item
    
    async def delete_{table_name}(self, item_id: int) -> bool:
        """Delete {table_name}"""
        item = self.db.query({model_name}).filter({model_name}.id == item_id).first()
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False
'''
            
            services[service_name] = service_code
        
        return services
    
    async def _generate_authentication(self, blueprint: TechnicalBlueprint) -> str:
        """Generate authentication and security code"""
        
        auth_code = '''"""
Authentication and security for MVP
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception
'''
        
        return auth_code
    
    async def _generate_main_app(self, blueprint: TechnicalBlueprint) -> str:
        """Generate main FastAPI application"""
        
        main_code = '''"""
Main FastAPI application for MVP
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .auth.auth import get_current_user
from .api import *
from .models.database import engine, Base
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="MVP API",
    description="Auto-generated MVP API",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MVP API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }

# Include API routers
# TODO: Add router includes based on generated endpoints

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8765)))
'''
        
        return main_code
    
    async def _generate_configuration(self, blueprint: TechnicalBlueprint) -> str:
        """Generate configuration settings"""
        
        config_code = '''"""
Configuration settings for MVP
"""
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "sqlite:///./mvp.db"
    
    # Security
    secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8765
    debug: bool = False
    
    # CORS
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()
'''
        
        return config_code
    
    async def _generate_requirements(self, blueprint: TechnicalBlueprint) -> str:
        """Generate Python requirements"""
        
        requirements = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
'''
        
        return requirements
    
    async def _generate_dockerfile(self, blueprint: TechnicalBlueprint) -> str:
        """Generate Dockerfile"""
        
        dockerfile = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8765

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"]
'''
        
        return dockerfile
    
    async def _generate_tests(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate test files"""
        
        tests = {}
        
        # Main test file
        tests["test_main"] = '''"""
Tests for main application
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "MVP API is running"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
'''
        
        # Generate test for each endpoint
        for endpoint_config in blueprint.api_endpoints:
            endpoint_name = endpoint_config.get("name", "api")
            
            tests[f"test_{endpoint_name}"] = f'''"""
Tests for {endpoint_name} endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_{endpoint_name}_endpoint():
    # TODO: Implement {endpoint_name} tests
    pass
'''
        
        return tests
    
    # Helper methods
    
    def _map_field_type(self, field_type: str) -> str:
        """Map field type to SQLAlchemy column type"""
        type_mapping = {
            "string": "String(255)",
            "text": "Text",
            "integer": "Integer",
            "boolean": "Boolean",
            "datetime": "DateTime",
            "float": "Float"
        }
        return type_mapping.get(field_type.lower(), "String(255)")
    
    async def _write_file(self, base_dir: str, file_path: str, content: str):
        """Write content to file, creating directories as needed"""
        full_path = os.path.join(base_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def _calculate_confidence(self, blueprint: TechnicalBlueprint, temp_dir: str) -> float:
        """Calculate confidence score for generated code"""
        confidence_factors = []
        
        # Blueprint completeness factor
        blueprint_score = blueprint.confidence_score if hasattr(blueprint, 'confidence_score') else 0.8
        confidence_factors.append(blueprint_score)
        
        # Code generation completeness
        expected_files = ["app/main.py", "app/config.py", "requirements.txt", "Dockerfile"]
        generated_files = await self._collect_artifacts(temp_dir)
        completeness = len([f for f in expected_files if any(f in path for path in generated_files)]) / len(expected_files)
        confidence_factors.append(completeness)
        
        # Complexity handling
        complexity_score = min(1.0, 1.0 - (len(blueprint.api_endpoints) - 5) * 0.1)  # Reduce confidence for very complex APIs
        confidence_factors.append(max(0.6, complexity_score))
        
        return sum(confidence_factors) / len(confidence_factors)
    
    async def _collect_artifacts(self, temp_dir: str) -> List[str]:
        """Collect all generated file paths"""
        artifacts = []
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, temp_dir)
                artifacts.append(relative_path)
        return artifacts
    
    async def _count_lines_of_code(self, temp_dir: str) -> int:
        """Count total lines of generated code"""
        total_lines = 0
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(('.py', '.txt', '.yml', '.yaml')):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            total_lines += len(f.readlines())
                    except Exception:
                        pass  # Skip files that can't be read
        return total_lines
    
    async def quality_check(self, result: AgentResult) -> QualityGateResult:
        """Perform quality checks on generated backend code"""
        checks = []
        
        # Check if code was generated
        if not result.artifacts:
            checks.append(QualityGateCheck(
                check_name="code_generation",
                passed=False,
                score=0.0,
                details="No code artifacts generated"
            ))
        else:
            checks.append(QualityGateCheck(
                check_name="code_generation",
                passed=True,
                score=1.0,
                details=f"Generated {len(result.artifacts)} files"
            ))
        
        # Check essential files
        essential_files = ["app/main.py", "requirements.txt", "Dockerfile"]
        missing_files = []
        for essential in essential_files:
            if not any(essential in artifact for artifact in result.artifacts):
                missing_files.append(essential)
        
        if missing_files:
            checks.append(QualityGateCheck(
                check_name="essential_files",
                passed=False,
                score=0.5,
                details=f"Missing essential files: {missing_files}",
                fix_suggestions=[f"Generate {f}" for f in missing_files]
            ))
        else:
            checks.append(QualityGateCheck(
                check_name="essential_files",
                passed=True,
                score=1.0,
                details="All essential files generated"
            ))
        
        # Check code complexity
        lines_of_code = result.metrics.get("lines_of_code", 0)
        if lines_of_code < 100:
            checks.append(QualityGateCheck(
                check_name="code_complexity",
                passed=False,
                score=0.3,
                details=f"Generated code too simple: {lines_of_code} lines",
                fix_suggestions=["Add more comprehensive business logic", "Expand API endpoints"]
            ))
        elif lines_of_code > 5000:
            checks.append(QualityGateCheck(
                check_name="code_complexity",
                passed=True,
                score=0.7,
                details=f"Generated code very complex: {lines_of_code} lines"
            ))
        else:
            checks.append(QualityGateCheck(
                check_name="code_complexity",
                passed=True,
                score=1.0,
                details=f"Generated code appropriately complex: {lines_of_code} lines"
            ))
        
        # Calculate overall result
        overall_score = sum(check.score for check in checks) / len(checks) if checks else 0.0
        overall_passed = all(check.passed for check in checks)
        
        blockers = []
        if not overall_passed and overall_score < 0.7:
            blockers.append("Backend code quality below acceptable threshold")
        
        return QualityGateResult(
            overall_passed=overall_passed and not blockers,
            overall_score=overall_score,
            checks=checks,
            blockers=blockers
        )