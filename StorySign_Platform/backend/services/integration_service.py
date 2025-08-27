"""
Integration Service
Handles external integrations including OAuth2, SAML, LTI, webhooks, and data synchronization
"""

import logging
import asyncio
import json
import hmac
import hashlib
import base64
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlencode, parse_qs
import aiohttp
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from core.database_service import DatabaseService
from models.user import User
from models.integrations import (
    OAuthProvider, SAMLProvider, LTIProvider, WebhookConfig, 
    ExternalIntegration, WebhookDelivery
)

logger = logging.getLogger(__name__)

class IntegrationService:
    """Service for handling external integrations"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self.oauth_providers: Dict[str, Any] = {}
        self.saml_config: Optional[SAMLProvider] = None
        self.lti_config: Optional[LTIProvider] = None
        self.webhooks: Dict[str, WebhookConfig] = {}
        
    async def initialize(self):
        """Initialize integration service"""
        try:
            # Load OAuth providers
            await self._load_oauth_providers()
            
            # Load SAML configuration
            await self._load_saml_config()
            
            # Load LTI configuration
            await self._load_lti_config()
            
            # Load webhooks
            await self._load_webhooks()
            
            logger.info("Integration service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize integration service: {e}")
            raise
    
    # OAuth2 methods
    
    async def get_oauth_providers(self) -> List[Dict[str, Any]]:
        """Get list of configured OAuth providers"""
        return list(self.oauth_providers.values())
    
    async def create_oauth_provider(self, provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new OAuth provider configuration"""
        try:
            # Store in database
            provider_id = await self.db.create_oauth_provider(provider_config)
            
            # Add to memory cache
            self.oauth_providers[provider_config["name"]] = {
                "id": provider_id,
                **provider_config
            }
            
            return {"id": provider_id, **provider_config}
        except Exception as e:
            logger.error(f"Error creating OAuth provider: {e}")
            raise
    
    async def get_oauth_authorization_url(
        self, 
        provider_name: str, 
        redirect_uri: str, 
        state: Optional[str] = None
    ) -> str:
        """Generate OAuth authorization URL"""
        if provider_name not in self.oauth_providers:
            raise ValueError(f"OAuth provider '{provider_name}' not found")
        
        provider = self.oauth_providers[provider_name]
        
        params = {
            "client_id": provider["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(provider["scopes"])
        }
        
        if state:
            params["state"] = state
        
        return f"{provider['authorization_url']}?{urlencode(params)}"
    
    async def exchange_oauth_code(self, provider_name: str, code: str) -> Dict[str, Any]:
        """Exchange OAuth authorization code for tokens"""
        if provider_name not in self.oauth_providers:
            raise ValueError(f"OAuth provider '{provider_name}' not found")
        
        provider = self.oauth_providers[provider_name]
        
        async with aiohttp.ClientSession() as session:
            data = {
                "client_id": provider["client_id"],
                "client_secret": provider["client_secret"],
                "code": code,
                "grant_type": "authorization_code"
            }
            
            async with session.post(provider["token_url"], data=data) as response:
                if response.status != 200:
                    raise ValueError("Failed to exchange OAuth code for tokens")
                
                return await response.json()
    
    async def get_oauth_user_info(self, provider_name: str, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        if provider_name not in self.oauth_providers:
            raise ValueError(f"OAuth provider '{provider_name}' not found")
        
        provider = self.oauth_providers[provider_name]
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with session.get(provider["user_info_url"], headers=headers) as response:
                if response.status != 200:
                    raise ValueError("Failed to get user info from OAuth provider")
                
                return await response.json()
    
    # SAML methods
    
    async def get_saml_metadata(self) -> str:
        """Generate SAML metadata XML"""
        if not self.saml_config:
            raise ValueError("SAML not configured")
        
        # Generate SAML metadata XML
        metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     entityID="{self.saml_config.entity_id}">
    <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>{self.saml_config.name_id_format}</md:NameIDFormat>
        <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                   Location="{self.saml_config.sso_url}"
                                   index="0" isDefault="true"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""
        
        return metadata
    
    async def parse_saml_response(self, saml_response: str) -> Dict[str, Any]:
        """Parse and validate SAML response"""
        if not self.saml_config:
            raise ValueError("SAML not configured")
        
        try:
            # Decode base64 SAML response
            decoded_response = base64.b64decode(saml_response)
            
            # Parse XML
            root = ET.fromstring(decoded_response)
            
            # Extract user attributes (simplified implementation)
            # In production, you would validate signatures and assertions
            attributes = {}
            
            # Find assertion elements
            for assertion in root.findall(".//{urn:oasis:names:tc:SAML:2.0:assertion}Assertion"):
                for attr_stmt in assertion.findall(".//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement"):
                    for attr in attr_stmt.findall(".//{urn:oasis:names:tc:SAML:2.0:assertion}Attribute"):
                        attr_name = attr.get("Name")
                        attr_value = attr.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue")
                        if attr_value is not None:
                            attributes[attr_name] = attr_value.text
            
            return attributes
            
        except Exception as e:
            logger.error(f"Error parsing SAML response: {e}")
            raise ValueError("Invalid SAML response")
    
    # LTI methods
    
    async def validate_lti_signature(self, lti_params: Dict[str, Any], url: str) -> bool:
        """Validate LTI OAuth signature"""
        if not self.lti_config:
            return False
        
        try:
            # Extract OAuth parameters
            oauth_signature = lti_params.pop("oauth_signature", "")
            
            # Build base string for signature
            normalized_params = "&".join([
                f"{k}={v}" for k, v in sorted(lti_params.items())
            ])
            
            base_string = f"POST&{url}&{normalized_params}"
            
            # Calculate expected signature
            key = f"{self.lti_config.consumer_secret}&"
            expected_signature = base64.b64encode(
                hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
            ).decode()
            
            return hmac.compare_digest(oauth_signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error validating LTI signature: {e}")
            return False
    
    # Webhook methods
    
    async def get_webhooks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get webhooks for user"""
        try:
            webhooks = await self.db.get_user_webhooks(user_id)
            return [webhook.dict() for webhook in webhooks]
        except Exception as e:
            logger.error(f"Error getting webhooks: {e}")
            raise
    
    async def create_webhook(self, webhook_config: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create webhook configuration"""
        try:
            webhook_id = await self.db.create_webhook(webhook_config, user_id)
            
            # Add to memory cache
            self.webhooks[webhook_id] = webhook_config
            
            return {"id": webhook_id, **webhook_config}
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            raise
    
    async def test_webhook(self, webhook_id: str, test_event: Dict[str, Any]) -> Dict[str, Any]:
        """Test webhook delivery"""
        try:
            webhook = await self.db.get_webhook(webhook_id)
            if not webhook:
                raise ValueError("Webhook not found")
            
            # Send test event
            result = await self._deliver_webhook(webhook, test_event)
            
            return {
                "success": result["success"],
                "status_code": result.get("status_code"),
                "response_time": result.get("response_time"),
                "error": result.get("error")
            }
        except Exception as e:
            logger.error(f"Error testing webhook: {e}")
            raise
    
    async def trigger_webhook_event(self, event: Dict[str, Any]):
        """Trigger webhook event to all subscribed webhooks"""
        try:
            # Get all webhooks subscribed to this event type
            webhooks = await self.db.get_webhooks_for_event(event["event_type"])
            
            # Deliver to all webhooks
            tasks = []
            for webhook in webhooks:
                if webhook.enabled:
                    tasks.append(self._deliver_webhook(webhook, event))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Error triggering webhook event: {e}")
    
    async def _deliver_webhook(self, webhook: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """Deliver webhook event"""
        start_time = datetime.utcnow()
        
        try:
            # Prepare payload
            payload = json.dumps(event)
            
            # Calculate signature if secret is provided
            headers = {"Content-Type": "application/json"}
            if webhook.get("secret"):
                signature = hmac.new(
                    webhook["secret"].encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            # Add custom headers
            if webhook.get("headers"):
                headers.update(webhook["headers"])
            
            # Send webhook
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=webhook.get("timeout", 30))) as session:
                async with session.post(webhook["url"], data=payload, headers=headers) as response:
                    response_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    # Log delivery
                    await self.db.log_webhook_delivery(
                        webhook["id"],
                        event["event_type"],
                        response.status,
                        response_time,
                        success=(200 <= response.status < 300)
                    )
                    
                    return {
                        "success": 200 <= response.status < 300,
                        "status_code": response.status,
                        "response_time": response_time
                    }
                    
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log failed delivery
            await self.db.log_webhook_delivery(
                webhook["id"],
                event["event_type"],
                0,
                response_time,
                success=False,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }
    
    # Widget methods
    
    async def get_widget_config(self, widget_type: str, domain: str) -> Dict[str, Any]:
        """Get widget configuration for domain"""
        try:
            config = await self.db.get_widget_config(widget_type, domain)
            if not config:
                raise ValueError(f"Widget '{widget_type}' not configured for domain '{domain}'")
            
            return config
        except Exception as e:
            logger.error(f"Error getting widget config: {e}")
            raise
    
    async def generate_widget_html(
        self,
        widget_type: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        theme: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> str:
        """Generate embeddable widget HTML"""
        
        # Widget templates
        widget_templates = {
            "practice": self._generate_practice_widget,
            "progress": self._generate_progress_widget,
            "leaderboard": self._generate_leaderboard_widget
        }
        
        if widget_type not in widget_templates:
            raise ValueError(f"Unsupported widget type: {widget_type}")
        
        return await widget_templates[widget_type](
            config, user_id, group_id, theme, width, height
        )
    
    async def generate_embed_script(self, widget_type: str, domain: str) -> str:
        """Generate JavaScript embed script"""
        
        script = f"""
(function() {{
    var StorySignWidget = {{
        init: function(options) {{
            var iframe = document.createElement('iframe');
            iframe.src = '/api/v1/integrations/embed/widget/{widget_type}?' + 
                        'domain=' + encodeURIComponent('{domain}') +
                        (options.userId ? '&user_id=' + encodeURIComponent(options.userId) : '') +
                        (options.groupId ? '&group_id=' + encodeURIComponent(options.groupId) : '') +
                        (options.theme ? '&theme=' + encodeURIComponent(options.theme) : '') +
                        (options.width ? '&width=' + options.width : '') +
                        (options.height ? '&height=' + options.height : '');
            
            iframe.width = options.width || '100%';
            iframe.height = options.height || '400';
            iframe.frameBorder = '0';
            iframe.style.border = 'none';
            
            var container = document.getElementById(options.containerId);
            if (container) {{
                container.appendChild(iframe);
            }}
        }}
    }};
    
    window.StorySignWidget = StorySignWidget;
}})();
"""
        
        return script
    
    # Data synchronization methods
    
    async def sync_external_users(
        self, 
        users: List[Dict[str, Any]], 
        source_system: str
    ) -> Dict[str, Any]:
        """Synchronize users from external system"""
        
        created = 0
        updated = 0
        errors = []
        
        for user_data in users:
            try:
                # Check if user exists
                existing_user = await self.db.get_user_by_external_id(
                    user_data["external_id"], 
                    source_system
                )
                
                if existing_user:
                    # Update existing user
                    await self.db.update_user(existing_user.id, user_data)
                    updated += 1
                else:
                    # Create new user
                    await self.db.create_user_from_external(user_data, source_system)
                    created += 1
                    
            except Exception as e:
                errors.append({
                    "external_id": user_data.get("external_id"),
                    "error": str(e)
                })
        
        return {
            "created": created,
            "updated": updated,
            "errors": errors
        }
    
    async def get_user_progress_for_sync(self, user_id: str, format: str = "json") -> Union[Dict, str]:
        """Get user progress data for external synchronization"""
        
        try:
            # Get user progress data
            progress_data = await self.db.get_user_progress_detailed(user_id)
            
            if format == "json":
                return progress_data
            elif format == "csv":
                return self._convert_progress_to_csv(progress_data)
            elif format == "xml":
                return self._convert_progress_to_xml(progress_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error getting user progress for sync: {e}")
            raise
    
    async def sync_user_progress(
        self, 
        user_id: str, 
        progress_data: Dict[str, Any], 
        source_system: str
    ) -> Dict[str, Any]:
        """Synchronize user progress from external system"""
        
        try:
            result = await self.db.sync_user_progress(user_id, progress_data, source_system)
            return result
        except Exception as e:
            logger.error(f"Error synchronizing user progress: {e}")
            raise
    
    # Private helper methods
    
    async def _load_oauth_providers(self):
        """Load OAuth providers from database"""
        try:
            providers = await self.db.get_oauth_providers()
            for provider in providers:
                self.oauth_providers[provider.name] = provider.dict()
        except Exception as e:
            logger.error(f"Error loading OAuth providers: {e}")
    
    async def _load_saml_config(self):
        """Load SAML configuration from database"""
        try:
            self.saml_config = await self.db.get_saml_config()
        except Exception as e:
            logger.error(f"Error loading SAML config: {e}")
    
    async def _load_lti_config(self):
        """Load LTI configuration from database"""
        try:
            self.lti_config = await self.db.get_lti_config()
        except Exception as e:
            logger.error(f"Error loading LTI config: {e}")
    
    async def _load_webhooks(self):
        """Load webhooks from database"""
        try:
            webhooks = await self.db.get_all_webhooks()
            for webhook in webhooks:
                self.webhooks[webhook.id] = webhook.dict()
        except Exception as e:
            logger.error(f"Error loading webhooks: {e}")
    
    async def _generate_practice_widget(
        self, 
        config: Dict[str, Any], 
        user_id: Optional[str], 
        group_id: Optional[str], 
        theme: Optional[str], 
        width: Optional[int], 
        height: Optional[int]
    ) -> str:
        """Generate practice widget HTML"""
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>StorySign Practice Widget</title>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        .widget-container {{ 
            width: {width or '100%'}px; 
            height: {height or '400'}px; 
            border: 1px solid #ddd; 
            border-radius: 8px; 
            padding: 20px; 
            box-sizing: border-box;
        }}
        .practice-area {{ 
            width: 100%; 
            height: 200px; 
            background: #f5f5f5; 
            border-radius: 4px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }}
        .controls {{ margin-top: 20px; text-align: center; }}
        button {{ 
            background: #007bff; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 4px; 
            cursor: pointer; 
            margin: 0 5px; 
        }}
        button:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <div class="widget-container">
        <h3>ASL Practice Session</h3>
        <div class="practice-area">
            <p>Practice area - Camera feed would appear here</p>
        </div>
        <div class="controls">
            <button onclick="startPractice()">Start Practice</button>
            <button onclick="stopPractice()">Stop</button>
        </div>
    </div>
    
    <script>
        function startPractice() {{
            console.log('Starting practice session');
            // Integration with parent window
            if (window.parent) {{
                window.parent.postMessage({{
                    type: 'storysign-widget-event',
                    event: 'practice-started',
                    userId: '{user_id or ""}',
                    groupId: '{group_id or ""}'
                }}, '*');
            }}
        }}
        
        function stopPractice() {{
            console.log('Stopping practice session');
            if (window.parent) {{
                window.parent.postMessage({{
                    type: 'storysign-widget-event',
                    event: 'practice-stopped',
                    userId: '{user_id or ""}',
                    groupId: '{group_id or ""}'
                }}, '*');
            }}
        }}
    </script>
</body>
</html>
"""
    
    async def _generate_progress_widget(
        self, 
        config: Dict[str, Any], 
        user_id: Optional[str], 
        group_id: Optional[str], 
        theme: Optional[str], 
        width: Optional[int], 
        height: Optional[int]
    ) -> str:
        """Generate progress widget HTML"""
        
        # Get user progress data if user_id provided
        progress_data = {}
        if user_id:
            try:
                progress_data = await self.db.get_user_progress_summary(user_id)
            except Exception as e:
                logger.error(f"Error getting progress data: {e}")
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>StorySign Progress Widget</title>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        .widget-container {{ 
            width: {width or '100%'}px; 
            height: {height or '300'}px; 
            border: 1px solid #ddd; 
            border-radius: 8px; 
            padding: 20px; 
            box-sizing: border-box;
        }}
        .progress-item {{ 
            margin: 10px 0; 
            padding: 10px; 
            background: #f8f9fa; 
            border-radius: 4px; 
        }}
        .progress-bar {{ 
            width: 100%; 
            height: 20px; 
            background: #e9ecef; 
            border-radius: 10px; 
            overflow: hidden; 
        }}
        .progress-fill {{ 
            height: 100%; 
            background: #28a745; 
            transition: width 0.3s ease; 
        }}
    </style>
</head>
<body>
    <div class="widget-container">
        <h3>Learning Progress</h3>
        <div class="progress-item">
            <div>Stories Completed: {progress_data.get('stories_completed', 0)}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {min(100, progress_data.get('stories_completed', 0) * 10)}%"></div>
            </div>
        </div>
        <div class="progress-item">
            <div>Practice Time: {progress_data.get('total_practice_time', 0)} minutes</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {min(100, progress_data.get('total_practice_time', 0) / 10)}%"></div>
            </div>
        </div>
        <div class="progress-item">
            <div>Skill Level: {progress_data.get('skill_level', 'Beginner')}</div>
        </div>
    </div>
</body>
</html>
"""
    
    async def _generate_leaderboard_widget(
        self, 
        config: Dict[str, Any], 
        user_id: Optional[str], 
        group_id: Optional[str], 
        theme: Optional[str], 
        width: Optional[int], 
        height: Optional[int]
    ) -> str:
        """Generate leaderboard widget HTML"""
        
        # Get leaderboard data
        leaderboard_data = []
        if group_id:
            try:
                leaderboard_data = await self.db.get_group_leaderboard(group_id)
            except Exception as e:
                logger.error(f"Error getting leaderboard data: {e}")
        
        leaderboard_html = ""
        for i, entry in enumerate(leaderboard_data[:10]):  # Top 10
            leaderboard_html += f"""
            <div class="leaderboard-item">
                <span class="rank">#{i+1}</span>
                <span class="name">{entry.get('name', 'Anonymous')}</span>
                <span class="score">{entry.get('score', 0)} pts</span>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>StorySign Leaderboard Widget</title>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        .widget-container {{ 
            width: {width or '100%'}px; 
            height: {height or '400'}px; 
            border: 1px solid #ddd; 
            border-radius: 8px; 
            padding: 20px; 
            box-sizing: border-box;
        }}
        .leaderboard-item {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 10px; 
            margin: 5px 0; 
            background: #f8f9fa; 
            border-radius: 4px; 
        }}
        .rank {{ font-weight: bold; color: #007bff; }}
        .name {{ flex-grow: 1; margin-left: 10px; }}
        .score {{ font-weight: bold; color: #28a745; }}
    </style>
</head>
<body>
    <div class="widget-container">
        <h3>Leaderboard</h3>
        {leaderboard_html or '<p>No leaderboard data available</p>'}
    </div>
</body>
</html>
"""
    
    def _convert_progress_to_csv(self, progress_data: Dict[str, Any]) -> str:
        """Convert progress data to CSV format"""
        
        csv_lines = ["Date,Session Type,Score,Duration,Stories Completed"]
        
        for session in progress_data.get("sessions", []):
            csv_lines.append(
                f"{session.get('date', '')},{session.get('type', '')},"
                f"{session.get('score', 0)},{session.get('duration', 0)},"
                f"{session.get('stories_completed', 0)}"
            )
        
        return "\n".join(csv_lines)
    
    def _convert_progress_to_xml(self, progress_data: Dict[str, Any]) -> str:
        """Convert progress data to XML format"""
        
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<progress>']
        
        xml_lines.append(f"<user_id>{progress_data.get('user_id', '')}</user_id>")
        xml_lines.append(f"<total_sessions>{progress_data.get('total_sessions', 0)}</total_sessions>")
        xml_lines.append(f"<total_practice_time>{progress_data.get('total_practice_time', 0)}</total_practice_time>")
        
        xml_lines.append('<sessions>')
        for session in progress_data.get("sessions", []):
            xml_lines.append('<session>')
            xml_lines.append(f"<date>{session.get('date', '')}</date>")
            xml_lines.append(f"<type>{session.get('type', '')}</type>")
            xml_lines.append(f"<score>{session.get('score', 0)}</score>")
            xml_lines.append(f"<duration>{session.get('duration', 0)}</duration>")
            xml_lines.append('</session>')
        xml_lines.append('</sessions>')
        
        xml_lines.append('</progress>')
        
        return "\n".join(xml_lines)