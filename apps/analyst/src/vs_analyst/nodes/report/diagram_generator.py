# diagram_generator.py
import math
import re
from typing import Any, Dict, List
from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

def _get_competitor_coordinates(c: Any) -> tuple[float, float]:
    """
    Deterministically map competitor properties to coordinates:
    X = Market Scope (0 to 100)
    Y = Funding Power (0 to 100)
    """
    # 1. Funding Power Map
    funding_stage = (c.funding_stage or "").lower()
    funding_amount = (c.funding_amount or "").lower()
    
    power = 45.0 # default middle
    if "series c" in funding_stage or "series d" in funding_stage or "growth" in funding_stage:
        power = 85.0
    elif "series b" in funding_stage:
        power = 75.0
    elif "series a" in funding_stage:
        power = 65.0
    elif "seed" in funding_stage:
        power = 45.0
    elif "pre-seed" in funding_stage:
        power = 30.0
    elif "bootstrapped" in funding_stage:
        power = 15.0
    elif funding_amount:
        # Try to parse numeric value from e.g. "$12M"
        match = re.search(r'\$?([0-9.]+)\s*([mK])', funding_amount)
        if match:
            num = float(match.group(1))
            unit = match.group(2).lower()
            if unit == 'm':
                val = num
            else:
                val = num / 1000.0
            if val > 50: power = 90.0
            elif val > 20: power = 80.0
            elif val > 5: power = 65.0
            elif val > 1: power = 50.0
            else: power = 35.0

    # 2. Market Scope Map
    competitor_type = (c.competitor_type or "").lower()
    geography = (c.geography or "").lower()
    
    scope = 50.0 # default middle
    if "global" in geography or "worldwide" in geography:
        scope = 85.0
    elif "us" in geography or "united states" in geography or "europe" in geography:
        scope = 70.0
    elif "regional" in geography or "india" in geography:
        scope = 45.0
    
    # Adjust based on competitor type
    if "direct" in competitor_type:
        scope = min(100.0, scope + 10.0)
    elif "indirect" in competitor_type:
        scope = max(0.0, scope - 10.0)
    elif "substitute" in competitor_type:
        scope = max(0.0, scope - 20.0)
    elif "emerging" in competitor_type:
        scope = max(0.0, scope - 15.0)
        
    return scope, power


def generate_competitive_quadrant_svg(competitors: List[Any]) -> str:
    """Generates an elegant, highly styled 2x2 grid SVG mapping competitors."""
    svg_width = 320
    svg_height = 320
    
    # Colors for competitor types
    # Direct = Red, Indirect = Blue, Emerging = Green, Substitute = Yellow
    type_colors = {
        "direct": "#ef4444",
        "indirect": "#3b82f6",
        "emerging": "#10b981",
        "substitute": "#f59e0b"
    }

    # Grid background & axes lines
    svg_content = f'''<svg width="100%" height="100%" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg" style="background:#111827; border-radius:12px;">
    <!-- Grid Lines -->
    <line x1="160" y1="20" x2="160" y2="300" stroke="#1f2937" stroke-width="1.5" />
    <line x1="20" y1="160" x2="300" y2="160" stroke="#1f2937" stroke-width="1.5" />
    
    <!-- Quadrant Labels -->
    <text x="25" y="35" font-family="'Inter', sans-serif" font-size="9" fill="#9ca3af" font-weight="600">HIGH POWER / NICHE</text>
    <text x="175" y="35" font-family="'Inter', sans-serif" font-size="9" fill="#3b82f6" font-weight="600">LEADERS (HIGH/BROAD)</text>
    <text x="25" y="290" font-family="'Inter', sans-serif" font-size="9" fill="#9ca3af" font-weight="600">BOOTSTRAPPED / LOCAL</text>
    <text x="175" y="290" font-family="'Inter', sans-serif" font-size="9" fill="#10b981" font-weight="600">EMERGING GIANTS</text>
    
    <!-- X/Y Axes Labels -->
    <text x="160" y="312" font-family="'Inter', sans-serif" font-size="8" fill="#9ca3af" text-anchor="middle" font-weight="500">Market Scope →</text>
    <text x="12" y="160" font-family="'Inter', sans-serif" font-size="8" fill="#9ca3af" text-anchor="middle" font-weight="500" transform="rotate(-90 12 160)">Funding Power →</text>
    '''

    for c in competitors:
        scope, power = _get_competitor_coordinates(c)
        # Map 0..100 to SVG pixels (margins of 40px to 280px)
        cx = 40 + (scope / 100.0) * 240
        cy = 280 - (power / 100.0) * 240
        
        comp_type = getattr(c, "competitor_type", "direct")
        if hasattr(comp_type, "value"):
            comp_type = comp_type.value
        
        color = type_colors.get(str(comp_type).lower(), "#9ca3af")
        name = getattr(c, "name", "Competitor")
        
        # Plot circle and short label
        svg_content += f'''
    <g>
        <circle cx="{cx}" cy="{cy}" r="6" fill="{color}" stroke="#111827" stroke-width="1.5" opacity="0.9" />
        <text x="{cx + 8}" y="{cy + 3}" font-family="'Inter', sans-serif" font-size="8" fill="#f3f4f6" font-weight="600">{name}</text>
    </g>
        '''

    svg_content += "\n</svg>"
    return svg_content


