import React from "react";
import { Composition } from "remotion";
import { BrandedIntro } from "./Composition";

// 20 seconds at 30fps = 600 frames
const DURATION_IN_FRAMES = 600;
const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="BrandedIntro"
        component={BrandedIntro}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
    </>
  );
};
