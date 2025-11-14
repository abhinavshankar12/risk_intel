"""Analyst copilot for explaining risk scores using Claude 4.5 Sonnet.

CRITICAL ETHICAL CONSTRAINTS:
- All explanations must be grounded in actual data from the database
- No hallucination of unknown facts
- No mention of religion, ethnicity, immigration status, or political opinion
- Focus on concrete behavioral patterns and incident data
"""
import os
from typing import Optional, Dict, List
from datetime import timedelta
from anthropic import Anthropic
from sqlalchemy.orm import Session
from sqlalchemy import and_
from dotenv import load_dotenv

from backend.db.models import Region, RiskScore, RegionFeature, Incident, Event

load_dotenv()


class CopilotExplainer:
    """Generates explanations for risk scores using Claude."""
    
    SYSTEM_PROMPT = """You are an analyst assistant for a public safety risk intelligence platform.

Your role is to explain why certain geographic regions have elevated risk scores in clear, concise language.

CRITICAL INSTRUCTIONS:
1. Base ALL explanations on the specific data provided to you
2. DO NOT speculate or make up information
3. DO NOT mention or infer:
   - Religion, religious beliefs, or religious groups
   - Ethnicity, race, or national origin
   - Immigration status
   - Political opinions or affiliations
4. Focus ONLY on:
   - Concrete incident counts and patterns
   - Upcoming events and their characteristics
   - Content signals (explicit violence calls only)
   - Structural risk factors
   - Spatial patterns (neighbor activity)
   - Temporal trends

5. Structure your explanation as 3-5 bullet points
6. Be specific with numbers when provided
7. Use professional, neutral language
8. Acknowledge limitations if data is sparse"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize copilot explainer.
        
        Args:
            api_key: Anthropic API key (uses env variable if not provided)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not found")
        
        self.client = Anthropic(api_key=self.api_key)
    
    def gather_context_data(
        self,
        db: Session,
        region_id: int,
        target_date
    ) -> Dict:
        """Gather all relevant data for explanation.
        
        Args:
            db: Database session
            region_id: Region to explain
            target_date: Date to explain
            
        Returns:
            Dictionary with structured context data
        """
        # Get region
        region = db.query(Region).filter(Region.region_id == region_id).first()
        if not region:
            raise ValueError(f"Region {region_id} not found")
        
        # Get risk score
        risk_score = db.query(RiskScore).filter(
            and_(
                RiskScore.region_id == region_id,
                RiskScore.date == target_date
            )
        ).first()
        
        # Get features
        features = db.query(RegionFeature).filter(
            and_(
                RegionFeature.region_id == region_id,
                RegionFeature.date == target_date
            )
        ).first()
        
        # Get recent incidents (last 30 days)
        recent_incidents = db.query(Incident).filter(
            and_(
                Incident.region_id == region_id,
                Incident.occurred_at >= target_date - timedelta(days=30),
                Incident.occurred_at < target_date
            )
        ).order_by(Incident.occurred_at.desc()).limit(10).all()
        
        # Get upcoming events
        upcoming_events = db.query(Event).filter(
            and_(
                Event.region_id == region_id,
                Event.start_time >= target_date,
                Event.start_time < target_date + timedelta(days=7)
            )
        ).all()
        
        # Structure the context
        context = {
            "region_name": region.name,
            "date": target_date.isoformat(),
            "risk_tier": risk_score.risk_tier if risk_score else "unknown",
            "r_smoothed": risk_score.r_smoothed if risk_score else 0.0,
            "p_raw": risk_score.p_raw if risk_score else 0.0,
            "baseline_risk": region.baseline_risk,
        }
        
        if features:
            context["features"] = {
                "recent_incidents_7d": features.recent_incidents_7d,
                "recent_incidents_30d": features.recent_incidents_30d,
                "neighbor_incidents_7d": features.neighbor_incidents_7d,
                "neighbor_incidents_30d": features.neighbor_incidents_30d,
                "event_count_7d": features.event_count_7d,
                "event_attendance_7d": features.event_attendance_7d,
                "content_violent_count": features.content_violent_count,
            }
        
        if recent_incidents:
            context["recent_incidents"] = [
                {
                    "date": inc.occurred_at.date().isoformat(),
                    "type": inc.type,
                    "severity": inc.severity,
                }
                for inc in recent_incidents
            ]
        
        if upcoming_events:
            context["upcoming_events"] = [
                {
                    "start_time": evt.start_time.date().isoformat(),
                    "type": evt.type,
                    "expected_attendance": evt.expected_attendance,
                }
                for evt in upcoming_events
            ]
        
        return context
    
    def explain(self, context: Dict) -> str:
        """Generate explanation from context data.
        
        Args:
            context: Structured context data
            
        Returns:
            Explanation text
        """
        # Format context as clear prompt
        prompt = f"""Explain why {context['region_name']} has a {context['risk_tier']} risk tier on {context['date']}.

RISK SCORES:
- Smoothed risk score (R): {context['r_smoothed']:.3f}
- Raw model prediction (p): {context['p_raw']:.3f}
- Baseline structural risk: {context['baseline_risk']:.3f}

FEATURES:"""
        
        if "features" in context:
            f = context["features"]
            prompt += f"""
- Recent incidents (7 days): {f['recent_incidents_7d']}
- Recent incidents (30 days): {f['recent_incidents_30d']}
- Neighbor incidents (7 days): {f['neighbor_incidents_7d']}
- Neighbor incidents (30 days): {f['neighbor_incidents_30d']}
- Upcoming events (7 days): {f['event_count_7d']}
- Expected event attendance: {f['event_attendance_7d']}
- Explicit violence calls detected: {f['content_violent_count']}"""
        
        if "recent_incidents" in context:
            prompt += "\n\nRECENT INCIDENTS:"
            for inc in context["recent_incidents"][:5]:
                prompt += f"\n- {inc['date']}: {inc['type']} (severity: {inc['severity']:.2f})"
        
        if "upcoming_events" in context:
            prompt += "\n\nUPCOMING EVENTS:"
            for evt in context["upcoming_events"]:
                prompt += f"\n- {evt['start_time']}: {evt['type']}"
                if evt['expected_attendance']:
                    prompt += f" (expected attendance: {evt['expected_attendance']})"
        
        prompt += "\n\nProvide a concise explanation in 3-5 bullet points. Remember: base explanation ONLY on the data above, and do not mention religion, ethnicity, immigration, or political views."
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            explanation = response.content[0].text
            return explanation
            
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return f"Unable to generate explanation: {str(e)}"
    
    def explain_hotspot(
        self,
        db: Session,
        region_id: int,
        target_date
    ) -> str:
        """Main entry point for hotspot explanation.
        
        Args:
            db: Database session
            region_id: Region to explain
            target_date: Date to explain
            
        Returns:
            Explanation text
        """
        context = self.gather_context_data(db, region_id, target_date)
        return self.explain(context)


def explain_hotspot(
    db: Session,
    region_id: int,
    target_date,
    api_key: Optional[str] = None
) -> str:
    """Convenience function to explain a hotspot.
    
    Args:
        db: Database session
        region_id: Region to explain
        target_date: Date to explain
        api_key: Anthropic API key (optional)
        
    Returns:
        Explanation text
    """
    explainer = CopilotExplainer(api_key=api_key)
    return explainer.explain_hotspot(db, region_id, target_date)

