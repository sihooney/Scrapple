export default function HudHeader() {
    return (
        <header
            className="bg-gray-950 border-b-4 border-cyan-500 px-6 py-4 glow-cyan"
            id="hudHeader"
        >
            <h1 className="text-4xl font-bold text-cyan-400 tracking-widest uppercase">
                SCRAPPLE
            </h1>
            <span className="text-sm text-cyan-300/80 tracking-wide uppercase inline-block mt-2">
                ROBOTIC PICKUP ARM — DASHBOARD v2.4
            </span>
        </header>
    );
}
