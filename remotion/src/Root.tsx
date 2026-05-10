import React from "react";
import { Composition } from "remotion";
import { FactReel, factReelSchema } from "./compositions/FactReel";
import { ReelThumbnail, reelThumbnailSchema } from "./compositions/ReelThumbnail";
import { ReelStory, reelStorySchema } from "./compositions/ReelStory";

export const Root: React.FC = () => (
  <>
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
        // Prefer the spec's pre-computed total_frames (includes title hold,
        // narration duration, breath room). Fall back to a derived estimate.
        const total = props.total_frames
          ?? (props.cta_window?.end_frame ?? 0)
          ?? 1800;
        return { durationInFrames: Math.max(total, fps), fps };
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
    <Composition
      id="ReelThumbnail"
      component={ReelThumbnail}
      durationInFrames={1}
      fps={30}
      width={1080}
      height={1920}
      schema={reelThumbnailSchema}
      defaultProps={{
        title: "Untitled fact",
        topic: "GENERAL",
        frame_path: null,
        kicker: null,
        fact_number: null,
        title_size: 132,
      }}
    />
    <Composition
      id="ReelStory"
      component={ReelStory}
      durationInFrames={1}
      fps={30}
      width={1080}
      height={1920}
      schema={reelStorySchema}
      defaultProps={{
        title: "Untitled fact",
        topic: "GENERAL",
        frame_path: null,
        kicker: null,
        title_size: 132,
      }}
    />
  </>
);
