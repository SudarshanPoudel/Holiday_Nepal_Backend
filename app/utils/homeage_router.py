from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HolidayNepal Backend</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0f0f0f;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
        }
        
        .container {
            text-align: center;
            padding: 3rem;
            max-width: 700px;
            animation: fadeInUp 0.6s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .header {
            margin-bottom: 2rem;
        }
        
        .logo {
            font-size: 3rem;
            margin-bottom: 1rem;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.05);
            }
            100% {
                transform: scale(1);
            }
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
            background: linear-gradient(45deg, #ffffff, #a0a0a0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            color: #a0a0a0;
        }
        
        .status {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: #1a1a1a;
            border-radius: 20px;
            font-size: 0.9rem;
            color: #4ade80;
            border: 1px solid #22c55e;
            margin-bottom: 2rem;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: #4ade80;
            border-radius: 50%;
            animation: blink 1.5s infinite;
        }
        
        @keyframes blink {
            0%, 50% {
                opacity: 1;
            }
            51%, 100% {
                opacity: 0.3;
            }
        }
        
        .links {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .link-button {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem 1.5rem;
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            color: #ffffff;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            text-align: left;
        }
        
        .link-button:hover {
            background: #2a2a2a;
            border-color: #3a3a3a;
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1);
        }
        
        .link-button:active {
            transform: translateY(0);
        }
        
        .link-icon {
            font-size: 1.5rem;
            flex-shrink: 0;
        }
        
        .link-content {
            flex: 1;
        }
        
        .link-title {
            font-size: 1rem;
            margin-bottom: 0.25rem;
            color: #ffffff;
        }
        
        .link-desc {
            font-size: 0.85rem;
            color: #888888;
            line-height: 1.3;
        }
        
        .footer {
            margin-top: 2.5rem;
            padding-top: 2rem;
            border-top: 1px solid #1a1a1a;
            font-size: 0.9rem;
            color: #666666;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 1rem;
                padding: 2rem;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .links {
                grid-template-columns: 1fr;
            }
            
            .link-button {
                text-align: center;
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .link-content {
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🏔️</div>
            <h1>HolidayNepal Backend</h1>
            <p class="subtitle">AI-Powered Trip Planner for Nepal</p>
            <div class="status">
                <div class="status-dot"></div>
                Backend Running
            </div>
        </div>
        
        <div class="links">
            <a href="/docs" class="link-button">
                <div class="link-icon">📚</div>
                <div class="link-content">
                    <div class="link-title">API Documentation</div>
                    <div class="link-desc">Interactive Swagger UI for testing endpoints</div>
                </div>
            </a>
            
            <a href="/redoc" class="link-button">
                <div class="link-icon">📖</div>
                <div class="link-content">
                    <div class="link-title">ReDoc</div>
                    <div class="link-desc">Clean, readable API documentation</div>
                </div>
            </a>
            
            <a href="http://localhost:7474/browser/" class="link-button" target="_blank">
                <div class="link-icon">🕸️</div>
                <div class="link-content">
                    <div class="link-title">Neo4j Browser</div>
                    <div class="link-desc">Visualize and query the graph database</div>
                </div>
            </a>
            
            <a href="/openapi.json" class="link-button">
                <div class="link-icon">⚙️</div>
                <div class="link-content">
                    <div class="link-title">OpenAPI Schema</div>
                    <div class="link-desc">Raw JSON schema specification</div>
                </div>
            </a>
        </div>
        
        <div class="footer">
            <p>Ready to plan your next adventure in Nepal 🇳🇵</p>
        </div>
    </div>
</body>
</html>"""