import React from "react";
import { Composition } from "remotion";
import { FactReel, factReelSchema } from "./compositions/FactReel";

export const Root: React.FC = () => (
  <Composition
    id="FactReel"
    component={FactReel}
    durationInFrames={1800}
    fps={30}
    width={1080}
    height={1920}
    schema={factReelSchema}
    calculateMetadata={({ props }) => {
      const fps = 30;
      const HOOK = Math.floor(fps * 1.5);
      const CTA = Math.floor(fps * 1.8);
      const lastEnd = props.beats.length ? props.beats[props.beats.length - 1].end_frame : HOOK;
      return { durationInFrames: HOOK + lastEnd + CTA, fps };
    }}
    defaultProps={{
      composition: "FactReel",
      title: "Untitled",
      hook: "",
      cta: "",
      narration_audio: null,
      alignment: [],
      beats: [],
    }}
  />
);
