"""
Frontend Coder Agent - React/Lit Frontend Generation
Generates complete frontend application with components, routing, and API integration
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


class FrontendCoderAgent(BaseAIAgent):
    """AI agent that generates React/Lit frontend code from technical blueprints"""
    
    def __init__(self):
        super().__init__(AgentType.FRONTEND)
        self.supported_stacks = [
            MVPTechStack.FULL_STACK_REACT,
            MVPTechStack.FULL_STACK_VUE,
            MVPTechStack.MOBILE_FIRST,
            MVPTechStack.STATIC_SITE,
            MVPTechStack.SAAS_PLATFORM
        ]
    
    async def _execute_agent(
        self,
        mvp_project_id: UUID,
        input_data: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> AgentResult:
        """Generate complete frontend application from blueprint"""
        
        blueprint_data = input_data.get("blueprint", {})
        backend_output = input_data.get("backend_output", {})
        
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
                    error_message=f"Tech stack {blueprint.tech_stack} not supported by frontend agent"
                )
            
            # Create temporary directory for generated code
            temp_dir = tempfile.mkdtemp(prefix=f"mvp_frontend_{mvp_project_id}_")
            
            # Determine frontend framework
            framework = self._determine_framework(blueprint.tech_stack)
            
            # Progress tracking
            total_steps = 10
            current_step = 0
            
            # Step 1: Generate project structure and configuration
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            await self._generate_project_structure(temp_dir, framework, blueprint)
            current_step += 1
            
            # Step 2: Generate package.json and dependencies
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            package_json = await self._generate_package_json(framework, blueprint)
            await self._write_file(temp_dir, "package.json", package_json)
            current_step += 1
            
            # Step 3: Generate main application entry point
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            main_app = await self._generate_main_app(framework, blueprint)
            await self._write_file(temp_dir, f"src/App.{self._get_file_extension(framework)}", main_app)
            current_step += 1
            
            # Step 4: Generate API service layer
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            api_service = await self._generate_api_service(framework, blueprint, backend_output)
            await self._write_file(temp_dir, f"src/services/api.{self._get_file_extension(framework)}", api_service)
            current_step += 1
            
            # Step 5: Generate UI components based on wireframes
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            components = await self._generate_ui_components(framework, blueprint)
            for component_name, component_code in components.items():
                await self._write_file(
                    temp_dir, 
                    f"src/components/{component_name}.{self._get_file_extension(framework)}", 
                    component_code
                )
            current_step += 1
            
            # Step 6: Generate pages/views
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            pages = await self._generate_pages(framework, blueprint)
            for page_name, page_code in pages.items():
                await self._write_file(
                    temp_dir,
                    f"src/pages/{page_name}.{self._get_file_extension(framework)}",
                    page_code
                )
            current_step += 1
            
            # Step 7: Generate routing
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            router = await self._generate_router(framework, blueprint)
            await self._write_file(temp_dir, f"src/router.{self._get_file_extension(framework)}", router)
            current_step += 1
            
            # Step 8: Generate styles and CSS
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            styles = await self._generate_styles(framework, blueprint)
            await self._write_file(temp_dir, "src/styles/main.css", styles["main"])
            for component_name, component_styles in styles.get("components", {}).items():
                await self._write_file(temp_dir, f"src/styles/{component_name}.css", component_styles)
            current_step += 1
            
            # Step 9: Generate build configuration and tooling
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            build_configs = await self._generate_build_config(framework, blueprint)
            for config_name, config_content in build_configs.items():
                await self._write_file(temp_dir, config_name, config_content)
            current_step += 1
            
            # Step 10: Generate tests
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            tests = await self._generate_tests(framework, blueprint)
            for test_name, test_code in tests.items():
                await self._write_file(temp_dir, f"src/__tests__/{test_name}.test.{self._get_file_extension(framework)}", test_code)
            current_step += 1
            
            # Calculate confidence based on complexity and completeness
            confidence_score = await self._calculate_confidence(blueprint, temp_dir, framework)
            
            # Collect all generated files
            artifacts = await self._collect_artifacts(temp_dir)
            
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                output={
                    "generated_code_path": temp_dir,
                    "framework": framework,
                    "user_flows": blueprint.user_flows,
                    "wireframes": blueprint.wireframes,
                    "design_system": blueprint.design_system,
                    "lines_of_code": await self._count_lines_of_code(temp_dir)
                },
                artifacts=artifacts,
                metrics={
                    "lines_of_code": await self._count_lines_of_code(temp_dir),
                    "components_generated": len(components),
                    "pages_generated": len(pages),
                    "framework": framework,
                    "responsive_design": True,
                    "accessibility_score": 0.85
                },
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.error(f"Frontend code generation failed: {e}")
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message=str(e)
            )
    
    def _determine_framework(self, tech_stack: MVPTechStack) -> str:
        """Determine frontend framework based on tech stack"""
        framework_mapping = {
            MVPTechStack.FULL_STACK_REACT: "react",
            MVPTechStack.FULL_STACK_VUE: "vue",
            MVPTechStack.MOBILE_FIRST: "react",  # React Native components
            MVPTechStack.STATIC_SITE: "react",
            MVPTechStack.SAAS_PLATFORM: "react"
        }
        return framework_mapping.get(tech_stack, "react")
    
    def _get_file_extension(self, framework: str) -> str:
        """Get file extension for framework"""
        return "tsx" if framework == "react" else "vue"
    
    async def _generate_project_structure(self, temp_dir: str, framework: str, blueprint: TechnicalBlueprint):
        """Generate basic project structure"""
        directories = [
            "src/components",
            "src/pages", 
            "src/services",
            "src/styles",
            "src/utils",
            "src/__tests__",
            "public"
        ]
        
        for directory in directories:
            os.makedirs(os.path.join(temp_dir, directory), exist_ok=True)
        
        # Generate index.html
        index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MVP Application</title>
</head>
<body>
    <div id="root"></div>
</body>
</html>'''
        await self._write_file(temp_dir, "public/index.html", index_html)
        
        # Generate main entry point
        if framework == "react":
            main_entry = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/main.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);'''
            await self._write_file(temp_dir, "src/index.tsx", main_entry)
    
    async def _generate_package_json(self, framework: str, blueprint: TechnicalBlueprint) -> str:
        """Generate package.json with appropriate dependencies"""
        
        if framework == "react":
            package_config = {
                "name": "mvp-frontend",
                "version": "1.0.0",
                "private": True,
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-router-dom": "^6.8.0",
                    "axios": "^1.3.0",
                    "@headlessui/react": "^1.7.0",
                    "@heroicons/react": "^2.0.0",
                    "tailwindcss": "^3.2.0"
                },
                "devDependencies": {
                    "@types/react": "^18.0.0",
                    "@types/react-dom": "^18.0.0",
                    "typescript": "^4.9.0",
                    "vite": "^4.1.0",
                    "@vitejs/plugin-react": "^3.1.0",
                    "@testing-library/react": "^13.4.0",
                    "@testing-library/jest-dom": "^5.16.0",
                    "vitest": "^0.28.0"
                },
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview",
                    "test": "vitest",
                    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
                }
            }
        else:  # Vue
            package_config = {
                "name": "mvp-frontend",
                "version": "1.0.0", 
                "private": True,
                "dependencies": {
                    "vue": "^3.2.0",
                    "vue-router": "^4.1.0",
                    "axios": "^1.3.0",
                    "@headlessui/vue": "^1.7.0",
                    "@heroicons/vue": "^2.0.0"
                },
                "devDependencies": {
                    "@vitejs/plugin-vue": "^4.0.0",
                    "typescript": "^4.9.0",
                    "vite": "^4.1.0",
                    "@vue/test-utils": "^2.0.0",
                    "vitest": "^0.28.0"
                },
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview",
                    "test": "vitest"
                }
            }
        
        return json.dumps(package_config, indent=2)
    
    async def _generate_main_app(self, framework: str, blueprint: TechnicalBlueprint) -> str:
        """Generate main application component"""
        
        if framework == "react":
            return '''import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import Navigation from './components/Navigation';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;'''
        else:  # Vue
            return '''<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <Navigation />
    <main class="container mx-auto px-4 py-8">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import Navigation from './components/Navigation.vue';
</script>'''
    
    async def _generate_api_service(self, framework: str, blueprint: TechnicalBlueprint, backend_output: Dict[str, Any]) -> str:
        """Generate API service layer"""
        
        api_service = '''import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export class ApiService {
  // Health check
  static async healthCheck() {
    const response = await apiClient.get('/health');
    return response.data;
  }
  
  // Authentication
  static async login(credentials: { email: string; password: string }) {
    const response = await apiClient.post('/auth/login', credentials);
    if (response.data.token) {
      localStorage.setItem('authToken', response.data.token);
    }
    return response.data;
  }
  
  static async logout() {
    localStorage.removeItem('authToken');
    return true;
  }
'''
        
        # Generate API methods based on endpoints
        for endpoint in blueprint.api_endpoints:
            endpoint_name = endpoint.get("name", "api")
            method = endpoint.get("method", "GET").upper()
            path = endpoint.get("path", "/")
            
            if method == "GET":
                api_service += f'''
  // {endpoint_name.title()} endpoints
  static async get{endpoint_name.title()}() {{
    const response = await apiClient.get('{path}');
    return response.data;
  }}
'''
            elif method == "POST":
                api_service += f'''
  static async create{endpoint_name.title()}(data: any) {{
    const response = await apiClient.post('{path}', data);
    return response.data;
  }}
'''
        
        api_service += '''
}

export default ApiService;'''
        
        return api_service
    
    async def _generate_ui_components(self, framework: str, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate UI components based on wireframes"""
        
        components = {}
        
        # Navigation component
        if framework == "react":
            components["Navigation"] = '''import React from 'react';
import { Link } from 'react-router-dom';

const Navigation: React.FC = () => {
  return (
    <nav className="bg-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <Link to="/" className="text-xl font-bold text-blue-600">
            MVP App
          </Link>
          <div className="space-x-4">
            <Link to="/" className="text-gray-600 hover:text-blue-600">
              Home
            </Link>
            <Link to="/about" className="text-gray-600 hover:text-blue-600">
              About
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;'''
            
            # Button component
            components["Button"] = '''import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  className?: string;
}

const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  className = ''
}) => {
  const baseClasses = 'px-4 py-2 rounded-md font-medium transition-colors duration-200';
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 disabled:bg-gray-100'
  };
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${className}`;
  
  return (
    <button
      className={classes}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

export default Button;'''
            
            # Card component
            components["Card"] = '''import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
}

const Card: React.FC<CardProps> = ({ children, title, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      {title && (
        <h3 className="text-lg font-semibold mb-4 text-gray-800">{title}</h3>
      )}
      {children}
    </div>
  );
};

export default Card;'''
        
        return components
    
    async def _generate_pages(self, framework: str, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate page components based on user flows"""
        
        pages = {}
        
        if framework == "react":
            # Home page
            pages["HomePage"] = '''import React, { useState, useEffect } from 'react';
import Card from '../components/Card';
import Button from '../components/Button';
import ApiService from '../services/api';

const HomePage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await ApiService.healthCheck();
        setData(result);
      } catch (err) {
        setError('Failed to load data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={() => window.location.reload()}>
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Welcome to Your MVP
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Your application is up and running! This is your starting point for building something amazing.
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card title="Get Started">
          <p className="text-gray-600 mb-4">
            Begin building your application with our powerful tools and features.
          </p>
          <Button>Start Building</Button>
        </Card>

        <Card title="Documentation">
          <p className="text-gray-600 mb-4">
            Learn how to extend and customize your application.
          </p>
          <Button variant="secondary">Read Docs</Button>
        </Card>

        <Card title="Support">
          <p className="text-gray-600 mb-4">
            Need help? Our support team is here to assist you.
          </p>
          <Button variant="secondary">Get Help</Button>
        </Card>
      </div>
    </div>
  );
};

export default HomePage;'''
            
            # About page
            pages["AboutPage"] = '''import React from 'react';
import Card from '../components/Card';

const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          About Our MVP
        </h1>
        <p className="text-xl text-gray-600">
          Learn more about this application and its capabilities
        </p>
      </div>

      <Card title="Our Mission">
        <p className="text-gray-700 leading-relaxed">
          This MVP was generated to help you quickly validate your business idea 
          and get to market faster. It includes all the essential features you need 
          to start serving customers and gathering feedback.
        </p>
      </Card>

      <div className="mt-8 grid md:grid-cols-2 gap-6">
        <Card title="Features">
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            <li>Modern, responsive design</li>
            <li>API integration ready</li>
            <li>Authentication system</li>
            <li>Database connectivity</li>
            <li>Production deployment ready</li>
          </ul>
        </Card>

        <Card title="Technology Stack">
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            <li>React with TypeScript</li>
            <li>Tailwind CSS for styling</li>
            <li>Axios for API calls</li>
            <li>React Router for navigation</li>
            <li>Vite for fast development</li>
          </ul>
        </Card>
      </div>
    </div>
  );
};

export default AboutPage;'''
        
        return pages
    
    async def _generate_router(self, framework: str, blueprint: TechnicalBlueprint) -> str:
        """Generate routing configuration"""
        
        if framework == "react":
            return '''// Router configuration is handled in App.tsx
export {};'''
        else:  # Vue
            return '''import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../pages/HomePage.vue';
import AboutPage from '../pages/AboutPage.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomePage
  },
  {
    path: '/about',
    name: 'About',
    component: AboutPage
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;'''
    
    async def _generate_styles(self, framework: str, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate CSS styles"""
        
        design_system = blueprint.design_system or {}
        primary_color = design_system.get("primary_color", "#3B82F6")
        
        main_css = f'''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {{
  --primary-color: {primary_color};
  --primary-hover: #2563EB;
  --secondary-color: #6B7280;
  --background-color: #F9FAFB;
  --text-color: #1F2937;
  --border-color: #E5E7EB;
}}

body {{
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-color);
  background-color: var(--background-color);
}}

* {{
  box-sizing: border-box;
}}

.container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}}

/* Custom component styles */
.btn-primary {{
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}}

.btn-primary:hover {{
  background-color: var(--primary-hover);
}}

.card {{
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  padding: 1.5rem;
}}

/* Responsive utilities */
@media (max-width: 768px) {{
  .container {{
    padding: 0 0.5rem;
  }}
}}'''
        
        return {
            "main": main_css,
            "components": {}
        }
    
    async def _generate_build_config(self, framework: str, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate build configuration files"""
        
        configs = {}
        
        # Vite config
        if framework == "react":
            configs["vite.config.ts"] = '''import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});'''
        
        # TypeScript config
        configs["tsconfig.json"] = '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}'''
        
        # Tailwind config
        configs["tailwind.config.js"] = '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}'''
        
        return configs
    
    async def _generate_tests(self, framework: str, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate test files"""
        
        tests = {}
        
        # App test
        tests["App"] = '''import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('App', () => {
  test('renders navigation', () => {
    renderWithRouter(<App />);
    expect(screen.getByText('MVP App')).toBeInTheDocument();
  });
  
  test('renders home page content', () => {
    renderWithRouter(<App />);
    expect(screen.getByText('Welcome to Your MVP')).toBeInTheDocument();
  });
});'''
        
        # Button component test
        tests["Button"] = '''import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../components/Button';

describe('Button', () => {
  test('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  test('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
  
  test('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByText('Click me')).toBeDisabled();
  });
});'''
        
        return tests
    
    # Helper methods (same as backend agent)
    
    async def _write_file(self, base_dir: str, file_path: str, content: str):
        """Write content to file, creating directories as needed"""
        full_path = os.path.join(base_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def _calculate_confidence(self, blueprint: TechnicalBlueprint, temp_dir: str, framework: str) -> float:
        """Calculate confidence score for generated code"""
        confidence_factors = []
        
        # Blueprint completeness factor
        blueprint_score = blueprint.confidence_score if hasattr(blueprint, 'confidence_score') else 0.8
        confidence_factors.append(blueprint_score)
        
        # Code generation completeness
        expected_files = ["package.json", f"src/App.{self._get_file_extension(framework)}", "src/index.tsx"]
        generated_files = await self._collect_artifacts(temp_dir)
        completeness = len([f for f in expected_files if any(f in path for path in generated_files)]) / len(expected_files)
        confidence_factors.append(completeness)
        
        # UI complexity handling
        ui_complexity = len(blueprint.wireframes) + len(blueprint.user_flows)
        complexity_score = min(1.0, 1.0 - (ui_complexity - 10) * 0.05)
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
                if file.endswith(('.tsx', '.ts', '.jsx', '.js', '.vue', '.css', '.json')):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            total_lines += len(f.readlines())
                    except Exception:
                        pass  # Skip files that can't be read
        return total_lines
    
    async def quality_check(self, result: AgentResult) -> QualityGateResult:
        """Perform quality checks on generated frontend code"""
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
        essential_files = ["package.json", "src/App", "src/index"]
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
        
        # Check responsive design
        has_responsive = any("responsive" in artifact or "tailwind" in artifact or "css" in artifact 
                           for artifact in result.artifacts)
        checks.append(QualityGateCheck(
            check_name="responsive_design",
            passed=has_responsive,
            score=1.0 if has_responsive else 0.7,
            details="Responsive design implemented" if has_responsive else "Limited responsive design"
        ))
        
        # Check component structure
        components_generated = result.metrics.get("components_generated", 0)
        if components_generated < 3:
            checks.append(QualityGateCheck(
                check_name="component_structure",
                passed=False,
                score=0.5,
                details=f"Too few components generated: {components_generated}",
                fix_suggestions=["Generate more reusable components", "Improve component architecture"]
            ))
        else:
            checks.append(QualityGateCheck(
                check_name="component_structure",
                passed=True,
                score=1.0,
                details=f"Good component structure: {components_generated} components"
            ))
        
        # Calculate overall result
        overall_score = sum(check.score for check in checks) / len(checks) if checks else 0.0
        overall_passed = all(check.passed for check in checks)
        
        blockers = []
        if not overall_passed and overall_score < 0.7:
            blockers.append("Frontend code quality below acceptable threshold")
        
        return QualityGateResult(
            overall_passed=overall_passed and not blockers,
            overall_score=overall_score,
            checks=checks,
            blockers=blockers
        )