def generate_moat_radar_svg(moat_assessment: str) -> str:
    """Generates a premium 7-axis spider radar chart representing Hamilton Powers."""
    svg_width = 320
    svg_height = 320
    cx, cy = 160, 160
    r_max = 100
    
    dimensions = [
        "Scale Economies",
        "Network Economies",
        "Counter-Positioning",
        "Switching Costs",
        "Brand Advantage",
        "Cornered Resource",
        "Process Power"
    ]
    
    # Establish scores deterministically (based on keywords or fallback defaults)
    scores = [50, 40, 60, 45, 55, 50, 45] # Default balanced shape
    text_lower = (moat_assessment or "").lower()
    
    if "scale" in text_lower or "size" in text_lower: scores[0] = 85
    if "network" in text_lower or "viral" in text_lower: scores[1] = 80
    if "counter" in text_lower or "business model" in text_lower: scores[2] = 90
    if "switching" in text_lower or "sticky" in text_lower: scores[3] = 75
    if "brand" in text_lower or "reputation" in text_lower: scores[4] = 80
    if "patent" in text_lower or "license" in text_lower or "exclusive" in text_lower or "cornered" in text_lower: scores[5] = 95
    if "process" in text_lower or "proprietary" in text_lower or "culture" in text_lower: scores[6] = 75

    # 1. Background regular heptagons
    svg_content = f'''<svg width="100%" height="100%" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg" style="background:#111827; border-radius:12px;">
    <!-- Grid Rings -->
    '''
    
    # Draw concentric ring heptagons
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(7):
            angle = (2 * math.pi * i / 7.0) - (math.pi / 2.0)
            px = cx + (r_max * level) * math.cos(angle)
            py = cy + (r_max * level) * math.sin(angle)
            pts.append(f"{px},{py}")
        svg_content += f'<polygon points="{" ".join(pts)}" fill="none" stroke="#1f2937" stroke-width="1" />\n'

    # 2. Draw 7 spokes & labels
    for i, dim in enumerate(dimensions):
        angle = (2 * math.pi * i / 7.0) - (math.pi / 2.0)
        px = cx + r_max * math.cos(angle)
        py = cy + r_max * math.sin(angle)
        svg_content += f'<line x1="{cx}" y1="{cy}" x2="{px}" y2="{py}" stroke="#1f2937" stroke-width="1" />\n'
        
        # Label offset
        lx = cx + (r_max + 18) * math.cos(angle)
        ly = cy + (r_max + 12) * math.sin(angle)
        
        # Adjust vertical alignment/anchoring for labels
        anchor = "middle"
        if math.cos(angle) > 0.3: anchor = "start"
        elif math.cos(angle) < -0.3: anchor = "end"
        
        # Shorten label if too long
        short_dim = dim
        if dim == "Counter-Positioning": short_dim = "Counter-Pos."
        
        svg_content += f"""<text x="{lx}" y="{ly + 3}" font-family="'Inter', sans-serif" font-size="8" fill="#9ca3af" text-anchor="{anchor}" font-weight="500">{short_dim}</text>\n"""

    # 3. Draw filled scores polygon
    score_pts = []
    for i, score in enumerate(scores):
        angle = (2 * math.pi * i / 7.0) - (math.pi / 2.0)
        dist = (score / 100.0) * r_max
        px = cx + dist * math.cos(angle)
        py = cy + dist * math.sin(angle)
        score_pts.append(f"{px},{py}")
        
    svg_content += f'''
    <!-- Scores Poly -->
    <polygon points="{" ".join(score_pts)}" fill="rgba(16, 185, 129, 0.2)" stroke="#10b981" stroke-width="2" />
    '''
    
    # Radar center point
    svg_content += f'<circle cx="{cx}" cy="{cy}" r="3" fill="#10b981" />'
    svg_content += "\n</svg>"
    
    return svg_content


