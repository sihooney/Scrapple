/**
 * HudHeader Component
 * 
 * Top-left overlay displaying the application title and subtitle.
 * Apocalyptic hacker terminal style.
 */
export default function HudHeader() {
    return (
        <header className="hud-header" id="hudHeader">
            <h1 className="hud-header__title">SCRAPPLE_</h1>
            <span className="hud-header__subtitle">
                [WASTELAND SALVAGE UNIT] // TERMINAL v6.66
            </span>
        </header>
    );
}
