"""
AI Architect Agent - Converts founder interviews to technical blueprints
Core intelligence for Blueprint System with NLP analysis and tech stack recommendations
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from ...models.mvp_models import (
    FounderInterview, TechnicalBlueprint, BusinessRequirement,
    MVPTechStack, MVPIndustry, MVPStatus
)
from ..assembly_line_system import BaseAIAgent, AgentType, AgentStatus, AgentResult

logger = logging.getLogger(__name__)


class AIArchitectAgent(BaseAIAgent):
    """AI agent for converting founder interviews into technical blueprints"""
    
    def __init__(self):
        super().__init__(AgentType.AI_ARCHITECT)
        
        # Initialize processing components
        self.business_analyzer = BusinessAnalysisEngine()
        self.tech_selector = TechStackRecommendationEngine()
        self.architecture_designer = ArchitectureDesignEngine()
        self.confidence_calculator = ConfidenceCalculator()
        
        logger.info("Initialized AI Architect Agent with blueprint generation capabilities")
    
    async def analyze_founder_interview(
        self, 
        interview: FounderInterview
    ) -> TechnicalBlueprint:
        """
        Main orchestration method for converting founder interview to technical blueprint
        Processing time target: < 30 seconds
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting blueprint generation for interview {interview.id}")
            
            # Stage 1: Business Analysis (5-8 seconds)
            business_requirements = await self.business_analyzer.extract_business_requirements(interview)
            
            user_personas = await self.business_analyzer.extract_user_personas(interview)
            
            complexity_analysis = await self.business_analyzer.analyze_complexity(interview, business_requirements)
            
            # Stage 2: Tech Stack Intelligence (3-5 seconds)
            recommended_stack = await self.tech_selector.recommend_optimal_stack(
                requirements=business_requirements,
                constraints=interview.technical_constraints,
                industry=interview.industry
            )
            
            # Stage 3: Architecture Design (10-15 seconds)
            database_schema = await self.architecture_designer.design_database_schema(
                business_requirements, user_personas
            )
            
            api_endpoints = await self.architecture_designer.create_api_endpoints(
                business_requirements, database_schema
            )
            
            # Stage 4: UX Flow Generation (5-8 seconds)
            user_flows = await self.architecture_designer.generate_user_flows(
                business_requirements, user_personas
            )
            
            wireframes = await self.architecture_designer.generate_wireframes(
                business_requirements, user_flows
            )
            
            # Stage 5: Quality Assessment (2-3 seconds)
            
            # Create initial blueprint
            blueprint = TechnicalBlueprint(
                tech_stack=recommended_stack,
                architecture_pattern=self._determine_architecture_pattern(business_requirements),
                database_schema=database_schema,
                api_endpoints=api_endpoints,
                user_flows=user_flows,
                wireframes=wireframes,
                design_system=self._generate_design_system(interview.industry),
                deployment_config=self._generate_deployment_config(recommended_stack),
                scaling_config=self._generate_scaling_config(complexity_analysis),
                monitoring_requirements=self._generate_monitoring_requirements(),
                monitoring_config=self._generate_monitoring_config(),
                test_strategy=self._generate_test_strategy(recommended_stack),
                performance_targets=self._generate_performance_targets(complexity_analysis),
                security_requirements=self._generate_security_requirements(interview.industry),
                generated_at=datetime.utcnow(),
                confidence_score=0.0,  # Will be calculated next
                estimated_generation_time=0  # Will be calculated next
            )
            
            # Calculate final confidence and estimates
            confidence_results = await self.confidence_calculator.calculate_confidence_score(
                blueprint, interview, business_requirements, complexity_analysis
            )
            
            blueprint.confidence_score = confidence_results["confidence_score"]
            blueprint.estimated_generation_time = confidence_results["estimated_generation_time"]
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Blueprint generation completed in {processing_time:.1f}s "
                f"with confidence {blueprint.confidence_score:.2f}"
            )
            
            return blueprint
            
        except Exception as e:
            logger.error(f"Blueprint generation failed: {e}")
            raise
    
    def _determine_architecture_pattern(self, requirements: List[BusinessRequirement]) -> str:
        """Determine optimal architecture pattern based on requirements"""
        # Analyze requirements for complexity indicators
        has_complex_workflows = any("workflow" in req.requirement.lower() for req in requirements)
        has_multiple_user_types = any("admin" in req.requirement.lower() or "role" in req.requirement.lower() for req in requirements)
        requires_high_scalability = any("scale" in req.requirement.lower() for req in requirements)
        
        if requires_high_scalability or len(requirements) > 15:
            return "microservices"
        elif has_complex_workflows or has_multiple_user_types:
            return "layered_architecture"
        else:
            return "mvc"
    
    def _generate_design_system(self, industry: MVPIndustry) -> Dict[str, Any]:
        """Generate design system based on industry best practices"""
        industry_designs = {
            MVPIndustry.FINTECH: {
                "primary_color": "#1E40AF",  # Professional blue
                "secondary_color": "#059669",  # Success green
                "font_family": "Inter",
                "theme": "professional",
                "ui_style": "minimal_modern"
            },
            MVPIndustry.HEALTHTECH: {
                "primary_color": "#0D9488",  # Medical teal
                "secondary_color": "#DC2626",  # Emergency red
                "font_family": "Inter",
                "theme": "clean_medical",
                "ui_style": "accessible_friendly"
            },
            MVPIndustry.ECOMMERCE: {
                "primary_color": "#7C3AED",  # Commerce purple
                "secondary_color": "#F59E0B",  # Accent orange
                "font_family": "Inter",
                "theme": "vibrant_commerce",
                "ui_style": "conversion_optimized"
            },
            MVPIndustry.PRODUCTIVITY: {
                "primary_color": "#3B82F6",  # Productivity blue
                "secondary_color": "#10B981",  # Success green
                "font_family": "Inter",
                "theme": "focused_minimal",
                "ui_style": "efficiency_focused"
            }
        }
        
        return industry_designs.get(industry, {
            "primary_color": "#3B82F6",
            "secondary_color": "#10B981", 
            "font_family": "Inter",
            "theme": "modern_neutral",
            "ui_style": "balanced_universal"
        })
    
    def _generate_deployment_config(self, tech_stack: MVPTechStack) -> Dict[str, Any]:
        """Generate deployment configuration based on tech stack"""
        base_config = {
            "type": "docker",
            "cloud_provider": "aws",
            "environment_stages": ["development", "staging", "production"],
            "ci_cd_platform": "github_actions"
        }
        
        if tech_stack == MVPTechStack.SAAS_PLATFORM:
            base_config.update({
                "orchestration": "kubernetes",
                "database_managed": True,
                "cdn_enabled": True,
                "backup_strategy": "automated_daily"
            })
        else:
            base_config.update({
                "orchestration": "docker_compose",
                "database_managed": False,
                "cdn_enabled": False,
                "backup_strategy": "manual"
            })
        
        return base_config
    
    def _generate_scaling_config(self, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate auto-scaling configuration based on complexity"""
        base_load = complexity_analysis.get("expected_load", "low")
        
        scaling_configs = {
            "low": {
                "min_replicas": 1,
                "max_replicas": 3,
                "auto_scaling": False,
                "cpu_threshold": 70
            },
            "medium": {
                "min_replicas": 2,
                "max_replicas": 10,
                "auto_scaling": True,
                "cpu_threshold": 60
            },
            "high": {
                "min_replicas": 3,
                "max_replicas": 20,
                "auto_scaling": True,
                "cpu_threshold": 50
            }
        }
        
        return scaling_configs.get(base_load, scaling_configs["low"])
    
    def _generate_monitoring_requirements(self) -> List[str]:
        """Generate monitoring requirements for MVP"""
        return [
            "API response times and error rates",
            "Database query performance",
            "User authentication success rates", 
            "Feature usage analytics",
            "System resource utilization",
            "Security events and anomalies"
        ]
    
    def _generate_monitoring_config(self) -> Dict[str, Any]:
        """Generate monitoring stack configuration"""
        return {
            "metrics_collection": {
                "prometheus": True,
                "custom_metrics": True,
                "retention_days": 30
            },
            "visualization": {
                "grafana": True,
                "dashboard_templates": ["system_overview", "business_metrics", "error_tracking"]
            },
            "alerting": {
                "email_notifications": True,
                "slack_integration": True,
                "alert_rules": ["high_error_rate", "system_down", "performance_degradation"]
            },
            "logging": {
                "centralized_logging": True,
                "log_retention_days": 90,
                "structured_logging": True
            }
        }
    
    def _generate_test_strategy(self, tech_stack: MVPTechStack) -> Dict[str, Any]:
        """Generate testing strategy based on tech stack"""
        return {
            "unit_tests": {
                "enabled": True,
                "coverage_threshold": 80,
                "framework": "pytest" if "api" in tech_stack.value.lower() else "jest"
            },
            "integration_tests": {
                "enabled": True,
                "api_testing": True,
                "database_testing": True
            },
            "e2e_tests": {
                "enabled": True,
                "framework": "playwright",
                "critical_user_flows": True
            },
            "performance_tests": {
                "enabled": False,  # Optional for MVP
                "load_testing": False
            }
        }
    
    def _generate_performance_targets(self, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance targets based on complexity"""
        complexity_level = complexity_analysis.get("complexity_level", "medium")
        
        targets = {
            "low": {
                "response_time": "< 500ms",
                "availability": "99.0%",
                "throughput": "100 rps",
                "page_load_time": "< 2s"
            },
            "medium": {
                "response_time": "< 300ms", 
                "availability": "99.5%",
                "throughput": "500 rps",
                "page_load_time": "< 1.5s"
            },
            "high": {
                "response_time": "< 200ms",
                "availability": "99.9%", 
                "throughput": "1000 rps",
                "page_load_time": "< 1s"
            }
        }
        
        return targets.get(complexity_level, targets["medium"])
    
    def _generate_security_requirements(self, industry: MVPIndustry) -> List[str]:
        """Generate security requirements based on industry"""
        base_requirements = [
            "HTTPS/TLS encryption for all data transmission",
            "JWT-based authentication with secure token handling",
            "Input validation and sanitization on all endpoints",
            "Rate limiting to prevent API abuse",
            "SQL injection prevention with parameterized queries"
        ]
        
        industry_specific = {
            MVPIndustry.FINTECH: [
                "PCI DSS compliance for payment processing",
                "Multi-factor authentication (MFA) required",
                "Encryption at rest for sensitive financial data",
                "Audit logging for all financial transactions"
            ],
            MVPIndustry.HEALTHTECH: [
                "HIPAA compliance for health data protection",
                "End-to-end encryption for PHI data",
                "Access controls based on healthcare roles",
                "Secure data backup and recovery procedures"
            ],
            MVPIndustry.ECOMMERCE: [
                "PCI compliance for payment processing",
                "Customer data encryption and privacy controls",
                "Fraud detection and prevention measures",
                "Secure payment gateway integration"
            ]
        }
        
        return base_requirements + industry_specific.get(industry, [])


class BusinessAnalysisEngine:
    """Extracts structured business requirements from founder interviews"""
    
    async def extract_business_requirements(
        self, 
        interview: FounderInterview
    ) -> List[BusinessRequirement]:
        """Extract structured requirements from interview data"""
        requirements = []
        
        # Process core features
        for i, feature in enumerate(interview.core_features):
            requirement = BusinessRequirement(
                requirement=feature,
                priority="high",
                category="functional",
                acceptance_criteria=self._generate_acceptance_criteria(feature)
            )
            requirements.append(requirement)
        
        # Process nice-to-have features as medium priority
        for feature in interview.nice_to_have_features:
            requirement = BusinessRequirement(
                requirement=feature,
                priority="medium", 
                category="functional",
                acceptance_criteria=self._generate_acceptance_criteria(feature)
            )
            requirements.append(requirement)
        
        # Add technical constraints as requirements
        for constraint in interview.technical_constraints:
            requirement = BusinessRequirement(
                requirement=f"Technical constraint: {constraint}",
                priority="high",
                category="performance",
                acceptance_criteria=[f"System must comply with: {constraint}"]
            )
            requirements.append(requirement)
        
        # Add integration requirements
        for integration in interview.integration_requirements:
            requirement = BusinessRequirement(
                requirement=f"Integration with {integration}",
                priority="medium",
                category="functional",
                acceptance_criteria=[f"Successfully integrate with {integration} API"]
            )
            requirements.append(requirement)
        
        logger.info(f"Extracted {len(requirements)} business requirements from interview")
        return requirements
    
    def _generate_acceptance_criteria(self, feature: str) -> List[str]:
        """Generate acceptance criteria for a feature using pattern matching"""
        feature_lower = feature.lower()
        
        # Common patterns and their criteria
        patterns = {
            "user registration": [
                "User can create account with email and password",
                "User receives email confirmation",
                "User can log in after registration"
            ],
            "user login": [
                "User can log in with valid credentials", 
                "Invalid credentials show appropriate error",
                "User session persists across browser refreshes"
            ],
            "dashboard": [
                "User sees personalized dashboard after login",
                "Dashboard loads within 2 seconds",
                "Dashboard shows relevant user data"
            ],
            "search": [
                "User can search using text input",
                "Search returns relevant results",
                "Search handles empty and invalid queries"
            ],
            "payment": [
                "User can securely enter payment information",
                "Payment processes successfully",
                "User receives payment confirmation"
            ]
        }
        
        # Find matching patterns
        for pattern, criteria in patterns.items():
            if pattern in feature_lower:
                return criteria
        
        # Default criteria for unmatched features
        return [
            f"Feature '{feature}' is implemented according to specifications",
            f"Feature '{feature}' is tested and working correctly",
            f"Feature '{feature}' provides appropriate user feedback"
        ]
    
    async def extract_user_personas(self, interview: FounderInterview) -> List[Dict[str, Any]]:
        """Extract user personas from interview data"""
        personas = []
        
        # Primary persona from target audience
        primary_persona = {
            "name": "Primary User",
            "description": interview.target_audience,
            "needs": interview.core_features[:3],  # Top 3 needs
            "pain_points": [interview.problem_statement],
            "goals": [interview.value_proposition]
        }
        personas.append(primary_persona)
        
        # Check for admin/secondary personas in features
        has_admin_features = any("admin" in feature.lower() for feature in interview.core_features)
        if has_admin_features:
            admin_persona = {
                "name": "Administrator", 
                "description": "System administrator managing the platform",
                "needs": [f for f in interview.core_features if "admin" in f.lower()],
                "pain_points": ["Need efficient platform management tools"],
                "goals": ["Maintain system performance and user satisfaction"]
            }
            personas.append(admin_persona)
        
        logger.info(f"Extracted {len(personas)} user personas")
        return personas
    
    async def analyze_complexity(
        self, 
        interview: FounderInterview,
        requirements: List[BusinessRequirement]
    ) -> Dict[str, Any]:
        """Analyze project complexity for resource estimation"""
        
        # Feature complexity scoring
        feature_count = len(interview.core_features) + len(interview.nice_to_have_features)
        integration_count = len(interview.integration_requirements)
        constraint_count = len(interview.technical_constraints)
        
        # Complexity indicators
        has_payments = any("payment" in feature.lower() for feature in interview.core_features)
        has_real_time = any("real-time" in feature.lower() for feature in interview.core_features)
        has_ai_ml = any("ai" in feature.lower() or "ml" in feature.lower() for feature in interview.core_features)
        has_multi_user = any("user" in feature.lower() and "multiple" in feature.lower() for feature in interview.core_features)
        
        # Calculate complexity score (0-1)
        base_score = min(feature_count / 20, 1.0)  # Normalize to 20 features = 1.0
        integration_bonus = min(integration_count * 0.1, 0.3)
        constraint_penalty = min(constraint_count * 0.05, 0.2)
        
        complexity_bonuses = 0
        if has_payments:
            complexity_bonuses += 0.2
        if has_real_time:
            complexity_bonuses += 0.15
        if has_ai_ml:
            complexity_bonuses += 0.25
        if has_multi_user:
            complexity_bonuses += 0.1
        
        final_score = min(base_score + integration_bonus + constraint_penalty + complexity_bonuses, 1.0)
        
        # Determine complexity level
        if final_score < 0.3:
            complexity_level = "low"
            expected_load = "low"
            development_time_weeks = 2-4
        elif final_score < 0.7:
            complexity_level = "medium" 
            expected_load = "medium"
            development_time_weeks = 4-8
        else:
            complexity_level = "high"
            expected_load = "high"
            development_time_weeks = 8-16
        
        analysis = {
            "complexity_score": final_score,
            "complexity_level": complexity_level,
            "expected_load": expected_load,
            "development_time_weeks": development_time_weeks,
            "feature_count": feature_count,
            "integration_count": integration_count,
            "has_payments": has_payments,
            "has_real_time": has_real_time,
            "has_ai_ml": has_ai_ml,
            "has_multi_user": has_multi_user
        }
        
        logger.info(f"Complexity analysis: {complexity_level} ({final_score:.2f}) - {development_time_weeks} weeks")
        return analysis


class TechStackRecommendationEngine:
    """Intelligent tech stack selection based on requirements and constraints"""
    
    STACK_COMPATIBILITY = {
        MVPTechStack.FULL_STACK_REACT: {
            "frontend": ["React 18", "TypeScript", "Tailwind CSS", "React Router"],
            "backend": ["FastAPI", "SQLAlchemy", "PostgreSQL", "Redis"],
            "deployment": ["Docker", "AWS ECS", "RDS", "CloudFront"],
            "monitoring": ["Prometheus", "Grafana", "Sentry"],
            "best_for": ["web applications", "dashboards", "productivity tools"],
            "complexity_range": [0.2, 0.8],
            "development_time_multiplier": 1.0
        },
        
        MVPTechStack.FULL_STACK_VUE: {
            "frontend": ["Vue 3", "TypeScript", "Tailwind CSS", "Vue Router"],
            "backend": ["FastAPI", "SQLAlchemy", "PostgreSQL", "Redis"],
            "deployment": ["Docker", "AWS ECS", "RDS", "CloudFront"],
            "monitoring": ["Prometheus", "Grafana", "Sentry"],
            "best_for": ["web applications", "content management", "e-commerce"],
            "complexity_range": [0.2, 0.8],
            "development_time_multiplier": 1.1
        },
        
        MVPTechStack.SAAS_PLATFORM: {
            "frontend": ["Next.js", "TypeScript", "Stripe", "Tailwind CSS"],
            "backend": ["FastAPI", "Multi-tenant PostgreSQL", "Redis", "Celery"],
            "deployment": ["Kubernetes", "AWS", "RDS", "CloudFront"],
            "monitoring": ["Full observability stack", "Business metrics"],
            "best_for": ["subscription services", "multi-tenant platforms", "fintech"],
            "complexity_range": [0.6, 1.0],
            "development_time_multiplier": 1.5
        },
        
        MVPTechStack.MOBILE_FIRST: {
            "frontend": ["React Native", "TypeScript", "Expo"],
            "backend": ["FastAPI", "SQLAlchemy", "PostgreSQL"],
            "deployment": ["Docker", "AWS ECS", "App Store", "Play Store"],
            "monitoring": ["Crashlytics", "Analytics", "APM"],
            "best_for": ["mobile apps", "on-the-go services", "consumer apps"],
            "complexity_range": [0.4, 0.9],
            "development_time_multiplier": 1.3
        },
        
        MVPTechStack.API_ONLY: {
            "frontend": [],
            "backend": ["FastAPI", "SQLAlchemy", "PostgreSQL", "Redis"],
            "deployment": ["Docker", "AWS Lambda", "RDS"],
            "monitoring": ["CloudWatch", "API Gateway metrics"],
            "best_for": ["api services", "integrations", "backend-only"],
            "complexity_range": [0.1, 0.6],
            "development_time_multiplier": 0.7
        }
    }
    
    async def recommend_optimal_stack(
        self,
        requirements: List[BusinessRequirement], 
        constraints: List[str],
        industry: MVPIndustry
    ) -> MVPTechStack:
        """Select optimal tech stack based on requirements analysis"""
        
        # Analyze requirements for stack indicators
        stack_indicators = self._analyze_stack_indicators(requirements, constraints, industry)
        
        # Score each stack option
        stack_scores = {}
        
        for stack, config in self.STACK_COMPATIBILITY.items():
            score = self._calculate_stack_score(stack_indicators, config, industry)
            stack_scores[stack] = score
            
        # Select highest scoring stack
        recommended_stack = max(stack_scores.items(), key=lambda x: x[1])[0]
        
        logger.info(f"Recommended tech stack: {recommended_stack} (score: {stack_scores[recommended_stack]:.2f})")
        return recommended_stack
    
    def _analyze_stack_indicators(
        self, 
        requirements: List[BusinessRequirement],
        constraints: List[str],
        industry: MVPIndustry
    ) -> Dict[str, Any]:
        """Analyze requirements for tech stack selection indicators"""
        
        req_text = " ".join([req.requirement.lower() for req in requirements])
        constraint_text = " ".join(constraints).lower()
        
        indicators = {
            "needs_mobile": "mobile" in req_text or "app" in constraint_text,
            "needs_web": "web" in req_text or "browser" in req_text,
            "needs_api_only": "api" in req_text and "frontend" not in req_text,
            "needs_multi_tenant": "tenant" in req_text or "saas" in req_text,
            "has_payments": "payment" in req_text or "stripe" in constraint_text,
            "has_real_time": "real-time" in req_text or "websocket" in req_text,
            "has_complex_auth": "auth" in req_text or "role" in req_text,
            "industry": industry,
            "requirement_count": len(requirements),
            "integration_heavy": len([r for r in requirements if "integration" in r.requirement.lower()]) > 2
        }
        
        return indicators
    
    def _calculate_stack_score(
        self, 
        indicators: Dict[str, Any],
        stack_config: Dict[str, Any],
        industry: MVPIndustry
    ) -> float:
        """Calculate compatibility score for a tech stack"""
        score = 0.5  # Base score
        
        # Mobile requirements
        if indicators["needs_mobile"]:
            if "React Native" in str(stack_config.get("frontend", [])):
                score += 0.3
            else:
                score -= 0.2
                
        # Web requirements
        if indicators["needs_web"] and not indicators["needs_mobile"]:
            if "React" in str(stack_config.get("frontend", [])) or "Vue" in str(stack_config.get("frontend", [])):
                score += 0.2
                
        # API-only requirements
        if indicators["needs_api_only"]:
            if not stack_config.get("frontend"):
                score += 0.4
            else:
                score -= 0.3
                
        # Multi-tenant/SaaS requirements
        if indicators["needs_multi_tenant"] or indicators["has_payments"]:
            if "Multi-tenant" in str(stack_config.get("backend", [])) or "Stripe" in str(stack_config.get("frontend", [])):
                score += 0.3
                
        # Industry-specific bonuses
        industry_preferences = {
            MVPIndustry.FINTECH: [MVPTechStack.SAAS_PLATFORM, MVPTechStack.FULL_STACK_REACT],
            MVPIndustry.ECOMMERCE: [MVPTechStack.FULL_STACK_VUE, MVPTechStack.SAAS_PLATFORM],
            MVPIndustry.PRODUCTIVITY: [MVPTechStack.FULL_STACK_REACT, MVPTechStack.SAAS_PLATFORM]
        }
        
        # Complexity matching
        complexity_score = indicators["requirement_count"] / 15.0  # Normalize to 15 requirements
        complexity_range = stack_config.get("complexity_range", [0, 1])
        
        if complexity_range[0] <= complexity_score <= complexity_range[1]:
            score += 0.2
        else:
            score -= abs(complexity_score - sum(complexity_range)/2) * 0.3
            
        return max(0, min(1, score))  # Clamp between 0 and 1


class ArchitectureDesignEngine:
    """Designs database schemas, API endpoints, and user flows"""
    
    async def design_database_schema(
        self,
        requirements: List[BusinessRequirement],
        user_personas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate database schema from business requirements"""
        
        schema = {"tables": {}, "relationships": [], "indexes": []}
        
        # Always include core user management
        schema["tables"]["users"] = {
            "fields": {
                "id": {"type": "uuid", "primary_key": True},
                "email": {"type": "string", "nullable": False, "unique": True},
                "password_hash": {"type": "string", "nullable": False},
                "first_name": {"type": "string", "nullable": False},
                "last_name": {"type": "string", "nullable": False},
                "is_active": {"type": "boolean", "default": True},
                "created_at": {"type": "timestamp", "default": "now()"},
                "updated_at": {"type": "timestamp", "default": "now()"}
            }
        }
        
        # Analyze requirements for domain entities
        entities = self._extract_domain_entities(requirements)
        
        for entity in entities:
            table_name = entity["name"].lower().replace(" ", "_") + "s"
            
            # Basic entity structure
            table_schema = {
                "fields": {
                    "id": {"type": "uuid", "primary_key": True},
                    "created_at": {"type": "timestamp", "default": "now()"},
                    "updated_at": {"type": "timestamp", "default": "now()"}
                }
            }
            
            # Add entity-specific fields
            for field in entity["fields"]:
                table_schema["fields"][field["name"]] = {
                    "type": field["type"],
                    "nullable": field.get("nullable", True)
                }
                
            # Add user relationship if entity is user-owned
            if entity.get("user_owned", True):
                table_schema["fields"]["user_id"] = {
                    "type": "uuid", 
                    "nullable": False,
                    "foreign_key": "users.id"
                }
                
            schema["tables"][table_name] = table_schema
            
        logger.info(f"Generated database schema with {len(schema['tables'])} tables")
        return schema
    
    def _extract_domain_entities(self, requirements: List[BusinessRequirement]) -> List[Dict[str, Any]]:
        """Extract domain entities from business requirements"""
        entities = []
        
        # Common entity patterns
        entity_patterns = {
            "task": {
                "fields": [
                    {"name": "title", "type": "string", "nullable": False},
                    {"name": "description", "type": "text"},
                    {"name": "status", "type": "string", "default": "pending"},
                    {"name": "priority", "type": "string", "default": "medium"},
                    {"name": "due_date", "type": "timestamp"}
                ]
            },
            "project": {
                "fields": [
                    {"name": "name", "type": "string", "nullable": False},
                    {"name": "description", "type": "text"},
                    {"name": "status", "type": "string", "default": "active"}
                ]
            },
            "user_profile": {
                "fields": [
                    {"name": "display_name", "type": "string", "nullable": False},
                    {"name": "bio", "type": "text"},
                    {"name": "avatar_url", "type": "string"},
                    {"name": "preferences", "type": "json", "default": "{}"}
                ]
            },
            "order": {
                "fields": [
                    {"name": "total_amount", "type": "decimal", "nullable": False},
                    {"name": "status", "type": "string", "default": "pending"},
                    {"name": "payment_status", "type": "string", "default": "unpaid"}
                ]
            },
            "product": {
                "fields": [
                    {"name": "name", "type": "string", "nullable": False},
                    {"name": "description", "type": "text"},
                    {"name": "price", "type": "decimal", "nullable": False},
                    {"name": "in_stock", "type": "boolean", "default": True}
                ]
            }
        }
        
        # Scan requirements for entity mentions
        found_entities = set()
        for req in requirements:
            req_lower = req.requirement.lower()
            for entity_name, entity_config in entity_patterns.items():
                if entity_name in req_lower and entity_name not in found_entities:
                    entity = {
                        "name": entity_name,
                        "fields": entity_config["fields"],
                        "user_owned": True
                    }
                    entities.append(entity)
                    found_entities.add(entity_name)
        
        # Always ensure we have at least 3 core entities for any business app
        required_entities = ["project", "task", "user_profile"]
        for req_entity in required_entities:
            if req_entity not in found_entities:
                if req_entity in entity_patterns:
                    entity = {
                        "name": req_entity,
                        "fields": entity_patterns[req_entity]["fields"],
                        "user_owned": True
                    }
                    entities.append(entity)
                    found_entities.add(req_entity)
                        
        return entities
    
    async def create_api_endpoints(
        self,
        requirements: List[BusinessRequirement],
        database_schema: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate RESTful API endpoints from requirements and schema"""
        
        endpoints = []
        
        # Authentication endpoints (always included)
        auth_endpoints = [
            {
                "name": "register",
                "method": "POST",
                "path": "/auth/register",
                "description": "User registration",
                "request_body": {"email": "string", "password": "string", "first_name": "string", "last_name": "string"},
                "response": {"user": "User", "token": "string"}
            },
            {
                "name": "login", 
                "method": "POST",
                "path": "/auth/login",
                "description": "User authentication",
                "request_body": {"email": "string", "password": "string"},
                "response": {"user": "User", "token": "string"}
            },
            {
                "name": "logout",
                "method": "POST", 
                "path": "/auth/logout",
                "description": "User logout",
                "response": {"message": "string"}
            }
        ]
        endpoints.extend(auth_endpoints)
        
        # Generate CRUD endpoints for each entity
        for table_name, table_config in database_schema["tables"].items():
            if table_name == "users":
                continue  # Skip users table (handled by auth)
                
            entity_name = table_name.rstrip("s")  # Remove plural
            
            crud_endpoints = [
                {
                    "name": f"list_{table_name}",
                    "method": "GET",
                    "path": f"/{table_name}",
                    "description": f"List {table_name}",
                    "query_params": {"limit": "integer", "offset": "integer"},
                    "response": {table_name: f"List[{entity_name.title()}]", "total": "integer"}
                },
                {
                    "name": f"create_{entity_name}",
                    "method": "POST",
                    "path": f"/{table_name}",
                    "description": f"Create new {entity_name}",
                    "request_body": self._generate_create_body(table_config),
                    "response": {entity_name: entity_name.title()}
                },
                {
                    "name": f"get_{entity_name}",
                    "method": "GET",
                    "path": f"/{table_name}/{{id}}",
                    "description": f"Get {entity_name} by ID",
                    "path_params": {"id": "uuid"},
                    "response": {entity_name: entity_name.title()}
                },
                {
                    "name": f"update_{entity_name}",
                    "method": "PUT",
                    "path": f"/{table_name}/{{id}}",
                    "description": f"Update {entity_name}",
                    "path_params": {"id": "uuid"},
                    "request_body": self._generate_update_body(table_config),
                    "response": {entity_name: entity_name.title()}
                },
                {
                    "name": f"delete_{entity_name}",
                    "method": "DELETE",
                    "path": f"/{table_name}/{{id}}",
                    "description": f"Delete {entity_name}",
                    "path_params": {"id": "uuid"},
                    "response": {"message": "string"}
                }
            ]
            endpoints.extend(crud_endpoints)
            
        logger.info(f"Generated {len(endpoints)} API endpoints")
        return endpoints
    
    def _generate_create_body(self, table_config: Dict[str, Any]) -> Dict[str, str]:
        """Generate request body schema for create endpoint"""
        body = {}
        fields = table_config.get("fields", {})
        
        for field_name, field_config in fields.items():
            # Skip auto-generated fields
            if field_name in ["id", "created_at", "updated_at"]:
                continue
                
            # Skip foreign keys (will be set from auth context)
            if "foreign_key" in field_config:
                continue
                
            if not field_config.get("nullable", True):
                body[field_name] = field_config["type"]
                
        return body
    
    def _generate_update_body(self, table_config: Dict[str, Any]) -> Dict[str, str]:
        """Generate request body schema for update endpoint"""
        body = {}
        fields = table_config.get("fields", {})
        
        for field_name, field_config in fields.items():
            # Skip auto-generated and immutable fields
            if field_name in ["id", "created_at", "updated_at", "user_id"]:
                continue
                
            body[field_name] = f"Optional[{field_config['type']}]"
                
        return body
    
    async def generate_user_flows(
        self,
        requirements: List[BusinessRequirement],
        user_personas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate user journey flows from requirements"""
        
        flows = []
        
        # Core authentication flow (always included)
        auth_flow = {
            "name": "user_authentication",
            "description": "User registration and login process",
            "steps": [
                {"step": "Landing page visit", "action": "View homepage"},
                {"step": "Registration", "action": "Create account with email/password"},
                {"step": "Email verification", "action": "Confirm email address"},
                {"step": "Login", "action": "Authenticate with credentials"},
                {"step": "Dashboard access", "action": "View personalized dashboard"}
            ],
            "persona": "Primary User"
        }
        flows.append(auth_flow)
        
        # Extract flows from requirements
        flow_patterns = self._identify_flow_patterns(requirements)
        
        for pattern in flow_patterns:
            flow = {
                "name": pattern["name"],
                "description": pattern["description"],
                "steps": pattern["steps"],
                "persona": "Primary User"
            }
            flows.append(flow)
            
        logger.info(f"Generated {len(flows)} user flows")
        return flows
    
    def _identify_flow_patterns(self, requirements: List[BusinessRequirement]) -> List[Dict[str, Any]]:
        """Identify common user flow patterns from requirements"""
        patterns = []
        
        req_text = " ".join([req.requirement.lower() for req in requirements])
        
        # Task management flow
        if any(word in req_text for word in ["task", "todo", "manage"]):
            patterns.append({
                "name": "task_management",
                "description": "Create and manage tasks",
                "steps": [
                    {"step": "Navigate to tasks", "action": "Access task management section"},
                    {"step": "Create task", "action": "Fill task creation form"},
                    {"step": "Set details", "action": "Add description, priority, due date"},
                    {"step": "Save task", "action": "Submit task to system"},
                    {"step": "View task", "action": "See task in task list"}
                ]
            })
            
        # E-commerce flow
        if any(word in req_text for word in ["order", "purchase", "cart", "payment"]):
            patterns.append({
                "name": "purchase_process",
                "description": "Complete product purchase",
                "steps": [
                    {"step": "Browse products", "action": "View product catalog"},
                    {"step": "Select product", "action": "Choose product and quantity"},
                    {"step": "Add to cart", "action": "Add items to shopping cart"},
                    {"step": "Checkout", "action": "Proceed to payment"},
                    {"step": "Payment", "action": "Enter payment information"},
                    {"step": "Confirmation", "action": "Receive order confirmation"}
                ]
            })
            
        # Admin management flow
        if "admin" in req_text:
            patterns.append({
                "name": "admin_management", 
                "description": "Administrative system management",
                "steps": [
                    {"step": "Admin login", "action": "Authenticate as administrator"},
                    {"step": "Access admin panel", "action": "Navigate to management interface"},
                    {"step": "Manage users", "action": "View and modify user accounts"},
                    {"step": "System configuration", "action": "Update system settings"},
                    {"step": "Monitor activity", "action": "Review system logs and metrics"}
                ]
            })
            
        return patterns
    
    async def generate_wireframes(
        self,
        requirements: List[BusinessRequirement],
        user_flows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate wireframe specifications from user flows"""
        
        wireframes = []
        
        # Core wireframes based on flows
        for flow in user_flows:
            flow_name = flow["name"]
            
            if flow_name == "user_authentication":
                wireframes.extend([
                    {
                        "name": "login_page",
                        "description": "User login interface",
                        "components": [
                            "Email input field",
                            "Password input field", 
                            "Login button",
                            "Registration link",
                            "Forgot password link"
                        ],
                        "layout": "centered_form"
                    },
                    {
                        "name": "registration_page",
                        "description": "User registration interface", 
                        "components": [
                            "First name input",
                            "Last name input",
                            "Email input field",
                            "Password input field",
                            "Confirm password field",
                            "Register button",
                            "Login link"
                        ],
                        "layout": "centered_form"
                    }
                ])
                
            elif flow_name == "task_management":
                wireframes.extend([
                    {
                        "name": "task_dashboard",
                        "description": "Main task management interface",
                        "components": [
                            "Task list/grid view",
                            "Create new task button",
                            "Filter and search controls",
                            "Task status indicators",
                            "Bulk actions toolbar"
                        ],
                        "layout": "dashboard_grid"
                    },
                    {
                        "name": "task_form", 
                        "description": "Task creation/editing form",
                        "components": [
                            "Task title input",
                            "Description textarea",
                            "Priority dropdown",
                            "Due date picker",
                            "Category selector", 
                            "Save/Cancel buttons"
                        ],
                        "layout": "form_layout"
                    }
                ])
                
        # Always include main dashboard
        main_dashboard = {
            "name": "main_dashboard",
            "description": "Primary user dashboard after login",
            "components": [
                "Navigation menu",
                "User profile section",
                "Key metrics/stats",
                "Recent activity feed",
                "Quick action buttons",
                "Notification center"
            ],
            "layout": "dashboard_layout"
        }
        wireframes.append(main_dashboard)
        
        logger.info(f"Generated {len(wireframes)} wireframe specifications")
        return wireframes


class ConfidenceCalculator:
    """Calculates blueprint confidence scores and generation estimates"""
    
    async def calculate_confidence_score(
        self,
        blueprint: TechnicalBlueprint,
        interview: FounderInterview,
        requirements: List[BusinessRequirement],
        complexity_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall confidence score and generation estimates"""
        
        # Individual confidence components
        tech_stack_confidence = self._calculate_tech_stack_confidence(blueprint, requirements)
        architecture_confidence = self._calculate_architecture_confidence(blueprint, complexity_analysis)
        requirement_coverage_confidence = self._calculate_requirement_coverage(blueprint, requirements)
        feasibility_confidence = self._calculate_technical_feasibility(blueprint, complexity_analysis)
        
        # Weighted overall confidence
        weights = {
            "tech_stack": 0.25,
            "architecture": 0.25, 
            "requirement_coverage": 0.30,
            "feasibility": 0.20
        }
        
        overall_confidence = (
            tech_stack_confidence * weights["tech_stack"] +
            architecture_confidence * weights["architecture"] +
            requirement_coverage_confidence * weights["requirement_coverage"] + 
            feasibility_confidence * weights["feasibility"]
        )
        
        # Estimate generation time based on complexity and confidence
        base_hours = complexity_analysis.get("development_time_weeks", 4) * 40 / 6  # Convert weeks to hours, divide by team size
        confidence_multiplier = 2.0 - overall_confidence  # Lower confidence = longer time
        estimated_hours = base_hours * confidence_multiplier
        
        results = {
            "confidence_score": round(overall_confidence, 3),
            "estimated_generation_time": max(2, min(24, int(estimated_hours))),  # Clamp between 2-24 hours
            "confidence_breakdown": {
                "tech_stack": tech_stack_confidence,
                "architecture": architecture_confidence,
                "requirement_coverage": requirement_coverage_confidence,
                "technical_feasibility": feasibility_confidence
            }
        }
        
        logger.info(f"Calculated confidence score: {overall_confidence:.3f} ({estimated_hours:.1f}h estimated)")
        return results
    
    def _calculate_tech_stack_confidence(
        self, 
        blueprint: TechnicalBlueprint,
        requirements: List[BusinessRequirement]
    ) -> float:
        """Calculate confidence in tech stack selection"""
        
        # Check for proven stack combinations
        proven_stacks = {
            MVPTechStack.FULL_STACK_REACT: 0.95,
            MVPTechStack.FULL_STACK_VUE: 0.90,
            MVPTechStack.SAAS_PLATFORM: 0.85,
            MVPTechStack.API_ONLY: 0.95,
            MVPTechStack.MOBILE_FIRST: 0.80
        }
        
        base_confidence = proven_stacks.get(blueprint.tech_stack, 0.70)
        
        # Penalty for complex requirements with simple stacks
        complex_features = sum(1 for req in requirements if any(word in req.requirement.lower() 
                              for word in ["payment", "real-time", "ai", "ml", "analytics"]))
        
        if complex_features > 3 and blueprint.tech_stack in [MVPTechStack.API_ONLY]:
            base_confidence -= 0.15
            
        return max(0.5, base_confidence)
    
    def _calculate_architecture_confidence(
        self,
        blueprint: TechnicalBlueprint,
        complexity_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence in architecture decisions"""
        
        complexity_level = complexity_analysis.get("complexity_level", "medium")
        architecture = blueprint.architecture_pattern
        
        # Architecture appropriateness for complexity
        architecture_match = {
            "low": {"mvc": 0.95, "layered_architecture": 0.85, "microservices": 0.60},
            "medium": {"mvc": 0.80, "layered_architecture": 0.95, "microservices": 0.85},
            "high": {"mvc": 0.60, "layered_architecture": 0.80, "microservices": 0.95}
        }
        
        base_confidence = architecture_match.get(complexity_level, {}).get(architecture, 0.70)
        
        # Bonus for good database design
        table_count = len(blueprint.database_schema.get("tables", {}))
        if 3 <= table_count <= 10:  # Reasonable table count
            base_confidence += 0.05
        
        # Bonus for comprehensive API design
        endpoint_count = len(blueprint.api_endpoints)
        if endpoint_count >= 8:  # Good API coverage
            base_confidence += 0.05
            
        return min(1.0, base_confidence)
    
    def _calculate_requirement_coverage(
        self,
        blueprint: TechnicalBlueprint,
        requirements: List[BusinessRequirement]
    ) -> float:
        """Calculate how well blueprint covers requirements"""
        
        total_requirements = len(requirements)
        if total_requirements == 0:
            return 0.5
            
        # Check coverage of high-priority requirements
        high_priority_reqs = [req for req in requirements if req.priority == "high"]
        coverage_score = 0.0
        
        # API endpoint coverage
        api_paths = [endpoint.get("path", "") for endpoint in blueprint.api_endpoints]
        covered_entities = set()
        
        for path in api_paths:
            path_parts = path.strip("/").split("/")
            if path_parts:
                covered_entities.add(path_parts[0])
                
        # Database coverage
        db_tables = set(blueprint.database_schema.get("tables", {}).keys())
        
        # User flow coverage
        flow_names = {flow.get("name", "") for flow in blueprint.user_flows}
        
        # Score based on coverage
        entity_coverage = len(covered_entities) / max(1, len(high_priority_reqs))
        flow_coverage = len(flow_names) / max(1, total_requirements / 5)  # Expect ~5 reqs per flow
        
        coverage_score = (entity_coverage + flow_coverage) / 2
        
        return min(1.0, max(0.3, coverage_score))
    
    def _calculate_technical_feasibility(
        self,
        blueprint: TechnicalBlueprint,
        complexity_analysis: Dict[str, Any]
    ) -> float:
        """Calculate technical feasibility of implementation"""
        
        base_feasibility = 0.85
        
        # Check for technical risk factors
        risk_factors = {
            "has_payments": complexity_analysis.get("has_payments", False),
            "has_real_time": complexity_analysis.get("has_real_time", False),
            "has_ai_ml": complexity_analysis.get("has_ai_ml", False),
            "high_integration_count": complexity_analysis.get("integration_count", 0) > 5
        }
        
        # Apply risk penalties
        for risk, present in risk_factors.items():
            if present:
                if risk == "has_ai_ml":
                    base_feasibility -= 0.20  # AI/ML adds complexity
                elif risk == "has_real_time":
                    base_feasibility -= 0.10  # Real-time features complex
                elif risk == "has_payments":
                    base_feasibility -= 0.05  # Payments well-understood
                elif risk == "high_integration_count":
                    base_feasibility -= 0.15  # Many integrations risky
                    
        # Bonus for good monitoring/testing strategy
        if blueprint.monitoring_config and blueprint.test_strategy:
            base_feasibility += 0.05
            
        return max(0.4, base_feasibility)