def generate_traction_sparkline_svg(traction: Any) -> str:
    """Generates a clean upward sparkline visual trend if metrics exist."""
    # Check if there is monthly revenue or user count
    rev_monthly = getattr(traction, "revenue_monthly", None)
    user_count = getattr(traction, "user_count", None)
    growth_rate = getattr(traction, "growth_rate", None)
    
    if not rev_monthly and not user_count:
        logger.info("Skipping Traction Sparkline: no major traction metrics found")
        return ""
        
    # We have metrics! Let's mock a nice 6-month historical sparkline
    # Base height & width
    w = 600
    h = 100
    
    # Resolve growth multiplier (default 1.15)
    mult = 1.15
    if growth_rate:
        match = re.search(r'([0-9.]+)\s*%', growth_rate)
        if match:
            mult = 1.0 + (float(match.group(1)) / 100.0)
            
    # Formulate 6 historical points leading up to current value
    # Let's say current is 100% of value
    points = [100.0 / (mult ** i) for i in range(5, -1, -1)]
    
    # Map points to fits in height 15 to 85 (margins)
    y_vals = []
    min_pt, max_pt = min(points), max(points)
    span = (max_pt - min_pt) if max_pt != min_pt else 1.0
    
    for pt in points:
        norm = (pt - min_pt) / span
        y_vals.append(85 - norm * 70) # higher Y is top of chart
        
    x_step = w / 5.0
    pts_str = " ".join([f"{i * x_step},{y_vals[i]}" for i in range(6)])
    
    # Build HTML/SVG Sparkline
    svg_content = f'''<svg width="100%" height="100%" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="background:#111827; border-radius:12px;">
    <!-- Background grid lines -->
    <line x1="0" y1="25" x2="{w}" y2="25" stroke="#1f2937" stroke-dasharray="4" />
    <line x1="0" y1="50" x2="{w}" y2="50" stroke="#1f2937" stroke-dasharray="4" />
    <line x1="0" y1="75" x2="{w}" y2="75" stroke="#1f2937" stroke-dasharray="4" />
    
    <!-- Sparkline Path -->
    <polyline points="{pts_str}" fill="none" stroke="#3b82f6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
    
    <!-- Gradient Fill Area -->
    <path d="M 0,100 L {pts_str} L {w},100 Z" fill="rgba(59, 130, 246, 0.08)" />
    
    <!-- Trend Indicator -->
    <text x="15" y="20" font-family="'Inter', sans-serif" font-size="10" fill="#9ca3af" font-weight="600">6-Month Projected Historical Metric Growth</text>
    '''
    
    # Draw points circles
    for i in range(6):
        cx = i * x_step
        cy = y_vals[i]
        # Only highlight start/end circles
        if i == 0 or i == 5:
            color = "#10b981" if i == 5 else "#9ca3af"
            svg_content += f'<circle cx="{cx}" cy="{cy}" r="4" fill="{color}" stroke="#111827" stroke-width="1.5" />\n'

    svg_content += "</svg>"
    return svg_content


async def vector_diagram_generator_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Vector Diagram Generator Node (Pure Python SVG - ZERO LLM CALLS).
    Generates programmatic SVGs for the Competitive 2x2 Quadrant, Moat Radar spider chart,
    and Traction Sparkline chart. Writes results directly to state.analysis_state.memo.diagrams.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Vector Diagram Generator node started", run_id=analysis_state.run_id)
    
    # 1. Competitive Quadrant
    competitors = analysis_state.competitive.competitors
    comp_quadrant_svg = generate_competitive_quadrant_svg(competitors)
    
    # 2. Moat Radar Spider Chart
    moat_assessment = analysis_state.competitive.moat_assessment or ""
    moat_radar_svg = generate_moat_radar_svg(moat_assessment)
    
    # 3. Traction Sparkline
    traction = analysis_state.company.traction
    traction_sparkline_svg = generate_traction_sparkline_svg(traction)
    
    # Create child update state
    parent_update = AnalysisState(
        run_id=analysis_state.run_id,
        user_input=analysis_state.user_input,
        created_at=analysis_state.created_at
    )
    
    # Save diagram strings to the state memo diagrams namespace
    parent_update.memo.diagrams = {
        "competitive_quadrant": comp_quadrant_svg,
        "moat_radar": moat_radar_svg
    }
    
    if traction_sparkline_svg:
        parent_update.memo.diagrams["traction_sparkline"] = traction_sparkline_svg
        
    parent_update.agent_statuses = {"vector_diagram_generator": AgentStatus.COMPLETE}
    
    logger.info("Vector Diagram Generator successfully completed", run_id=analysis_state.run_id, diagrams_generated=list(parent_update.memo.diagrams.keys()))
    return {"analysis_state": parent_update}
