import GridCanvas from './components/GridCanvas';
import CameraFeed from './components/CameraFeed';
import HudHeader from './components/HudHeader';
import HudFooter from './components/HudFooter';
import CliPanel from './components/CliPanel';

export default function App() {
  return (
    <>
      <GridCanvas />
      <HudHeader />

      {/* Video + CLI column — centered, stacked vertically */}
      <div className="main-column">
        <CameraFeed />
        <CliPanel />
      </div>

      <HudFooter />
    </>
  );
}
