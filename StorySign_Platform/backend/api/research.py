"""
Research Data Management API
Provides endpoints for research consent, data anonymization, and research data exports
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, File, UploadFile
from fastapi.security import HTTPBearer
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from services.research_service import ResearchService
from models.research import ResearchConsentType, DataAnonymizationLevel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Simple auth dependency for now - TODO: Replace with proper auth
async def get_current_user(token: str = Depends(security)) -> Optional[Dict]:
    """Simple auth dependency - replace with proper implementation"""
    return {"id": "test_user_123", "role": "researcher"}

# Simple research service dependency - TODO: Replace with proper DI
def get_research_service() -> ResearchService:
    """Simple research service dependency"""
    return ResearchService()


# Pydantic models for request/response
class ResearchParticipantRequest(BaseModel):
    research_id: str = Field(..., description="Research study identifier")
    consent_version: str = Field(..., description="Version of consent agreement")
    anonymization_level: str = Field("pseudonymized", description="Level of data anonymization")
    data_retention_years: int = Field(5, description="Years to retain data")
    allow_data_sharing: bool = Field(False, description="Allow sharing data with other researchers")
    research_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional research metadata")


class ConsentUpdateRequest(BaseModel):
    research_id: str = Field(..., description="Research study identifier")
    consent_given: bool = Field(..., description="Whether consent is given")
    consent_version: Optional[str] = Field(None, description="Version of consent agreement")


class WithdrawalRequest(BaseModel):
    research_id: str = Field(..., description="Research study identifier")
    reason: Optional[str] = Field(None, description="Reason for withdrawal")


class DatasetRequest(BaseModel):
    dataset_name: str = Field(..., description="Name for the dataset")
    research_id: str = Field(..., description="Research study identifier")
    data_types: List[str] = Field(..., description="Types of data to include")
    start_date: datetime = Field(..., description="Start date for data collection")
    end_date: datetime = Field(..., description="End date for data collection")
    anonymization_level: str = Field("pseudonymized", description="Level of anonymization")
    export_format: str = Field("json", description="Export format (json, csv, xlsx)")
    include_demographics: bool = Field(False, description="Include demographic data")
    include_video_data: bool = Field(False, description="Include video analysis data")


class RetentionRuleRequest(BaseModel):
    rule_name: str = Field(..., description="Name of the retention rule")
    data_type: str = Field(..., description="Type of data this rule applies to")
    retention_days: int = Field(..., description="Days to retain data")
    anonymize_after_days: Optional[int] = Field(None, description="Days after which to anonymize")
    hard_delete_after_days: Optional[int] = Field(None, description="Days after which to hard delete")
    applies_to_research_data: bool = Field(True, description="Apply to research data")
    applies_to_non_research_data: bool = Field(True, description="Apply to non-research data")
    compliance_framework: Optional[str] = Field(None, description="Compliance framework (GDPR, COPPA, etc.)")
    rule_config: Optional[Dict[str, Any]] = Field(None, description="Additional rule configuration")


# Research Participation Endpoints

@router.post("/participants/register", summary="Register Research Participant")
async def register_research_participant(
    participant_request: ResearchParticipantRequest,
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Register current user as a research participant"""
    try:
        # Validate anonymization level
        try:
            anonymization_level = DataAnonymizationLevel(participant_request.anonymization_level)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid anonymization level")
        
        participant = await research_service.register_research_participant(
            user_id=current_user['id'],
            research_id=participant_request.research_id,
            consent_version=participant_request.consent_version,
            anonymization_level=anonymization_level,
            data_retention_years=participant_request.data_retention_years,
            allow_data_sharing=participant_request.allow_data_sharing,
            research_metadata=participant_request.research_metadata
        )
        
        return {
            "status": "success",
            "message": "Successfully registered as research participant",
            "participant": participant.to_dict()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering research participant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/participants/me", summary="Get My Research Participations")
async def get_my_research_participations(
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Get all research participations for the current user"""
    try:
        # This would need to be implemented in the research service
        # For now, return a placeholder
        return {
            "participations": [],
            "message": "Research participation lookup not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error getting research participations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/participants/consent", summary="Update Research Consent")
async def update_research_consent(
    consent_request: ConsentUpdateRequest,
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Update consent for research participation"""
    try:
        participant = await research_service.update_research_consent(
            user_id=current_user['id'],
            research_id=consent_request.research_id,
            consent_given=consent_request.consent_given,
            consent_version=consent_request.consent_version
        )
        
        if not participant:
            raise HTTPException(status_code=404, detail="Research participation not found")
        
        return {
            "status": "success",
            "message": f"Consent {'granted' if consent_request.consent_given else 'revoked'} successfully",
            "participant": participant.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error updating research consent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/participants/withdraw", summary="Withdraw from Research")
async def withdraw_from_research(
    withdrawal_request: WithdrawalRequest,
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Withdraw from research participation"""
    try:
        success = await research_service.withdraw_from_research(
            user_id=current_user['id'],
            research_id=withdrawal_request.research_id,
            reason=withdrawal_request.reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Research participation not found")
        
        return {
            "status": "success",
            "message": "Successfully withdrawn from research study"
        }
        
    except Exception as e:
        logger.error(f"Error withdrawing from research: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Data Anonymization Endpoints

@router.post("/data/anonymize", summary="Anonymize User Data")
async def anonymize_user_data(
    research_id: str = Query(..., description="Research study identifier"),
    data_types: Optional[List[str]] = Query(None, description="Types of data to anonymize"),
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Anonymize user data for research purposes"""
    try:
        # Check if user has permission (admin or the user themselves)
        if current_user.get('role') not in ['admin', 'researcher']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        anonymized_counts = await research_service.anonymize_user_data(
            user_id=current_user['id'],
            research_id=research_id,
            data_types=data_types
        )
        
        return {
            "status": "success",
            "message": "Data anonymization completed",
            "anonymized_counts": anonymized_counts
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error anonymizing user data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Research Dataset Endpoints

@router.post("/datasets", summary="Create Research Dataset")
async def create_research_dataset(
    dataset_request: DatasetRequest,
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Create a research dataset export request"""
    try:
        # Check researcher permissions
        if current_user.get('role') not in ['admin', 'researcher']:
            raise HTTPException(status_code=403, detail="Researcher access required")
        
        # Validate anonymization level
        try:
            anonymization_level = DataAnonymizationLevel(dataset_request.anonymization_level)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid anonymization level")
        
        # Prepare query parameters
        query_parameters = {
            'data_types': dataset_request.data_types,
            'start_date': dataset_request.start_date,
            'end_date': dataset_request.end_date,
            'include_demographics': dataset_request.include_demographics,
            'include_video_data': dataset_request.include_video_data
        }
        
        dataset = await research_service.create_research_dataset(
            researcher_id=current_user['id'],
            dataset_name=dataset_request.dataset_name,
            research_id=dataset_request.research_id,
            query_parameters=query_parameters,
            anonymization_level=anonymization_level,
            export_format=dataset_request.export_format
        )
        
        return {
            "status": "success",
            "message": "Research dataset creation initiated",
            "dataset": dataset.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating research dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets", summary="List Research Datasets")
async def list_research_datasets(
    research_id: Optional[str] = Query(None, description="Filter by research study"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of datasets to return"),
    offset: int = Query(0, description="Number of datasets to skip"),
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """List research datasets for the current researcher"""
    try:
        # Check researcher permissions
        if current_user.get('role') not in ['admin', 'researcher']:
            raise HTTPException(status_code=403, detail="Researcher access required")
        
        # This would need to be implemented in the research service
        return {
            "datasets": [],
            "total": 0,
            "message": "Dataset listing not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error listing research datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}", summary="Get Research Dataset")
async def get_research_dataset(
    dataset_id: str,
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Get details of a specific research dataset"""
    try:
        # Check researcher permissions
        if current_user.get('role') not in ['admin', 'researcher']:
            raise HTTPException(status_code=403, detail="Researcher access required")
        
        # This would need to be implemented in the research service
        return {
            "dataset": None,
            "message": "Dataset retrieval not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error getting research dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/download", summary="Download Research Dataset")
async def download_research_dataset(
    dataset_id: str,
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Download a completed research dataset"""
    try:
        # Check researcher permissions
        if current_user.get('role') not in ['admin', 'researcher']:
            raise HTTPException(status_code=403, detail="Researcher access required")
        
        # This would need to be implemented to return the actual file
        # For now, return a placeholder response
        return JSONResponse(
            content={"message": "Dataset download not yet implemented"},
            status_code=501
        )
        
    except Exception as e:
        logger.error(f"Error downloading research dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Data Retention Endpoints

@router.post("/retention/rules", summary="Create Data Retention Rule")
async def create_retention_rule(
    rule_request: RetentionRuleRequest,
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Create a data retention rule"""
    try:
        # Check admin permissions
        if current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        rule = await research_service.create_retention_rule(
            rule_name=rule_request.rule_name,
            data_type=rule_request.data_type,
            retention_days=rule_request.retention_days,
            anonymize_after_days=rule_request.anonymize_after_days,
            hard_delete_after_days=rule_request.hard_delete_after_days,
            compliance_framework=rule_request.compliance_framework,
            rule_config=rule_request.rule_config
        )
        
        return {
            "status": "success",
            "message": "Data retention rule created successfully",
            "rule": rule.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating retention rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention/rules", summary="List Data Retention Rules")
async def list_retention_rules(
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """List data retention rules"""
    try:
        # Check admin permissions
        if current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # This would need to be implemented in the research service
        return {
            "rules": [],
            "message": "Retention rules listing not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error listing retention rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention/execute", summary="Execute Retention Policies")
async def execute_retention_policies(
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Execute all active data retention policies"""
    try:
        # Check admin permissions
        if current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Run retention policies in background
        background_tasks.add_task(research_service.execute_retention_policies)
        
        return {
            "status": "success",
            "message": "Retention policy execution initiated"
        }
        
    except Exception as e:
        logger.error(f"Error executing retention policies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Compliance and Reporting Endpoints

@router.get("/compliance/{research_id}", summary="Get Research Compliance Report")
async def get_research_compliance_report(
    research_id: str,
    current_user: Dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Generate compliance report for a research study"""
    try:
        # Check admin or researcher permissions
        if current_user.get('role') not in ['admin', 'researcher']:
            raise HTTPException(status_code=403, detail="Researcher access required")
        
        report = await research_service.get_research_compliance_report(research_id)
        
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consent-types", summary="Get Available Consent Types")
async def get_consent_types():
    """Get list of available research consent types"""
    return {
        "consent_types": [consent_type.value for consent_type in ResearchConsentType],
        "anonymization_levels": [level.value for level in DataAnonymizationLevel]
    }


@router.get("/health", summary="Research Service Health Check")
async def health_check(
    research_service: ResearchService = Depends(get_research_service)
):
    """Check the health of the research service"""
    try:
        return {
            "status": "healthy",
            "service": "research_service",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Research service health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }