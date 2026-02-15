/**
 * HudHeader Component
 * 
 * Top-left overlay displaying the application title and subtitle.
 * Part of the HUD overlay system (z-index: 2).
 * 
 * Features:
 * - Fixed positioning at top-left
 * - Orbitron font for title
 * - Cyan glow effects
 */
export default function HudHeader() {
    return (
        <header className="hud-header" id="hudHeader">
            <h1 className="hud-header__title">SCRAPPLE</h1>
            <span className="hud-header__subtitle">
                ROBOTIC PICKUP ARM — DASHBOARD v2.4
            </span>
        </header>
    );
}
