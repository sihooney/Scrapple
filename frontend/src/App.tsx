import GridCanvas from './components/GridCanvas';
import CameraFeed from './components/CameraFeed';
import HudHeader from './components/HudHeader';
import HudFooter from './components/HudFooter';

export default function App() {
  return (
    <>
      <GridCanvas />
      <CameraFeed />
      <HudHeader />
      <HudFooter />
    </>
  );
}
